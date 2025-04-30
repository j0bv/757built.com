#!/bin/bash
# Complete workflow for Phi-3 document processing and IPFS publishing

set -e

# Configuration - modify these values as needed
PHI3_MODEL_PATH="/path/to/phi3.gguf"
REDIS_PORT=6379
RAW_DIR="data/raw"
PROCESSED_DIR="data/processed"
LOGS_DIR="logs"
IPFS_API="/ip4/127.0.0.1/tcp/5001"
BATCH_LIMIT=100
MAX_RETRIES=3

# Create directories if they don't exist
mkdir -p $RAW_DIR
mkdir -p $PROCESSED_DIR
mkdir -p $LOGS_DIR

echo "Starting Phi-3 IPFS workflow..."
timestamp=$(date +"%Y%m%d_%H%M%S")
logfile="$LOGS_DIR/workflow_$timestamp.log"

# Helper function to log messages
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $logfile
}

# Check dependencies
log "Checking dependencies..."

# Check if Redis is running
if ! redis-cli -p $REDIS_PORT ping > /dev/null 2>&1; then
  log "Starting Redis server..."
  redis-server --port $REDIS_PORT --daemonize yes
  sleep 2
else
  log "Redis server already running."
fi

# Check if IPFS daemon is running
if ! ipfs --api $IPFS_API id > /dev/null 2>&1; then
  log "ERROR: IPFS daemon not running. Please start it with 'ipfs daemon'"
  exit 1
else
  log "IPFS daemon is running."
fi

# Check if Phi-3 model exists
if [ ! -f "$PHI3_MODEL_PATH" ]; then
  log "ERROR: Phi-3 model not found at $PHI3_MODEL_PATH"
  exit 1
else
  log "Phi-3 model found at $PHI3_MODEL_PATH"
fi

# Step 1: Start document processor
log "Starting document processor with Phi-3 model..."
nohup python Agent/enhanced_document_processor.py --model-path $PHI3_MODEL_PATH --queue > $LOGS_DIR/processor_$timestamp.log 2>&1 &
PROCESSOR_PID=$!
log "Document processor started with PID: $PROCESSOR_PID"

# Give the processor a moment to initialize
sleep 5

# Step 2: Run ingestion orchestrator
log "Starting ingestion orchestrator..."
python -m ingestion.orchestrator --out $RAW_DIR

# Wait for processing to complete
log "Waiting for document processing to complete..."
sleep 30  # Adjust this based on your expected processing time

# Check if there are documents in the processed directory
processed_count=$(find $PROCESSED_DIR -name "*.json" | wc -l)
log "Found $processed_count processed documents."

if [ $processed_count -eq 0 ]; then
  log "No processed documents found. Checking processor logs..."
  tail -n 50 $LOGS_DIR/processor_$timestamp.log | tee -a $logfile
  
  # Wait a bit longer if no documents are found
  log "Waiting additional time for processing..."
  sleep 60
  
  processed_count=$(find $PROCESSED_DIR -name "*.json" | wc -l)
  log "Found $processed_count processed documents after waiting."
  
  if [ $processed_count -eq 0 ]; then
    log "ERROR: No documents were processed. Check logs for details."
    log "Stopping processor..."
    kill $PROCESSOR_PID
    exit 1
  fi
fi

# Step 3: Verify document quality
log "Verifying document quality..."
if ! python -m ipfs.verify_data --dir $PROCESSED_DIR; then
  log "WARNING: Some documents failed verification."
  log "Proceeding with only valid documents."
else
  log "All documents passed verification."
fi

# Step 4: Upload documents to IPFS
log "Uploading documents to IPFS (limit: $BATCH_LIMIT)..."

retry_count=0
upload_success=false

while [ $retry_count -lt $MAX_RETRIES ] && [ "$upload_success" = false ]; do
  if python -m ipfs.batch_upload --dir $PROCESSED_DIR --api $IPFS_API --limit $BATCH_LIMIT; then
    upload_success=true
    log "Upload to IPFS completed successfully."
  else
    retry_count=$((retry_count+1))
    if [ $retry_count -lt $MAX_RETRIES ]; then
      log "Upload failed. Retrying ($retry_count/$MAX_RETRIES)..."
      sleep 10
    else
      log "ERROR: Failed to upload documents to IPFS after $MAX_RETRIES attempts."
    fi
  fi
done

# Step 5: Clean up
log "Stopping document processor..."
kill $PROCESSOR_PID || true

log "Workflow complete!"
log "See reports in the current directory for verification and upload details."

# Print summary
echo "================ WORKFLOW SUMMARY ================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Documents processed: $processed_count"
echo "Upload status: $(if [ "$upload_success" = true ]; then echo "Success"; else echo "Failed"; fi)"
echo "Log file: $logfile"
echo "==================================================" 