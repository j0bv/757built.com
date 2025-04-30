@echo off
:: Batch upload processed documents to IPFS (Windows version)
title IPFS Batch Upload

echo Starting IPFS batch upload process...

:: Configuration
set PROJECT_DIR=C:\Users\Jo\7
set PROCESSED_DIR=%PROJECT_DIR%\data\processed
set IPFS_API=/ip4/127.0.0.1/tcp/5001
set BATCH_LIMIT=50

:: Fix Python path to include 757built.com and root project
set PYTHONPATH=%PROJECT_DIR%;%PROJECT_DIR%\757built.com;%PYTHONPATH%

:: Create timestamp for logging
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "timestamp=%dt:~0,8%_%dt:~8,6%"
set "log_file=ipfs_upload_%timestamp%.log"

:: Check if IPFS daemon is running
echo Checking IPFS daemon...
ipfs --api %IPFS_API% id >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo ERROR: IPFS daemon not running. Please start it with 'ipfs daemon'
  exit /b 1
) else (
  echo IPFS daemon is running.
)

:: Step 1: Verify documents
echo Verifying document quality before upload...
python "%PROJECT_DIR%\ipfs\verify_data.py" --dir "%PROCESSED_DIR%" > "%log_file%" 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo WARNING: Some documents failed verification. See %log_file% for details.
  echo Proceeding with only valid documents.
) else (
  echo All documents passed verification.
)

:: Step 2: Upload to IPFS
echo Uploading documents to IPFS (limit: %BATCH_LIMIT%)...
python "%PROJECT_DIR%\ipfs\batch_upload.py" --dir "%PROCESSED_DIR%" --api "%IPFS_API%" --limit %BATCH_LIMIT% >> "%log_file%" 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo ERROR: Upload failed. See %log_file% for details.
  exit /b 1
) else (
  echo Upload to IPFS completed successfully.
)

:: Display summary
echo.
echo ================ UPLOAD SUMMARY ================
echo Timestamp: %timestamp%
echo Log file: %log_file%
type %log_file% | findstr "Uploaded"
echo ================================================
echo.
echo Process complete! See %log_file% for full details. 