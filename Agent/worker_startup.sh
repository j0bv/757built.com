#!/bin/bash
# Worker startup script for 757Built document processor
# This script is used to start the document processor worker
# with automatic code updates via git pull

set -e  # Exit on any error

# Config - adjust these as needed
REPO_DIR="/root/757built.com"
MODEL_PATH="/root/models/phi3-q3_k_l.gguf"
LLAMA_PATH="/root/llama.cpp/main"
VENV_PATH="${REPO_DIR}/venv"
WORKER_SCRIPT="${REPO_DIR}/Agent/enhanced_document_processor.py"
BRANCH="main"
GIT_REMOTE="origin"
LOG_FILE="/var/log/757built/worker.log"

# Ensure log directory exists
mkdir -p $(dirname "$LOG_FILE")

echo "[$(date)] Starting worker startup script" | tee -a "$LOG_FILE"

# Change to repository directory
cd "$REPO_DIR"
echo "[$(date)] Current directory: $(pwd)" | tee -a "$LOG_FILE"

# Check for git repository and if it exists, update the code
if [ -d ".git" ]; then
    echo "[$(date)] Git repository found, checking for updates..." | tee -a "$LOG_FILE"
    
    # Fetch updates from remote
    echo "[$(date)] Running: git fetch $GIT_REMOTE $BRANCH" | tee -a "$LOG_FILE"
    git fetch "$GIT_REMOTE" "$BRANCH"
    
    # Check if local is behind remote
    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse "$GIT_REMOTE"/"$BRANCH")
    
    if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
        echo "[$(date)] Updates available. Local: $LOCAL_COMMIT, Remote: $REMOTE_COMMIT" | tee -a "$LOG_FILE"
        
        # Check for uncommitted changes
        if ! git diff --quiet; then
            echo "[$(date)] Warning: Uncommitted changes detected!" | tee -a "$LOG_FILE"
            echo "[$(date)] Stashing local changes before pull" | tee -a "$LOG_FILE"
            git stash
        fi
        
        # Pull updates
        echo "[$(date)] Running: git pull --ff-only $GIT_REMOTE $BRANCH" | tee -a "$LOG_FILE"
        if git pull --ff-only "$GIT_REMOTE" "$BRANCH"; then
            echo "[$(date)] Code updated successfully to $(git rev-parse HEAD)" | tee -a "$LOG_FILE"
        else
            echo "[$(date)] Error during git pull. Continuing with existing code." | tee -a "$LOG_FILE"
        fi
    else
        echo "[$(date)] Code is up to date (commit: $LOCAL_COMMIT)" | tee -a "$LOG_FILE"
    fi
else
    echo "[$(date)] Not a git repository or .git directory not found" | tee -a "$LOG_FILE"
fi

# Activate virtual environment if it exists
if [ -d "$VENV_PATH" ]; then
    echo "[$(date)] Activating virtual environment at $VENV_PATH" | tee -a "$LOG_FILE"
    source "$VENV_PATH/bin/activate"
fi

# Check if model exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "[$(date)] Error: Model file not found at $MODEL_PATH" | tee -a "$LOG_FILE"
    exit 1
fi

# Check if llama.cpp executable exists
if [ ! -f "$LLAMA_PATH" ]; then
    echo "[$(date)] Error: llama.cpp executable not found at $LLAMA_PATH" | tee -a "$LOG_FILE"
    exit 1
fi

# Start the worker
echo "[$(date)] Starting document processor worker" | tee -a "$LOG_FILE"
echo "[$(date)] Command: python $WORKER_SCRIPT --model-path $MODEL_PATH --llama-path $LLAMA_PATH" | tee -a "$LOG_FILE"

# Execute the worker script
exec python "$WORKER_SCRIPT" --model-path "$MODEL_PATH" --llama-path "$LLAMA_PATH" --queue

# Note: If we reach here, something went wrong with exec
echo "[$(date)] Worker exited unexpectedly" | tee -a "$LOG_FILE"
exit 1 