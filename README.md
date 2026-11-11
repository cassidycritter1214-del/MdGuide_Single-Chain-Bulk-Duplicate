# Single-chain bulk and surface adsorption simulations

LAMMPS and Python scripts for generating polymer configurations, running bulk
equilibration and surface adsorption simulations, and analyzing adsorption
events and contact data.

## Running simulations

Edit the settings in `0-scripts/init/init_run.sh`, then run it from the project
root:

```bash
bash 0-scripts/init/init_run.sh
```

The script activates the `polymer` Conda environment and runs the configured
chain lengths, repetitions, and simulation stage. See the command-line options
in `0-scripts/init/run_experiment.py` for direct invocation.

## Generated files

LAMMPS trajectories, logs, events, restart checkpoints, and final configurations
are generated under `1-surface-runs/`. These run outputs stay local and are
excluded from Git because they can be very large. Input scripts and source code
are tracked in this repository.
