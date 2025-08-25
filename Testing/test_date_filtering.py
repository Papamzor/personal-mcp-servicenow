#!/usr/bin/env python3
"""
Test script to verify date filtering functionality in ServiceNow MCP server.
Run this script to test various date filter scenarios.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from Table_Tools.incident_tools import getIncidentsByFilter, IncidentFilterParams

async def test_date_filtering():
    """Test various date filtering scenarios"""
    
    print("Testing ServiceNow Date Filtering")
    print("=" * 50)
    
    # Test cases for date filtering
    test_cases = [
        {
            "name": "Incidents created today",
            "filters": {
                "sys_created_on_gte": datetime.now().strftime("%Y-%m-%d")
            }
        },
        {
            "name": "Incidents created in last 7 days", 
            "filters": {
                "sys_created_on_gte": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            }
        },
        {
            "name": "Incidents created in last 30 days",
            "filters": {
                "sys_created_on_gte": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            }
        },
        {
            "name": "Incidents created between dates",
            "filters": {
                "sys_created_on_gte": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "sys_created_on_lte": datetime.now().strftime("%Y-%m-%d")
            }
        },
        {
            "name": "High priority incidents from last week",
            "filters": {
                "priority": "1",
                "sys_created_on_gte": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"   Filters: {test_case['filters']}")
        
        try:
            # Create parameters
            params = IncidentFilterParams(
                filters=test_case['filters'],
                fields=["number", "short_description", "sys_created_on", "priority", "state"]
            )
            
            # Execute the test
            result = await getIncidentsByFilter(params)
            
            # Analyze results
            if isinstance(result, dict) and result.get('result'):
                count = len(result['result'])
                print(f"   SUCCESS: Found {count} incident(s)")
                
                # Show first few results
                for idx, incident in enumerate(result['result'][:3]):
                    created_on = incident.get('sys_created_on', 'Unknown')
                    number = incident.get('number', 'Unknown')
                    desc = incident.get('short_description', 'No description')[:50]
                    print(f"      {idx+1}. {number} - {desc}... (Created: {created_on})")
                
                if count > 3:
                    print(f"      ... and {count - 3} more")
                    
            elif isinstance(result, str):
                print(f"   ERROR: {result}")
            else:
                print(f"   WARNING: Unexpected result type: {type(result)}")
                
        except Exception as e:
            print(f"   EXCEPTION: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Date filtering tests completed!")
    print("\nTips for using date filters:")
    print("   • Use format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")
    print("   • Supported suffixes: _gte, _lte, _gt, _lt")
    print("   • Example: sys_created_on_gte: '2024-01-01'")
    print("   • Combine with other filters like priority, state, etc.")

if __name__ == "__main__":
    try:
        asyncio.run(test_date_filtering())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")