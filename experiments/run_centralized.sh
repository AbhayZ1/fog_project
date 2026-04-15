#!/bin/bash
#
# RUN 3: Centralized Baseline (no federation, no DP)
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== RUN 3: Centralized Baseline ==="
echo "Working directory: $SCRIPT_DIR"
echo ""

cd "$SCRIPT_DIR"

uv run --project "$PROJECT_DIR" python centralized_train.py

if [ -f "centralized_baseline.json" ]; then
    cp "centralized_baseline.json" "$PROJECT_DIR/centralized_baseline.json"
    echo "✅ Results copied to $PROJECT_DIR/centralized_baseline.json"
fi

echo ""
echo "=== RUN 3 COMPLETE ==="
