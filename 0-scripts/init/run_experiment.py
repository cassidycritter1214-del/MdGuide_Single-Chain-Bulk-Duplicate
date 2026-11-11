
#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd, cwd=None):
    """Run a command and report whether it succeeded."""
    print(f"\nRunning: {' '.join(map(str, cmd))}")

    result = subprocess.run(cmd, cwd=cwd)

    if result.returncode != 0:
        print(f"ERROR: Command failed with exit code {result.returncode}")
        return False

    return True


def find_lammps(project_dir):
    """Find the LAMMPS executable."""
    local_lmp = project_dir / "0-software" / "lmp"

    if local_lmp.exists():
        return str(local_lmp)

    system_lmp = shutil.which("lmp")

    if system_lmp:
        return system_lmp

    raise FileNotFoundError(
        "Could not find LAMMPS. Make sure the polymer conda environment is active."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Run polymer bulk equilibration or adsorption."
    )

    parser.add_argument(
        "--stage",
        choices=["bulk", "adsorption"],
        required=True,
        help="Which simulation stage to run."
    )

    parser.add_argument(
        "--chain-lengths",
        type=int,
        nargs="+",
        default=[10, 20, 50, 100, 200]
    )

    parser.add_argument(
        "--repetitions",
        type=int,
        default=1
    )

    parser.add_argument("--lx", type=float, default=20.0)
    parser.add_argument("--ly", type=float, default=20.0)
    parser.add_argument("--lz", type=float, default=40.0)

    # so i can control timesteps from init_run.sh
    parser.add_argument("--bulk-steps", type=int, default=20000000)
    parser.add_argument("--adsorption-steps", type=int, default=20000000)
    args = parser.parse_args()

    # Locate project directories
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent.parent
    runs_dir = project_dir / "1-surface-runs"

    runs_dir.mkdir(parents=True, exist_ok=True)

    # Locate simulation programs and input files
    lmp_exec = find_lammps(project_dir)

    init_script = script_dir / "init_polymer.py"
    bulk_script = script_dir / "equilibrate.in"
    adsorption_script = script_dir / "polymer.in"

    base_velocity_seed = 12345

    failures = 0
    jobs = []

    for n in args.chain_lengths:
        n_dir = runs_dir / f"N{n}"
        n_dir.mkdir(parents=True, exist_ok=True)

        # Bulk creates new repetitions after the highest existing rep###.
        # Adsorption uses the matching existing bulk repetition numbers.
        if args.stage == "bulk":
            existing_reps = [
                int(path.name[3:])
                for path in n_dir.glob("rep[0-9][0-9][0-9]")
                if path.is_dir()
            ]
            first_rep = max(existing_reps, default=0) + 1
        else:
            first_rep = 1

        for rep in range(first_rep, first_rep + args.repetitions):
            rep_name = f"rep{rep:03d}"
            rep_dir = n_dir / rep_name
            bulk_dir = rep_dir / "bulk"
            ads_dir = rep_dir / "adsorption"
            vel_seed = base_velocity_seed + n * 1000 + rep * 17

            print(
                f"Preparing {args.stage}: N={n}, {rep_name}",
                flush=True,
            )

            if args.stage == "bulk":
                if (bulk_dir / "final.data").exists():
                    print(f"Skipping N={n}, {rep_name}: bulk/final.data already exists.")
                    continue

                bulk_dir.mkdir(parents=True, exist_ok=True)
                ads_dir.mkdir(parents=True, exist_ok=True)
                data_file = bulk_dir / "data.data"

                if not data_file.exists():
                    gen_cmd = [
                        sys.executable, str(init_script),
                        "--monomers-per-chain", str(n),
                        "--lx", str(args.lx), "--ly", str(args.ly),
                        "--lz", str(args.lz), "--output", str(data_file),
                        "--seed", str(vel_seed),
                    ]
                    if not run_cmd(gen_cmd):
                        failures += 1
                        continue
                else:
                    print(f"Using existing {data_file}.")

                shutil.copy(bulk_script, bulk_dir / "equilibrate.in")
                cmd = [
                    lmp_exec,
                    "-var", "velseed", str(vel_seed),
                    "-var", "nsteps", str(args.bulk_steps),
                    "-in", "equilibrate.in",
                ]
                jobs.append((n, rep_name, bulk_dir, cmd, bulk_dir / "final.data"))

            else:
                final_data = bulk_dir / "final.data"
                if not final_data.exists():
                    print(
                        f"Skipping N={n}, {rep_name}: bulk/final.data does not exist. "
                        "Run bulk equilibration first."
                    )
                    failures += 1
                    continue

                ads_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy(adsorption_script, ads_dir / "polymer.in")
                cmd = [
                    lmp_exec,
                    "-var", "nsteps", str(args.adsorption_steps),
                    "-in", "polymer.in",
                ]
                jobs.append((n, rep_name, ads_dir, cmd, None))

    # Launch every prepared simulation before waiting, with one process and
    # one OpenMP thread per run.
    run_env = os.environ.copy()
    run_env["OMP_NUM_THREADS"] = "1"
    running_jobs = []
    for n, rep_name, cwd, cmd, expected_output in jobs:
        print(f"Launching N={n}, {rep_name}: {' '.join(cmd)}", flush=True)
        try:
            process = subprocess.Popen(cmd, cwd=cwd, env=run_env)
            running_jobs.append((n, rep_name, process, expected_output))
        except OSError as exc:
            print(f"Failed to launch N={n}, {rep_name}: {exc}", file=sys.stderr)
            failures += 1

    for n, rep_name, process, expected_output in running_jobs:
        return_code = process.wait()
        if return_code != 0:
            print(f"Run failed: N={n}, {rep_name} (exit code {return_code}).")
            failures += 1
        elif expected_output and not expected_output.exists():
            print(f"Run ended without creating {expected_output}.")
            failures += 1
        else:
            print(f"Run completed: N={n}, {rep_name}.")

    print("\n==========================================")
    print(f"Finished {args.stage} stage.")

    if failures:
        print(f"Number of failed or skipped runs: {failures}")
        sys.exit(1)

    print("All requested runs completed successfully.")
    print("==========================================")


if __name__ == "__main__":
    main()
