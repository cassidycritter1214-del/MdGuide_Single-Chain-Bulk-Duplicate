
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Project directory
project_root = Path(__file__).resolve().parents[2]

# Simulation information
N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
dt = 0.005

surface_files = sorted(
    (project_root / "1-surface-runs" / f"N{N}").glob(
        "rep*/adsorption/surface.out"
    )
)

if not surface_files:
    raise FileNotFoundError(f"No adsorption surface.out files found for N={N}.")

# Plot
plt.figure(figsize=(11, 6))
for surface_file in surface_files:
    # These files can contain millions of rows. Load only the plotted
    # columns and downsample for a readable, fast-rendering overview.
    data = np.loadtxt(surface_file, comments="#", usecols=(0, 1))
    if data.ndim == 1:
        data = data.reshape(1, -1)
    stride = max(1, len(data) // 20000)
    data = data[::stride]
    time = data[:, 0] * dt
    contact_fraction = data[:, 1] / N
    repetition = surface_file.parents[1].name
    plt.plot(time, contact_fraction, alpha=0.75, linewidth=1, label=repetition)

# Mark the 80% adsorption threshold
plt.axhline(
    0.8,
    linestyle="--",
    label="80% adsorption threshold"
)

plt.xlabel("Time (LJ units)")
plt.ylabel("Fraction of beads in contact")
plt.title(f"Polymer Contact Fraction vs Time (N={N}, {len(surface_files)} repetitions)")

plt.ylim(0, 1.05)
plt.xlim(0, time[-1])
plt.legend(loc="upper left", bbox_to_anchor=(1.01, 1))
plt.grid(True)
plt.tight_layout()

# Save figure
output_folder = Path(__file__).resolve().parent / "results"
output_folder.mkdir(exist_ok=True)

output_file = output_folder / f"contact_fraction_N{N}_all_reps.png"

plt.savefig(output_file, dpi=300, bbox_inches="tight")

print(f"Figure saved to: {output_file}")
