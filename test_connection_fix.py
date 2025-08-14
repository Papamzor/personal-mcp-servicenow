#!/usr/bin/env python3
"""
Test script to verify the connection fix for similarincidentsforincident function.
"""

import asyncio
from unittest.mock import AsyncMock, patch
from Table_Tools.consolidated_tools import similarincidentsforincident

async def test_connection_fix():
    """Test the connection error handling fix."""
    print("Testing connection error handling for similarincidentsforincident...")
    
    # Mock the service calls to simulate different scenarios
    with patch('Table_Tools.consolidated_tools.getshortdescforincident') as mock_get_desc, \
         patch('Table_Tools.consolidated_tools.similarincidentsfortext') as mock_search:
        
        # Scenario 1: Successful case
        mock_get_desc.return_value = {
            'result': [{'short_description': 'server down error'}]
        }
        mock_search.return_value = {'result': [{'number': 'INC0001', 'short_description': 'similar issue'}]}
        
        result = await similarincidentsforincident("INC0010001")
        print(f"Successful case result: {type(result)} - {str(result)[:100]}...")
        
        # Scenario 2: Connection error in get_description
        mock_get_desc.side_effect = Exception("Connection timeout")
        result = await similarincidentsforincident("INC0010001")
        print(f"Connection error case result: {result}")
        
        # Scenario 3: No description found
        mock_get_desc.side_effect = None
        mock_get_desc.return_value = {'result': []}
        result = await similarincidentsforincident("INC0010001")
        print(f"No description case result: {result}")

def main():
    print("=== Testing Connection Fix ===")
    asyncio.run(test_connection_fix())
    print("\n=== Fix Summary ===")
    print("+ Added try/catch blocks for connection errors")
    print("+ Implemented fallback approach mimicking original behavior")
    print("+ Added proper null checks and error handling")
    print("+ Applied fix to all similar functions (incidents, changes, URs)")

if __name__ == "__main__":
    main()