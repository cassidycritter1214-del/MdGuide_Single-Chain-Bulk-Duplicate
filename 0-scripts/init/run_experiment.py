#!/usr/bin/env python3
import os
import subprocess
import sys
import shutil
import argparse
from pathlib import Path

def run_cmd(cmd, cwd=None):
    """Run a shell command and check for errors."""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str))
    if result.returncode != 0:
        print(f"Error: Command failed with exit code {result.returncode}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Run polymer bulk equilibration and adsorption experiment pipeline.")
    parser.add_argument("--chain-lengths", type=int, nargs="+", default=[10, 20, 50], help="List of chain lengths (N)")
    parser.add_argument("--repetitions", type=int, default=3, help="Number of repetitions per chain length")
    parser.add_argument("--lx", type=float, default=20.0, help="Box length X")
    parser.add_argument("--ly", type=float, default=20.0, help="Box length Y")
    parser.add_argument("--lz", type=float, default=40.0, help="Box length Z")
    args = parser.parse_args()

    # Define project paths
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent.parent
    runs_dir = project_dir / "1-surface-runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    # Check local folder first, then check active conda environment / system path
    lmp_exec = project_dir / "0-software" / "lmp"
    if not lmp_exec.exists():
        system_lmp = shutil.which("lmp")
        if system_lmp:
            lmp_exec = Path(system_lmp)
        else:
            # Fallback string if neither exists
            lmp_exec = "lmp"

    init_polymer_script = script_dir / "init_polymer.py"
    equilibrate_script = script_dir / "equilibrate.in"
    polymer_script = script_dir / "polymer.in"

    base_velocity_seed = 12345

    for n in args.chain_lengths:
        n_dir = runs_dir / f"N{n}"
        n_dir.mkdir(exist_ok=True)

        for rep in range(1, args.repetitions + 1):
            rep_name = f"rep{rep:03d}"
            rep_dir = n_dir / rep_name
            
            bulk_dir = rep_dir / "bulk"
            ads_dir = rep_dir / "adsorption"

            if rep_dir.exists():
                print(f"Skipping existing trial directory: {rep_dir} (Refusing to overwrite)")
                continue

            print(f"\n==========================================")
            print(f"Starting N={n}, Repetition {rep_name}")
            print(f"==========================================")

            bulk_dir.mkdir(parents=True, exist_ok=True)
            ads_dir.mkdir(parents=True, exist_ok=True)

            # Unique velocity seed for each trial
            vel_seed = base_velocity_seed + n * 1000 + rep * 17

            # 1. Generate initial polymer chain in bulk/data.data
            data_file = bulk_dir / "data.data"
            gen_cmd = [
                sys.executable, str(init_polymer_script),
                "--monomers-per-chain", str(n),
                "--lx", str(args.lx),
                "--ly", str(args.ly),
                "--lz", str(args.lz),
                "--output", str(data_file),
                "--seed", str(vel_seed)
            ]
            if not run_cmd(gen_cmd):
                print(f"Failed generating polymer for N={n}, {rep_name}")
                continue

            # Copy input scripts into trial subdirectories for self-contained execution
            shutil.copy(equilibrate_script, bulk_dir / "equilibrate.in")
            shutil.copy(polymer_script, ads_dir / "polymer.in")

            # Modify or pass velocity seed to equilibrate.in if needed, 
            # or rely on LAMMPS variable indexing. Here we can pass `-var velseed <seed>` via command line.
            # 2. Run Bulk Equilibration
            print(f"Running bulk equilibration for N={n}, {rep_name}...")
            eq_cmd = [
                str(lmp_exec),
                "-var", "velseed", str(vel_seed),
                "-in", "equilibrate.in"
            ]
            if not run_cmd(eq_cmd, cwd=bulk_dir):
                print(f"Bulk equilibration crashed for N={n}, {rep_name}")
                continue

            # Check if final.data exists
            if not (bulk_dir / "final.data").exists():
                print(f"Error: Bulk final.data not found for N={n}, {rep_name}. Equilibration may have failed.")
                continue

            # 3. Run Adsorption Simulation
            print(f"Running adsorption simulation for N={n}, {rep_name}...")
            ads_cmd = [
                str(lmp_exec),
                "-in", "polymer.in"
            ]
            if not run_cmd(ads_cmd, cwd=ads_dir):
                print(f"Adsorption simulation crashed or exited early for N={n}, {rep_name}")
                continue

            print(f"Successfully completed N={n}, {rep_name}!")

    print("\nAll scheduled experiment runs completed.")

if __name__ == "__main__":
    main()