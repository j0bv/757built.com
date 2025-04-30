#!/bin/bash
# Test script for phi-3 model on Server1 with ingestion framework

set -e

# Configuration (adjust paths as needed)
PHI3_MODEL_PATH="/path/to/(Phi-3 Q3_K_L.gguf"
REDIS_PORT=6379
OUTPUT_DIR="data/raw"
LOGS_DIR="logs"

# Create directories if they don't exist
mkdir -p $OUTPUT_DIR
mkdir -p $LOGS_DIR

echo "Starting phi-3 model test on Server1..."

# Check if Redis is running, start if not
redis_running=$(pgrep redis-server || echo "")
if [ -z "$redis_running" ]; then
  echo "Starting Redis server..."
  redis-server --port $REDIS_PORT --daemonize yes
else
  echo "Redis server already running."
fi

# Start the document processor with phi-3 model
echo "Starting document processor with phi-3 model..."
nohup python Agent/enhanced_document_processor.py --model-path $PHI3_MODEL_PATH --queue > $LOGS_DIR/processor.log 2>&1 &
PROCESSOR_PID=$!
echo "Document processor started with PID: $PROCESSOR_PID"

# Start the orchestrator with all plugins in a separate process
echo "Starting ingestion orchestrator..."
nohup python -m ingestion.orchestrator --out $OUTPUT_DIR > $LOGS_DIR/orchestrator.log 2>&1 &
ORCHESTRATOR_PID=$!
echo "Orchestrator started with PID: $ORCHESTRATOR_PID"

echo "Test setup complete. Monitoring logs..."
echo "Processor log: $LOGS_DIR/processor.log"
echo "Orchestrator log: $LOGS_DIR/orchestrator.log"

# Function to check if a process is still running
is_running() {
  ps -p $1 > /dev/null
  return $?
}

# Wait for a while to collect some data
echo "Waiting for 5 minutes to collect initial data..."
sleep 300

# Check if processes are still running
if is_running $PROCESSOR_PID && is_running $ORCHESTRATOR_PID; then
  echo "All processes running correctly."
else
  echo "WARNING: Some processes have stopped."
  [ ! is_running $PROCESSOR_PID ] && echo "Document processor stopped."
  [ ! is_running $ORCHESTRATOR_PID ] && echo "Orchestrator stopped."
fi

echo "To stop the test, run: kill $PROCESSOR_PID $ORCHESTRATOR_PID"
echo "To check processed documents: ls -la data/processed/"
echo "To verify IPFS readiness: python -m ipfs.verify_data" 