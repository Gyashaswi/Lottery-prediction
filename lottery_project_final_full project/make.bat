@echo off
REM Windows replacement for "make update"

IF "%1"=="update" (
    echo [RUN] Updating pipeline...
    python -m src.ingest.fetch_api
    python -m src.ingest.clean_data
    python -m src.ingest.load_to_db
    python -m src.ingest.load_to_star
    python -m src.ingest.dq_checks
    python -m src.ingest.build_indices
    echo ✅ Pipeline complete.
    exit /b 0
)

IF "%1"=="fetch" (
    python -m src.ingest.fetch_api
    exit /b 0
)

IF "%1"=="clean" (
    python -m src.ingest.clean_data
    exit /b 0
)

IF "%1"=="load" (
    python -m src.ingest.load_to_db
    exit /b 0
)

IF "%1"=="star" (
    python -m src.ingest.load_to_star
    exit /b 0
)

IF "%1"=="dq" (
    python -m src.ingest.dq_checks
    exit /b 0
)

IF "%1"=="idx" (
    python -m src.ingest.build_indices
    exit /b 0
)

echo Usage:
echo   make update   - run full pipeline
echo   make fetch    - only fetch data
echo   make clean    - only clean data
echo   make load     - load to simple DB
echo   make star     - load to star DB
echo   make dq       - run data quality checks
echo   make idx      - build indices
