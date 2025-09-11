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
    """Run all tests with coverage reporting."""
    print("ServiceNow MCP Server Test Suite")
    print("=" * 50)
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    success = True
    
    # 1. Run tests with coverage
    if not run_command(
        "python -m coverage run -m unittest discover -s tests -p 'test_*.py' -v",
        "Running all tests with coverage"
    ):
        success = False
    
    # 2. Generate coverage report
    if not run_command(
        "python -m coverage report",
        "Generating coverage report"
    ):
        success = False
    
    # 3. Generate XML report for SonarQube
    if not run_command(
        "python -m coverage xml -o coverage.xml",
        "Generating XML coverage report for SonarQube"
    ):
        success = False
    
    # 4. Generate HTML report for local viewing
    if not run_command(
        "python -m coverage html",
        "Generating HTML coverage report"
    ):
        success = False
    
    return success


def run_specific_test_module(module_name):
    """Run a specific test module."""
    command = f"python -m unittest tests.{module_name} -v"
    return run_command(command, f"Running {module_name}")


def run_integration_tests_only():
    """Run only integration tests."""
    return run_specific_test_module("test_integration")


def run_unit_tests_only():
    """Run all unit tests except integration tests."""
    test_modules = [
        "test_oauth",
        "test_filtering", 
        "test_cmdb_tools",
        "test_mcp_tools"
    ]
    
    success = True
    for module in test_modules:
        if not run_specific_test_module(module):
            success = False
    
    return success


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
            print(f"[WARNING] {module} import warning: {e}")
    
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
        print(f"\n[OK] Test command '{command}' completed successfully!")
        sys.exit(0)
    else:
        print(f"\n✗ Test command '{command}' failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()