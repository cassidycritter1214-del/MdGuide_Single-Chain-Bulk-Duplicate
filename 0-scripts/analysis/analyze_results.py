
import csv
import sys
from pathlib import Path

# Import the event-analysis function from adsorption.py
from adsorption import calculate_event_times


def collect_results(project_root):
    """
    Find every adsorption events.out file and collect its event results.
    """

    results = []

    event_files = sorted(
        project_root.glob("1-surface-runs/N*/rep*/adsorption/events.out")
    )

    for events_file in event_files:
        # Extract chain length and repetition from the folder names
        chain_length = int(events_file.parts[-4][1:])
        repetition = events_file.parts[-3]

        print(f"Analyzing N={chain_length}, {repetition}")

        trial_results = calculate_event_times(events_file, chain_length)

        trial_results["repetition"] = repetition
        trial_results["events_file"] = str(events_file)

        results.append(trial_results)

    return results


def save_results(results, output_file):
    """
    Save all trial results to a CSV file.
    """

    if not results:
        print("No adsorption event files were found.")
        return

    with open(output_file, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\nSaved results to: {output_file}")


def save_summary(results, output_file):
    """
    Save descriptive summary statistics grouped by chain length.
    Censored event times are not treated as measured values.
    """

    summary = []

    chain_lengths = sorted(set(row["N"] for row in results))

    event_columns = {
        "t_hit": "hit_observed",
        "t_ads": "adsorption_observed",
        "tau_after": "tau_observed",
    }

    for N in chain_lengths:
        trials = [row for row in results if row["N"] == N]

        row = {
            "N": N,
            "number_of_trials": len(trials),
        }

        for event_name, observed_flag in event_columns.items():
            observed_times = [
                trial[event_name]
                for trial in trials
                if trial[observed_flag]
            ]

            row[f"{event_name}_observed"] = len(observed_times)
            row[f"{event_name}_censored"] = len(trials) - len(observed_times)

            if observed_times:
                row[f"{event_name}_mean"] = (
                    sum(observed_times) / len(observed_times)
                )
            else:
                row[f"{event_name}_mean"] = None

        summary.append(row)

    if not summary:
        print("No summary statistics to save.")
        return

    with open(output_file, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=summary[0].keys())
        writer.writeheader()
        writer.writerows(summary)

    print(f"Saved summary statistics to: {output_file}")


if __name__ == "__main__":
    # This script is located in 0-scripts/analysis/
    # The project root is two folders above it.
    project_root = Path(__file__).resolve().parents[2]

    output_folder = Path(__file__).resolve().parent / "results"
    output_folder.mkdir(exist_ok=True)

    results = collect_results(project_root)

    save_results(results, output_folder / "event_times.csv")
    save_summary(results, output_folder / "summary_statistics.csv")