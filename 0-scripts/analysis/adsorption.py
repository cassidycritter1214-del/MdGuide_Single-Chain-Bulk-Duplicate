import math
import sys
from pathlib import Path

dt = 0.005



def calculate_event_times(events_file, N):
    """
    Calculate event times and censoring information
    from an events.out file.
    """

    adsorption_threshold = math.ceil(0.8 * N)

    first_contact_step = None
    adsorption_step = None
    last_step = None

    with open(events_file, "r") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            values = line.split()

            try:
                step = int(float(values[0]))
                contact_count = int(float(values[1]))
            except (ValueError, IndexError):
                continue

            last_step = step

            if first_contact_step is None and contact_count >= 1:
                first_contact_step = step

            if adsorption_step is None and contact_count >= adsorption_threshold:
                adsorption_step = step

    if last_step is None:
        raise ValueError("No valid event data found in events.out")

    # Total observed adsorption time.
    observation_duration = last_step * dt

    # Convert event steps into LJ time.
    t_hit = first_contact_step * dt if first_contact_step is not None else None
    t_ads = adsorption_step * dt if adsorption_step is not None else None

    tau_after = (
        t_ads - t_hit
        if t_hit is not None and t_ads is not None
        else None
    )

    # Event observation flags.
    hit_observed = t_hit is not None
    adsorption_observed = t_ads is not None
    tau_observed = tau_after is not None

    # Available observation duration for each quantity.
    hit_observation_duration = observation_duration

    adsorption_observation_duration = observation_duration

    if hit_observed:
        tau_observation_duration = observation_duration - t_hit
    else:
        # The chain never made contact, so after-contact time
        # was never observable.
        tau_observation_duration = None

    return {
        "N": N,
        "t_hit": t_hit,
        "t_ads": t_ads,
        "tau_after": tau_after,
        "hit_observed": hit_observed,
        "adsorption_observed": adsorption_observed,
        "tau_observed": tau_observed,
        "hit_observation_duration": hit_observation_duration,
        "adsorption_observation_duration": adsorption_observation_duration,
        "tau_observation_duration": tau_observation_duration,
        "observation_duration": observation_duration,
    }



if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python adsorption.py EVENTS_FILE CHAIN_LENGTH")
        sys.exit(1)

    events_file = Path(sys.argv[1])
    N = int(sys.argv[2])

    results = calculate_event_times(events_file, N)

    print(f"Chain length: N = {results['N']}")
    print(f"80% contact threshold: {math.ceil(0.8 * N)} beads")
    print(f"Observation duration: {results['observation_duration']} LJ time units")

    print("\n--- Event results ---")

    print(f"First contact: {results['t_hit']}")
    print(f"First contact observed: {results['hit_observed']}")

    print(f"Total adsorption: {results['t_ads']}")
    print(f"Adsorption observed: {results['adsorption_observed']}")

    print(f"After-contact time: {results['tau_after']}")
    print(f"After-contact time observed: {results['tau_observed']}")

    print("\n--- Observation durations ---")
    print(f"First-contact observation: {results['hit_observation_duration']}")
    print(f"Adsorption observation: {results['adsorption_observation_duration']}")
    print(f"After-contact observation: {results['tau_observation_duration']}")
