@echo off
:: schedule_ingest.bat
:: This batch script runs the swim data ingestion pipeline and logs the output.
:: You can schedule this to run weekly using Windows Task Scheduler.

:: Move to the directory where this script is located
cd /d "%~dp0"

:: Create a logs directory if it doesn't exist
if not exist logs mkdir logs

:: Generate a timestamp for the log file
set year=%date:~10,4%
set month=%date:~4,2%
set day=%date:~7,2%
set hour=%time:~0,2%
:: Replace space in hour with 0 if it's single digit
if "%hour:~0,1%" == " " set hour=0%hour:~1,1%
set minute=%time:~3,2%
set timestamp=%year%-%month%-%day%_%hour%-%minute%

set LOG_FILE=logs\pipeline_%timestamp%.log

echo ================================================== > "%LOG_FILE%"
echo STARTING WEEKLY SWIM INGESTION PIPELINE: %date% %time% >> "%LOG_FILE%"
echo ================================================== >> "%LOG_FILE%"

:: Set Python Path to include current directory
set PYTHONPATH=.

:: Optional: Activate Python Virtual Environment
:: If you use a virtual environment (e.g. venv or .venv), uncomment the line below:
:: call .venv\Scripts\activate.bat

:: Execute the pipeline
echo Running python run_pipeline.py... >> "%LOG_FILE%"
python run_pipeline.py >> "%LOG_FILE%" 2>&1

if %ERRORLEVEL% equ 0 (
    echo SUCCESS: Pipeline completed. >> "%LOG_FILE%"
    echo pipeline run was SUCCESSFUL.
) else (
    echo ERROR: Pipeline failed with error code %ERRORLEVEL%. >> "%LOG_FILE%"
    echo pipeline run FAILED. See log at "%LOG_FILE%"
)

echo ================================================== >> "%LOG_FILE%"
echo PIPELINE FINISHED AT: %date% %time% >> "%LOG_FILE%"
echo ================================================== >> "%LOG_FILE%"
