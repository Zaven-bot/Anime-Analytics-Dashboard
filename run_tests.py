#!/usr/bin/env python3
"""
Test runner script for AnimeDashboard ETL tests.
Runs unit tests with proper path configuration.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add ETL source to Python path
project_root = Path(__file__).parent
etl_src_path = project_root / "etl"
sys.path.insert(0, str(etl_src_path))

def run_tests():
    """Run the test suite"""
    print("Running AnimeDashboard ETL Unit Tests")
    print("=" * 50)
    
    # Install test requirements if needed
    try:
        import pytest
    except ImportError:
        print("Installing test requirements...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "-r", "tests/requirements.txt"
        ], check=True)
    
    # Run pytest with configuration
    test_args = [
        "python", "-m", "pytest",
        "tests/unit/",
        "-v",
        "--tb=short"
    ]
    
    print(f"Running: {' '.join(test_args)}")
    print("-" * 50)
    
    result = subprocess.run(test_args, cwd=project_root)
    
    if result.returncode == 0:
        print("\nAll tests passed! ✅")
    else:
        print(f"\nTests failed with exit code {result.returncode}")
    
    return result.returncode

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
