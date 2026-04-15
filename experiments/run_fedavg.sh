#!/bin/bash
#
# RUN 2: FedAvg Baseline (with DP)
# Start server + 2 clients, capture all output to logs_fedavg.txt
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== RUN 2: FedAvg Baseline ==="
echo "Working directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_DIR"
echo ""

cd "$SCRIPT_DIR"

# Clean up stale processes from previous runs
echo "Cleaning up stale processes..."
pkill -f "server_fedavg.py" 2>/dev/null
pkill -f "client_A_fedavg.py" 2>/dev/null
pkill -f "client_B_fedavg.py" 2>/dev/null
sleep 2

# Force-kill anything on port 8081
fuser -k 8081/tcp 2>/dev/null
sleep 2

# Verify port is free
if ss -tlnp 2>/dev/null | grep -q 8081; then
    echo "ERROR: Port 8081 still in use. Waiting 10 seconds..."
    sleep 10
    fuser -k 8081/tcp 2>/dev/null
    sleep 2
fi
echo "Port 8081 is ready."

# Start server in background
echo "Starting FedAvg server..."
uv run --project "$PROJECT_DIR" python server_fedavg.py &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for server
sleep 8

# Start Client A
echo "Starting Client A (FedAvg + DP)..."
uv run --project "$PROJECT_DIR" python client_A_fedavg.py &
CLIENT_A_PID=$!
echo "Client A PID: $CLIENT_A_PID"

sleep 3

# Start Client B
echo "Starting Client B (FedAvg + DP)..."
uv run --project "$PROJECT_DIR" python client_B_fedavg.py &
CLIENT_B_PID=$!
echo "Client B PID: $CLIENT_B_PID"

echo ""
echo "All processes started. Waiting for completion..."
echo "Server: $SERVER_PID | Client A: $CLIENT_A_PID | Client B: $CLIENT_B_PID"
echo ""

wait $SERVER_PID
SERVER_EXIT=$?

echo "Server finished (exit code: $SERVER_EXIT)"
sleep 5

kill $CLIENT_A_PID 2>/dev/null
kill $CLIENT_B_PID 2>/dev/null
wait $CLIENT_A_PID 2>/dev/null
wait $CLIENT_B_PID 2>/dev/null

if [ -f "fl_metrics_fedavg.json" ]; then
    cp "fl_metrics_fedavg.json" "$PROJECT_DIR/fl_metrics_fedavg.json"
    echo "✅ Metrics copied to $PROJECT_DIR/fl_metrics_fedavg.json"
fi

echo ""
echo "=== RUN 2 COMPLETE ==="
