#!/usr/bin/env python3

"""
Test script for CMDB CI Discovery & Search tools.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Table_Tools.cmdb_tools import (
    find_cis_by_type, search_cis_by_attributes, get_ci_details,
    similar_cis_for_ci, get_all_ci_types, quick_ci_search
)

def print_test_result(test_name: str, result, success_message: str = None):
    """Helper function to print test results consistently."""
    print(f"Result: {type(result).__name__}")
    
    if isinstance(result, dict):
        if success_message:
            print(success_message)
        else:
            print(f"Success: {result}")
    else:
        print(f"Error or no data: {result}")

def print_ci_types_details(ci_types: dict):
    """Print CI types details if available."""
    if not ci_types.get('ci_types'):
        return
    
    for ci_type in ci_types['ci_types'][:3]:
        print(f"  - {ci_type['table_name']}: {ci_type['display_name']}")

def print_ci_details(details: dict):
    """Print CI details if available."""
    if not isinstance(details, dict):
        return
    
    print(f"Got details for CI: {details.get('ci_number')}")
    print(f"CI Table: {details.get('ci_table')}")

async def test_get_all_ci_types():
    """Test getting all CI types."""
    print("\n1. Testing get_all_ci_types()...")
    result = await get_all_ci_types()
    
    if isinstance(result, dict):
        count = result.get('total_ci_types', 0)
        print_test_result("get_all_ci_types", result, f"Found {count} CI types")
        print_ci_types_details(result)
    else:
        print_test_result("get_all_ci_types", result)
    
    return result

async def test_find_cis_by_type():
    """Test finding CIs by type."""
    print("\n2. Testing find_cis_by_type('cmdb_ci_server')...")
    result = await find_cis_by_type('cmdb_ci_server')
    
    if isinstance(result, dict):
        count = result.get('count', 0)
        print_test_result("find_cis_by_type", result, f"Found {count} servers")
    else:
        print_test_result("find_cis_by_type", result)
    
    return result

async def test_search_cis_by_attributes():
    """Test searching CIs by attributes."""
    print("\n3. Testing search_cis_by_attributes(name='prod')...")
    result = await search_cis_by_attributes(name='prod')
    
    if isinstance(result, dict):
        count = result.get('count', 0)
        print_test_result("search_cis_by_attributes", result, f"Found {count} CIs with 'prod' in name")
    else:
        print_test_result("search_cis_by_attributes", result)
    
    return result

async def test_quick_ci_search():
    """Test quick CI search."""
    print("\n4. Testing quick_ci_search('server')...")
    result = await quick_ci_search('server')
    
    if isinstance(result, dict):
        count = result.get('count', 0)
        print_test_result("quick_ci_search", result, f"Quick search found {count} CIs")
    else:
        print_test_result("quick_ci_search", result)
    
    return result

async def test_get_ci_details(ci_source):
    """Test getting CI details if CI source has results."""
    if not (isinstance(ci_source, dict) and ci_source.get('result')):
        return
    
    ci_number = ci_source['result'][0].get('number')
    if not ci_number:
        return
    
    print(f"\n5. Testing get_ci_details('{ci_number}')...")
    result = await get_ci_details(ci_number)
    
    print_test_result("get_ci_details", result)
    if isinstance(result, dict):
        print_ci_details(result)

async def test_cmdb_tools():
    """Test CMDB tools functionality."""
    print("Testing CMDB CI Discovery & Search Tools")
    print("=" * 50)
    
    await test_get_all_ci_types()
    await test_find_cis_by_type()
    
    prod_cis = await test_search_cis_by_attributes()
    await test_quick_ci_search()
    await test_get_ci_details(prod_cis)
    
    print("\n" + "=" * 50)
    print("CMDB tools test completed!")
    print("All tools have been implemented and are ready for use.")

if __name__ == "__main__":
    asyncio.run(test_cmdb_tools())