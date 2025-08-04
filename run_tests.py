#!/usr/bin/env python3
"""
Test runner for the fantasy football application
"""

import os
import subprocess
import sys

from logging_config import get_logger


def run_test_file(test_file):
    """Run a specific test file"""
    logger = get_logger(__name__)
    logger.info(f"🧪 Running {test_file}...")
    try:
        result = subprocess.run(
            [sys.executable, test_file], capture_output=True, text=True, cwd=os.getcwd()
        )
        logger.info(result.stdout)
        if result.stderr:
            logger.warning(f"⚠️  Warnings/Errors: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        logger.error(f"❌ Failed to run {test_file}: {e}")
        return False


def main():
    """Run all tests"""
    logger = get_logger(__name__)
    logger.info("🚀 Starting Test Suite...")

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
                logger.info(f"✅ {test_file} passed\n")
            else:
                logger.error(f"❌ {test_file} failed\n")
        else:
            logger.warning(f"⚠️  {test_file} not found\n")

    logger.info(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
