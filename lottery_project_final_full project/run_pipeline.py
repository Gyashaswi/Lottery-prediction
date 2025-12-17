#!/usr/bin/env python3
"""
Master Pipeline Script for NY Lottery Data Project.

Runs the complete data pipeline:
1. Fetch data from NY Open Data APIs
2. Clean and normalize data
3. Load to simple SQLite database
4. Load to normalized star schema database
5. Run data quality checks
6. Build database indices

Usage:
    python run_pipeline.py [--step STEP]
    
Steps: fetch, clean, load, load_star, dq, indices, all (default)
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingest.fetch_api import main as fetch_main
from src.ingest.clean_data import main as clean_main
from src.ingest.load_to_db import main as load_main
from src.ingest.load_to_star import main as load_star_main
from src.ingest.dq_checks import main as dq_main
from src.ingest.build_indices import main as indices_main

def run_step(step_name: str, step_func, description: str):
    """Run a pipeline step with logging."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")
    try:
        step_func()
        print(f"\n✓ {step_name} completed successfully")
        return True
    except Exception as e:
        print(f"\n✗ {step_name} failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run NY Lottery data pipeline')
    parser.add_argument('--step', choices=['fetch', 'clean', 'load', 'load_star', 'dq', 'indices', 'all'],
                       default='all', help='Pipeline step to run')
    args = parser.parse_args()
    
    steps = {
        'fetch': (fetch_main, 'Fetching data from NY Open Data APIs'),
        'clean': (clean_main, 'Cleaning and normalizing data'),
        'load': (load_main, 'Loading to simple SQLite database'),
        'load_star': (load_star_main, 'Loading to normalized star schema'),
        'dq': (dq_main, 'Running data quality checks'),
        'indices': (indices_main, 'Building database indices'),
    }
    
    if args.step == 'all':
        print("\n" + "="*60)
        print("NY LOTTERY DATA PIPELINE - FULL RUN")
        print("="*60)
        
        success_count = 0
        for step_name, (step_func, desc) in steps.items():
            if run_step(step_name, step_func, desc):
                success_count += 1
        
        print(f"\n{'='*60}")
        print(f"PIPELINE COMPLETE: {success_count}/{len(steps)} steps successful")
        print(f"{'='*60}")
        
        # Print data summary
        print("\nData files created:")
        for d in ['data/processed', 'data/clean']:
            path = PROJECT_ROOT / d
            if path.exists():
                files = list(path.glob('*.csv'))
                print(f"  {d}/: {len(files)} CSV files")
        
        for db in ['data/lottery.db', 'data/lottery_star.db']:
            path = PROJECT_ROOT / db
            if path.exists():
                size_mb = path.stat().st_size / (1024 * 1024)
                print(f"  {db}: {size_mb:.2f} MB")
    else:
        step_func, desc = steps[args.step]
        run_step(args.step, step_func, desc)

if __name__ == '__main__':
    main()
