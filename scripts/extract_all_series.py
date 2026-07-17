#!/usr/bin/env python3
"""
Extract All Series Script
-------------------------
This script iterates over all series configurations in `data/series/*.yaml`, reads the 
associated `die` mapping, and automatically calls `extract_series.py` to regenerate 
the disabled peripherals and interrupts based on the Series' SVD.

Usage:
  python3 scripts/extract_all_series.py
"""

import os
import glob
import yaml
import subprocess
import sys

def main():
    # Ensure we are running from the root of the repository (py32-data)
    if not os.path.exists("data/series") or not os.path.exists("scripts/extract_series.py"):
        print("Error: Please run this script from the root directory of the py32-data project.")
        print("Example: python3 scripts/extract_all_series.py")
        sys.exit(1)

    series_files = glob.glob('data/series/*.yaml')
    if not series_files:
        print("Error: No series YAML files found in data/series/")
        sys.exit(1)

    success_count = 0
    failure_count = 0
    skipped_count = 0

    print(f"Found {len(series_files)} series configurations. Starting extraction...")
    print("-" * 60)

    for series_yaml in sorted(series_files):
        series_name = os.path.basename(series_yaml).replace('.yaml', '')
        
        # Extract die mapping
        try:
            with open(series_yaml, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if not config:
                    print(f"[{series_name}] Error: Empty YAML file.")
                    failure_count += 1
                    continue
                die = config.get('die')
        except Exception as e:
            print(f"[{series_name}] Error reading YAML: {e}")
            failure_count += 1
            continue
            
        if not die:
            print(f"[{series_name}] Skipped: No 'die' defined in YAML.")
            skipped_count += 1
            continue
            
        svd_path = f'svd/{series_name}xx.svd'
        if not os.path.exists(svd_path):
            print(f"[{series_name}] Skipped: SVD not found at {svd_path}.")
            skipped_count += 1
            continue
            
        print(f"[{series_name}] Extracting against {die}...")
        
        try:
            result = subprocess.run(
                ['python3', 'scripts/extract_series.py', '--die', die, '--series', series_name, '--svd', svd_path],
                check=True,
                capture_output=True,
                text=True
            )
            # You can print result.stdout here if you want verbose output
            # print(result.stdout.strip())
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"[{series_name}] ERROR: extract_series.py failed with exit code {e.returncode}.")
            print("--- Standard Error ---")
            print(e.stderr.strip())
            print("----------------------")
            failure_count += 1

    print("-" * 60)
    print("Summary:")
    print(f"  Total Series Processed: {len(series_files)}")
    print(f"  Success: {success_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Failed:  {failure_count}")

    if failure_count > 0:
        sys.exit(1)
    else:
        print("\nAll extractions completed successfully!")

if __name__ == "__main__":
    main()
