#!/usr/bin/env python3
"""
Test runner script for ServiceNow MCP unittest suite.

This script runs all tests with coverage reporting for SonarQube integration.
It also provides convenient commands for different test scenarios.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def run_all_tests():
    """Run all tests with coverage reporting and JUnit XML output."""
    print("ServiceNow MCP Server Test Suite")
    print("=" * 50)
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    success = True
    
    # 1. Run tests with pytest, coverage, and JUnit XML output
    if not run_command(
        "python -m pytest tests/ --cov=. --cov-report=xml --cov-report=term --cov-report=html --junit-xml=test-results.xml -v",
        "Running all tests with coverage and JUnit XML output"
    ):
        success = False
    
    # 2. Generate coverage report (if pytest-cov didn't already)
    if not run_command(
        "python -m coverage report",
        "Generating coverage report"
    ):
        success = False
    
    return success


def run_specific_test_module(module_name):
    """Run a specific test module."""
    command = f"python -m pytest tests/{module_name}.py -v --junit-xml=test-results-{module_name}.xml"
    return run_command(command, f"Running {module_name}")


def run_integration_tests_only():
    """Run only integration tests."""
    command = "python -m pytest tests/test_integration.py -v --junit-xml=test-results-integration.xml"
    return run_command(command, "Running integration tests")


def run_unit_tests_only():
    """Run all unit tests except integration tests."""
    command = "python -m pytest tests/ --ignore=tests/test_integration.py -v --junit-xml=test-results-unit.xml"
    return run_command(command, "Running unit tests")


def check_test_environment():
    """Check if test environment is properly set up."""
    print("Checking test environment setup...")
    
    # Check if coverage is installed
    try:
        import coverage
        print("[OK] Coverage package is available")
    except ImportError:
        print("✗ Coverage package not found. Install with: pip install coverage[toml]")
        return False
    
    # Check if pytest is installed
    try:
        import pytest
        print("[OK] pytest package is available")
    except ImportError:
        print("✗ pytest package not found. Install with: pip install pytest pytest-cov")
        return False
    
    # Check if unittest module is available (should always be available)
    try:
        import unittest
        print("[OK] unittest module is available") 
    except ImportError:
        print("✗ unittest module not found (this should not happen)")
        return False
    
    # Check if project modules are importable
    test_imports = [
        "query_validation",
        "Table_Tools.generic_table_tools"
    ]
    
    for module in test_imports:
        try:
            __import__(module)
            print(f"[OK] {module} is importable")
        except ImportError as e:
            print(f"⚠ {module} import warning: {e}")
    
    print("Environment check completed.")
    return True


def show_coverage_results():
    """Show coverage results if available."""
    if os.path.exists("coverage.xml"):
        print("\n" + "="*60)
        print("COVERAGE RESULTS SUMMARY")
        print("="*60)
        run_command("python -m coverage report --show-missing", "Detailed coverage report")
        
        if os.path.exists("htmlcov/index.html"):
            print(f"\nHTML coverage report available at: file://{os.path.abspath('htmlcov/index.html')}")
        
        if os.path.exists("coverage.xml"):
            print(f"XML coverage report for SonarQube: {os.path.abspath('coverage.xml')}")
        
        if os.path.exists("test-results.xml"):
            print(f"JUnit XML test results for SonarQube: {os.path.abspath('test-results.xml')}")
    else:
        print("No coverage results found. Run tests with coverage first.")


def main():
    """Main test runner function."""
    if len(sys.argv) < 2:
        print("ServiceNow MCP Test Runner")
        print("\nUsage:")
        print("  python tests/run_tests.py [command]")
        print("\nCommands:")
        print("  all              - Run all tests with coverage")
        print("  unit             - Run unit tests only")
        print("  integration      - Run integration tests only")
        print("  specific <name>  - Run specific test module")
        print("  check            - Check test environment setup")
        print("  coverage         - Show coverage results")
        print("\nExamples:")
        print("  python tests/run_tests.py all")
        print("  python tests/run_tests.py specific test_oauth")
        print("  python tests/run_tests.py coverage")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "check":
        success = check_test_environment()
    elif command == "all":
        success = run_all_tests()
        show_coverage_results()
    elif command == "unit":
        success = run_unit_tests_only()
    elif command == "integration":
        success = run_integration_tests_only()
    elif command == "specific" and len(sys.argv) > 2:
        test_module = sys.argv[2]
        success = run_specific_test_module(test_module)
    elif command == "coverage":
        show_coverage_results()
        success = True
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    if success:
        print(f"\n[SUCCESS] Test command '{command}' completed successfully!")
        sys.exit(0)
    else:
        print(f"\n[FAILED] Test command '{command}' failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()