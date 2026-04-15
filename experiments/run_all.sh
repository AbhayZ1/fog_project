#!/bin/bash
#
# MASTER RUN SCRIPT — Runs all 3 experiments sequentially
# Each experiment takes ~2+ hours on CPU.
# Total estimated time: ~5-7 hours.
#
# Usage:
#   cd experiments/
#   bash run_all.sh 2>&1 | tee ../logs_all_experiments.txt
#
# Or run individual experiments:
#   bash run_no_dp.sh 2>&1 | tee ../logs_no_dp.txt
#   bash run_fedavg.sh 2>&1 | tee ../logs_fedavg.txt
#   bash run_centralized.sh 2>&1 | tee ../logs_centralized.txt
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "  MASTER EXPERIMENT RUNNER"
echo "========================================"
echo "Script Dir:  $SCRIPT_DIR"
echo "Project Dir: $PROJECT_DIR"
echo "Start Time:  $(date)"
echo "========================================"
echo ""

# ===== RUN 1: No-DP =====
echo "========================================"
echo "  STARTING RUN 1: No-DP Baseline"
echo "  $(date)"
echo "========================================"
cd "$SCRIPT_DIR"
bash run_no_dp.sh 2>&1 | tee "$PROJECT_DIR/logs_no_dp.txt"
echo ""
echo "RUN 1 finished at $(date)"
echo ""

# Wait between experiments for cleanup
sleep 10

# ===== RUN 2: FedAvg =====
echo "========================================"
echo "  STARTING RUN 2: FedAvg Baseline"
echo "  $(date)"
echo "========================================"
cd "$SCRIPT_DIR"
bash run_fedavg.sh 2>&1 | tee "$PROJECT_DIR/logs_fedavg.txt"
echo ""
echo "RUN 2 finished at $(date)"
echo ""

sleep 10

# ===== RUN 3: Centralized =====
echo "========================================"
echo "  STARTING RUN 3: Centralized Baseline"
echo "  $(date)"
echo "========================================"
cd "$SCRIPT_DIR"
bash run_centralized.sh 2>&1 | tee "$PROJECT_DIR/logs_centralized.txt"
echo ""
echo "RUN 3 finished at $(date)"
echo ""

# ===== Generate Comparison =====
echo "========================================"
echo "  GENERATING COMPARISON SUMMARY"
echo "========================================"
cd "$SCRIPT_DIR"
uv run --project "$PROJECT_DIR" python generate_comparison.py

echo ""
echo "========================================"
echo "  ALL EXPERIMENTS COMPLETE!"
echo "  $(date)"
echo "========================================"
echo ""
echo "Output files:"
echo "  $PROJECT_DIR/fl_metrics_no_dp.json"
echo "  $PROJECT_DIR/fl_metrics_fedavg.json"
echo "  $PROJECT_DIR/centralized_baseline.json"
echo "  $PROJECT_DIR/logs_no_dp.txt"
echo "  $PROJECT_DIR/logs_fedavg.txt"
echo "  $PROJECT_DIR/logs_centralized.txt"
echo "  $PROJECT_DIR/comparison_summary.txt"
