#!/bin/bash
#
# RUN 1: No-DP Baseline
# Start server + 2 clients, capture all output to logs_no_dp.txt
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== RUN 1: No-DP Baseline ==="
echo "Working directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_DIR"
echo ""

# Use uv from project root
cd "$SCRIPT_DIR"

# Start server in background
echo "Starting No-DP server..."
uv run --project "$PROJECT_DIR" python server_no_dp.py &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for server to initialize
sleep 8

# Start Client A
echo "Starting Client A (No DP)..."
uv run --project "$PROJECT_DIR" python client_A_no_dp.py &
CLIENT_A_PID=$!
echo "Client A PID: $CLIENT_A_PID"

# Small delay between clients
sleep 3

# Start Client B
echo "Starting Client B (No DP)..."
uv run --project "$PROJECT_DIR" python client_B_no_dp.py &
CLIENT_B_PID=$!
echo "Client B PID: $CLIENT_B_PID"

echo ""
echo "All processes started. Waiting for completion..."
echo "Server: $SERVER_PID | Client A: $CLIENT_A_PID | Client B: $CLIENT_B_PID"
echo ""

# Wait for server (it exits when training completes)
wait $SERVER_PID
SERVER_EXIT=$?

echo ""
echo "Server finished (exit code: $SERVER_EXIT)"
echo "Waiting for clients to terminate..."

# Give clients a moment to disconnect
sleep 5

# Kill remaining clients if needed
kill $CLIENT_A_PID 2>/dev/null
kill $CLIENT_B_PID 2>/dev/null
wait $CLIENT_A_PID 2>/dev/null
wait $CLIENT_B_PID 2>/dev/null

# Copy metrics to project root
if [ -f "fl_metrics_no_dp.json" ]; then
    cp "fl_metrics_no_dp.json" "$PROJECT_DIR/fl_metrics_no_dp.json"
    echo "✅ Metrics copied to $PROJECT_DIR/fl_metrics_no_dp.json"
fi

echo ""
echo "=== RUN 1 COMPLETE ==="
