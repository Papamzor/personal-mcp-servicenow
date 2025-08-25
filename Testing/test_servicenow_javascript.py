#!/usr/bin/env python3
"""
Test script to verify ServiceNow JavaScript function support in date filtering.
Tests the exact query format used by Claude Desktop.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from Table_Tools.incident_tools import getIncidentsByFilter, IncidentFilterParams

async def test_servicenow_javascript():
    """Test ServiceNow JavaScript function filtering"""
    
    print("Testing ServiceNow JavaScript Functions")
    print("=" * 50)
    
    # Test the exact format Claude Desktop is using
    print("\nTest 1: Claude Desktop format - javascript:gs.daysAgoStart(14)")
    params = IncidentFilterParams(
        fields=["number", "sys_created_on", "short_description", "state"],
        filters={
            "sys_created_on": ">=javascript:gs.daysAgoStart(14)"
        }
    )
    
    try:
        result = await getIncidentsByFilter(params)
        
        if isinstance(result, dict) and result.get('result'):
            count = len(result['result'])
            print(f"   SUCCESS: Found {count} incident(s) from last 14 days")
            
            # Show first few results
            for idx, incident in enumerate(result['result'][:3]):
                created_on = incident.get('sys_created_on', 'Unknown')
                number = incident.get('number', 'Unknown')
                desc = incident.get('short_description', 'No description')[:50]
                print(f"      {idx+1}. {number} - {desc}... (Created: {created_on})")
                
        elif isinstance(result, str):
            print(f"   ERROR: {result}")
        else:
            print(f"   WARNING: Unexpected result type: {type(result)}")
            
    except Exception as e:
        print(f"   EXCEPTION: {str(e)}")
    
    # Test other ServiceNow JavaScript functions
    print("\nTest 2: Other JavaScript functions")
    
    js_functions = [
        (">=javascript:gs.daysAgoStart(7)", "Last 7 days"),
        (">=javascript:gs.daysAgoStart(1)", "Last 24 hours"),
        (">=javascript:gs.monthsAgoStart(1)", "Last month"),
        (">=javascript:gs.weeksAgoStart(2)", "Last 2 weeks")
    ]
    
    for js_func, description in js_functions:
        print(f"\nTesting: {description} ({js_func})")
        
        params = IncidentFilterParams(
            fields=["number", "sys_created_on", "short_description"],
            filters={
                "sys_created_on": js_func
            }
        )
        
        try:
            result = await getIncidentsByFilter(params)
            
            if isinstance(result, dict) and result.get('result'):
                count = len(result['result'])
                print(f"   SUCCESS: Found {count} incident(s)")
            else:
                print(f"   ERROR: {result}")
                
        except Exception as e:
            print(f"   EXCEPTION: {str(e)}")
    
    print("\n" + "=" * 50)
    print("ServiceNow JavaScript function tests completed!")
    print("\nSupported JavaScript functions:")
    print("   - gs.daysAgoStart(N) - N days ago start of day")
    print("   - gs.daysAgoEnd(N) - N days ago end of day") 
    print("   - gs.weeksAgoStart(N) - N weeks ago start of week")
    print("   - gs.monthsAgoStart(N) - N months ago start of month")
    print("   - gs.yearsAgoStart(N) - N years ago start of year")

if __name__ == "__main__":
    try:
        asyncio.run(test_servicenow_javascript())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")