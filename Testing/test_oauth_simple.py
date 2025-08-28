#!/usr/bin/env python3
"""
Simple test script for OAuth 2.0 implementation.
Tests OAuth functionality without making actual ServiceNow API calls.
"""

import asyncio
import os
from unittest.mock import patch, AsyncMock

def test_environment_setup():
    """Test that environment variables are properly configured."""
    print("=== Testing Environment Setup ===")
    
    required_vars = [
        "SERVICENOW_INSTANCE",
        "SERVICENOW_CLIENT_ID", 
        "SERVICENOW_CLIENT_SECRET"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Missing environment variables: {missing_vars}")
        print("Set these in your .env file for OAuth to work")
        return False
    else:
        print("All OAuth environment variables are configured")
        return True

def test_oauth_client_creation():
    """Test OAuth client creation and configuration."""
    print("\n=== Testing OAuth Client Creation ===")
    
    try:
        from oauth_client import ServiceNowOAuthClient
        
        # Test with mock environment variables
        with patch.dict(os.environ, {
            'SERVICENOW_INSTANCE': 'https://test.service-now.com',
            'SERVICENOW_CLIENT_ID': 'test_client_id',
            'SERVICENOW_CLIENT_SECRET': 'test_client_secret'
        }):
            client = ServiceNowOAuthClient()
            print("OAuth client created successfully")
            print(f"Token endpoint: {client.token_endpoint}")
            return True
    except Exception as e:
        print(f"Failed to create OAuth client: {str(e)}")
        return False

async def test_api_integration():
    """Test API client integration."""
    print("\n=== Testing API Integration ===")
    
    try:
        from service_now_api_oauth import get_auth_info
        
        # Test with OAuth config
        with patch.dict(os.environ, {
            'SERVICENOW_CLIENT_ID': 'test_client_id',
            'SERVICENOW_CLIENT_SECRET': 'test_client_secret',
            'SERVICENOW_INSTANCE': 'https://test.service-now.com'
        }):
            auth_info = await get_auth_info()
            print(f"OAuth enabled: {auth_info['oauth_enabled']}")
            print(f"Auth method: {auth_info['auth_method']}")
            
            if auth_info['oauth_enabled']:
                print("OAuth correctly detected as primary auth method")
                return True
            else:
                print("OAuth not detected despite credentials being set")
                return False
    except Exception as e:
        print(f"API integration test failed: {str(e)}")
        return False

async def run_tests():
    """Run all OAuth tests."""
    print("OAuth 2.0 Implementation Tests\n")
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("OAuth Client Creation", test_oauth_client_creation),
        ("API Integration", test_api_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("Test Results Summary")
    print(f"{'='*50}")
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n{passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\nAll OAuth tests passed! Your OAuth implementation is ready.")
        print("\nNext Steps:")
        print("1. Set up OAuth Application Registry in ServiceNow")
        print("2. Configure environment variables with real credentials")
        print("3. Test with: await nowtestoauth()")
    else:
        print(f"\n{len(results) - passed} tests failed. Please review the implementation.")

if __name__ == "__main__":
    asyncio.run(run_tests())