@echo off
:: Test script for phi-3 model on Server1 with ingestion framework (Windows version)
title Server1 Phi-3 Q3_K_L Test

echo Starting phi-3 model test on Server1...

:: Configuration (adjust paths as needed)
set PHI3_MODEL_PATH=C:\Users\Jo\7\phi3-q3_k_l.gguf
set PROJECT_DIR=C:\Users\Jo\7
set REDIS_PORT=6379
set OUTPUT_DIR=%PROJECT_DIR%\data\raw
set PROCESSED_DIR=%PROJECT_DIR%\data\processed
set LOGS_DIR=%PROJECT_DIR%\logs
set WEB_API_ENDPOINT=https://api.757built.com/ipfs_hashes.php

:: Fix Python path to include 757built.com
set PYTHONPATH=%PROJECT_DIR%;%PROJECT_DIR%\757built.com;%PYTHONPATH%

:: Create directories if they don't exist
if not exist %OUTPUT_DIR% mkdir %OUTPUT_DIR%
if not exist %PROCESSED_DIR% mkdir %PROCESSED_DIR%
if not exist %LOGS_DIR% mkdir %LOGS_DIR%

:: Check if Redis is running, don't start if not (requires manual start on Windows)
redis-cli -p %REDIS_PORT% ping >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo Redis server is not running. Please start Redis before continuing.
  echo You can start Redis using: redis-server --port %REDIS_PORT%
  exit /b 1
) else (
  echo Redis server is running.
)

:: Start the document processor with phi-3 model in a new command window
echo Starting document processor with phi-3 Q3_K_L model...
start "Phi-3 Document Processor" cmd /c "title Phi-3 Document Processor && python %PROJECT_DIR%\757built.com\Agent\enhanced_document_processor.py --model-path %PHI3_MODEL_PATH% --queue --output-dir %PROCESSED_DIR% --web-api %WEB_API_ENDPOINT% > %LOGS_DIR%\processor.log 2>&1"

:: Wait for processor to initialize
timeout /t 5 /nobreak

:: Start the orchestrator with all plugins in a new command window
echo Starting ingestion orchestrator...
cd %PROJECT_DIR%\757built.com
start "Ingestion Orchestrator" cmd /c "title Ingestion Orchestrator && python -m ingestion.orchestrator --out %OUTPUT_DIR% > %LOGS_DIR%\orchestrator.log 2>&1"
cd %PROJECT_DIR%

echo Test setup complete. Monitoring logs...
echo Processor log: %LOGS_DIR%\processor.log
echo Orchestrator log: %LOGS_DIR%\orchestrator.log

:: Wait for a while to collect some data
echo Waiting for 5 minutes to collect initial data...
timeout /t 300 /nobreak

:: Check processed documents
echo Checking processed documents...
dir %PROCESSED_DIR%\*.json 2>nul
if %ERRORLEVEL% NEQ 0 (
  echo No processed documents found yet. This could be normal if processing is still ongoing.
) else (
  echo Found processed documents. System appears to be working.
)

echo To verify IPFS readiness, run: python -m ipfs.verify_data --dir %PROCESSED_DIR%
echo.
echo Test script complete. The processor and orchestrator are running in background windows.
echo To close them, close their respective command windows. 