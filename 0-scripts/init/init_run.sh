#!/bin/bash
set -e

# Activate the environment before running the experiment runner.
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate polymer

# Locate project directories
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Launching experiment pipeline via run_experiment.py..."
python "$SCRIPT_DIR/run_experiment.py"