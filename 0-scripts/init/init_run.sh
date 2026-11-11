
#!/bin/bash
set -e

# ==========================================
# SIMULATION SETTINGS — EDIT THESE
# ==========================================

# Choose: "bulk" or "adsorption"
STAGE="bulk"

# Chain lengths to simulate
CHAIN_LENGTHS=(100) # do 10 to 100

# Number of repetitions per chain length
REPETITIONS=1

# Simulation box dimensions
BOX_X=100.0
BOX_Y=100.0
BOX_Z=50.0 # for N=200, Lz=40 is too small

# Simulation lengths (number of timesteps)
BULK_STEPS=20000000 # at least 20mil
ADSORPTION_STEPS=20000000 # at least 20mil

# ==========================================
# DO NOT NEED TO EDIT BELOW THIS LINE
# ==========================================

# Activate the polymer conda environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate polymer

# Locate project directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "Polymer simulation"
echo "Stage: $STAGE"
echo "Chain lengths: ${CHAIN_LENGTHS[*]}"
echo "Repetitions: $REPETITIONS"
echo "=========================================="

python "$SCRIPT_DIR/run_experiment.py" \
    --stage "$STAGE" \
    --chain-lengths "${CHAIN_LENGTHS[@]}" \
    --repetitions "$REPETITIONS" \
    --lx "$BOX_X" \
    --ly "$BOX_Y" \
    --lz "$BOX_Z" \
    --bulk-steps "$BULK_STEPS" \
    --adsorption-steps "$ADSORPTION_STEPS"