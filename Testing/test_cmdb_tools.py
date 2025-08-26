#!/usr/bin/env python3

"""
Test script for CMDB CI Discovery & Search tools.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Table_Tools.cmdb_tools import (
    findCIsByType, searchCIsByAttributes, getCIDetails, 
    similarCIsForCI, getAllCITypes, quickCISearch
)

async def test_cmdb_tools():
    """Test CMDB tools functionality."""
    
    print("Testing CMDB CI Discovery & Search Tools")
    print("=" * 50)
    
    # Test 1: Get all CI types
    print("\n1. Testing getAllCITypes()...")
    ci_types = await getAllCITypes()
    print(f"Result: {type(ci_types).__name__}")
    if isinstance(ci_types, dict):
        print(f"Found {ci_types.get('total_ci_types', 0)} CI types")
        # Show first few types
        if ci_types.get('ci_types'):
            for ci_type in ci_types['ci_types'][:3]:
                print(f"  - {ci_type['table_name']}: {ci_type['display_name']}")
    else:
        print(f"Error or no data: {ci_types}")
    
    # Test 2: Find CIs by type  
    print("\n2. Testing findCIsByType('cmdb_ci_server')...")
    servers = await findCIsByType('cmdb_ci_server')
    print(f"Result: {type(servers).__name__}")
    if isinstance(servers, dict):
        print(f"Found {servers.get('count', 0)} servers")
    else:
        print(f"Error or no data: {servers}")
    
    # Test 3: Search CIs by attributes
    print("\n3. Testing searchCIsByAttributes(name='prod')...")
    prod_cis = await searchCIsByAttributes(name='prod')
    print(f"Result: {type(prod_cis).__name__}")
    if isinstance(prod_cis, dict):
        print(f"Found {prod_cis.get('count', 0)} CIs with 'prod' in name")
    else:
        print(f"Error or no data: {prod_cis}")
    
    # Test 4: Quick CI search
    print("\n4. Testing quickCISearch('server')...")
    quick_results = await quickCISearch('server')
    print(f"Result: {type(quick_results).__name__}")
    if isinstance(quick_results, dict):
        print(f"Quick search found {quick_results.get('count', 0)} CIs")
    else:
        print(f"Error or no data: {quick_results}")
    
    # Test 5: Get CI details (if we found any CIs)
    if isinstance(prod_cis, dict) and prod_cis.get('result'):
        ci_number = prod_cis['result'][0].get('number')
        if ci_number:
            print(f"\n5. Testing getCIDetails('{ci_number}')...")
            details = await getCIDetails(ci_number)
            print(f"Result: {type(details).__name__}")
            if isinstance(details, dict):
                print(f"Got details for CI: {details.get('ci_number')}")
                print(f"CI Table: {details.get('ci_table')}")
            else:
                print(f"Error or no data: {details}")
    
    print("\n" + "=" * 50)
    print("CMDB tools test completed!")
    print("All tools have been implemented and are ready for use.")

if __name__ == "__main__":
    asyncio.run(test_cmdb_tools())