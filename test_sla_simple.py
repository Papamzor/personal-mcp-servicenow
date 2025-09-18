#!/usr/bin/env python3
"""
Simple test script for SLA functionality in the MCP server.
"""

import asyncio
import sys
import os
import traceback

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import SLA functions
from Table_Tools.consolidated_tools import (
    get_active_slas,
    get_slas_by_stage,
    get_breaching_slas
)

async def test_sla_functions():
    """Test basic SLA functions."""

    print("Testing SLA Functions")
    print("=" * 50)

    # Test 1: Get active SLAs
    try:
        print("\nTest 1: Get Active SLAs")
        result = await get_active_slas()
        if isinstance(result, dict) and "records" in result:
            count = len(result.get("records", []))
            print(f"SUCCESS: Found {count} active SLA records")
        else:
            print(f"WARNING: Unexpected response format: {result}")
    except Exception as e:
        print(f"ERROR: Testing active SLAs failed: {str(e)}")

    # Test 2: Get breaching SLAs
    try:
        print("\nTest 2: Get SLAs at Risk of Breaching")
        result = await get_breaching_slas(60)
        if isinstance(result, dict) and "records" in result:
            count = len(result.get("records", []))
            print(f"SUCCESS: Found {count} SLAs at risk of breaching")
        else:
            print(f"WARNING: Unexpected response format: {result}")
    except Exception as e:
        print(f"ERROR: Testing breaching SLAs failed: {str(e)}")

    # Test 3: Get SLAs by stage
    try:
        print("\nTest 3: Get SLAs by Stage")
        result = await get_slas_by_stage("In Progress")
        if isinstance(result, dict) and "records" in result:
            count = len(result.get("records", []))
            print(f"SUCCESS: Found {count} SLAs in 'In Progress' stage")
        else:
            print(f"WARNING: Unexpected response format: {result}")
    except Exception as e:
        print(f"ERROR: Testing SLAs by stage failed: {str(e)}")

    print("\n" + "=" * 50)
    print("SLA Function Testing Complete")

if __name__ == "__main__":
    print("Starting SLA functionality test...")
    try:
        asyncio.run(test_sla_functions())
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        traceback.print_exc()
    finally:
        print("Test script finished")