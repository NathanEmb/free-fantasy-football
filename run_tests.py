#!/usr/bin/env python3
"""
Test runner for the fantasy football application
"""

import os
import sys
import subprocess

def run_test_file(test_file):
    """Run a specific test file"""
    print(f"🧪 Running {test_file}...")
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, cwd=os.getcwd())
        print(result.stdout)
        if result.stderr:
            print(f"⚠️  Warnings/Errors: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run {test_file}: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Test Suite...")
    
    # List of test files to run
    test_files = [
        "tests/test_espn_adapter.py",
    ]
    
    passed = 0
    total = len(test_files)
    
    for test_file in test_files:
        if os.path.exists(test_file):
            if run_test_file(test_file):
                passed += 1
                print(f"✅ {test_file} passed\n")
            else:
                print(f"❌ {test_file} failed\n")
        else:
            print(f"⚠️  {test_file} not found\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 