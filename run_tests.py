#!/usr/bin/env python3
"""
AutoTest - Test Runner
Run unit tests and generate coverage reports
"""

import sys
import subprocess
import os
from pathlib import Path

def run_tests():
    """Run the test suite"""
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🧪 Running AutoTest Unit Tests")
    print("=" * 50)
    
    # Activate virtual environment and run tests
    venv_python = project_root / "venv" / "bin" / "python"
    
    if not venv_python.exists():
        print("❌ Virtual environment not found. Please run: python -m venv venv")
        return 1
    
    # Run pytest with coverage
    cmd = [
        str(venv_python), "-m", "pytest",
        "autotest/tests/unit/",
        "-v",
        "--tb=short",
        "--cov=autotest",
        "--cov-report=html:autotest/tests/htmlcov",
        "--cov-report=term-missing",
        "--durations=10"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            print("\n📊 Coverage report generated at: autotest/tests/htmlcov/index.html")
        else:
            print(f"\n❌ Tests failed with exit code: {result.returncode}")
            
        return result.returncode
        
    except FileNotFoundError:
        print("❌ Python not found in virtual environment")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

def run_specific_test(test_path):
    """Run a specific test file or test function"""
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    venv_python = project_root / "venv" / "bin" / "python"
    
    cmd = [
        str(venv_python), "-m", "pytest",
        test_path,
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return 1

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Run specific test
        test_path = sys.argv[1]
        return run_specific_test(test_path)
    else:
        # Run all tests
        return run_tests()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)