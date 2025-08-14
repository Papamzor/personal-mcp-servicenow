#!/usr/bin/env python3
"""
Test script for OAuth 2.0 implementation.
This script tests OAuth functionality without making actual ServiceNow API calls.
"""

import asyncio
import os
from unittest.mock import patch, AsyncMock
from oauth_client import ServiceNowOAuthClient
from service_now_api_oauth import test_oauth_connection, get_auth_info

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
        print("   Set these in your .env file for OAuth to work")
        return False
    else:
        print("All OAuth environment variables are configured")
        return True

async def test_oauth_client_creation():
    """Test OAuth client creation and configuration."""
    print("\n=== Testing OAuth Client Creation ===")
    
    try:
        # Test with mock environment variables
        with patch.dict(os.environ, {
            'SERVICENOW_INSTANCE': 'https://test.service-now.com',
            'SERVICENOW_CLIENT_ID': 'test_client_id',
            'SERVICENOW_CLIENT_SECRET': 'test_client_secret'
        }):
            client = ServiceNowOAuthClient()
            print("OAuth client created successfully")
            print(f"   Token endpoint: {client.token_endpoint}")
            return True
    except Exception as e:
        print(f"Failed to create OAuth client: {str(e)}")
        return False

async def test_token_request_format():
    """Test token request formatting."""
    print("\n=== Testing Token Request Format ===")
    
    try:
        with patch.dict(os.environ, {
            'SERVICENOW_INSTANCE': 'https://test.service-now.com',
            'SERVICENOW_CLIENT_ID': 'test_client_id',
            'SERVICENOW_CLIENT_SECRET': 'test_client_secret'
        }):
            client = ServiceNowOAuthClient()
            
            # Test Basic Auth header generation
            auth_header = client._get_basic_auth_header()
            print(f"✅ Basic Auth header format: {auth_header[:20]}...")
            
            # Verify it starts with "Basic "
            if auth_header.startswith("Basic "):
                print("✅ Auth header format is correct")
                return True
            else:
                print("❌ Auth header format is incorrect")
                return False
    except Exception as e:
        print(f"❌ Token request format test failed: {str(e)}")
        return False

async def test_mock_token_flow():
    """Test OAuth flow with mocked HTTP requests."""
    print("\n=== Testing Mock OAuth Flow ===")
    
    try:
        with patch.dict(os.environ, {
            'SERVICENOW_INSTANCE': 'https://test.service-now.com',
            'SERVICENOW_CLIENT_ID': 'test_client_id',
            'SERVICENOW_CLIENT_SECRET': 'test_client_secret'
        }):
            client = ServiceNowOAuthClient()
            
            # Mock successful token response
            mock_token_response = {
                "access_token": "mock_access_token_12345",
                "token_type": "Bearer",
                "expires_in": 1800,
                "scope": ""
            }
            
            # Mock the HTTP client
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = AsyncMock()
                mock_response.json.return_value = mock_token_response
                mock_response.raise_for_status.return_value = None
                
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                
                # Test token retrieval
                token = await client._get_valid_token()
                print(f"✅ Mock token retrieved: {token[:10]}...")
                
                # Test auth headers
                headers = await client.get_auth_headers()
                print(f"✅ Auth headers generated: {headers['Authorization'][:20]}...")
                
                return True
    except Exception as e:
        print(f"❌ Mock OAuth flow test failed: {str(e)}")
        return False

async def test_api_client_selection():
    """Test API client authentication method selection."""
    print("\n=== Testing API Client Selection ===")
    
    try:
        # Test OAuth configuration detection
        with patch.dict(os.environ, {
            'SERVICENOW_CLIENT_ID': 'test_client_id',
            'SERVICENOW_CLIENT_SECRET': 'test_client_secret'
        }, clear=True):
            auth_info = await get_auth_info()
            print(f"✅ OAuth detection: {auth_info}")
            
            if auth_info['oauth_enabled']:
                print("✅ OAuth correctly detected as primary auth method")
            else:
                print("❌ OAuth not detected despite credentials being set")
                return False
        
        # Test basic auth fallback
        with patch.dict(os.environ, {
            'SERVICENOW_USERNAME': 'test_user',
            'SERVICENOW_PASSWORD': 'test_pass'
        }, clear=True):
            auth_info = await get_auth_info()
            print(f"✅ Basic auth fallback: {auth_info}")
            
            if not auth_info['oauth_enabled'] and auth_info['basic_auth_available']:
                print("✅ Basic auth fallback correctly detected")
            else:
                print("❌ Basic auth fallback not working correctly")
                return False
        
        return True
    except Exception as e:
        print(f"❌ API client selection test failed: {str(e)}")
        return False

async def run_all_tests():
    """Run all OAuth tests."""
    print("OAuth 2.0 Implementation Tests\n")
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("OAuth Client Creation", test_oauth_client_creation),
        ("Token Request Format", test_token_request_format),
        ("Mock OAuth Flow", test_mock_token_flow),
        ("API Client Selection", test_api_client_selection)
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
            print(f"❌ {test_name} failed with exception: {str(e)}")
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
        print("   1. Set up OAuth Application Registry in ServiceNow")
        print("   2. Configure environment variables with real credentials")
        print("   3. Test with: await nowtestoauth()")
    else:
        print(f"\n{len(results) - passed} tests failed. Please review the implementation.")

if __name__ == "__main__":
    asyncio.run(run_all_tests())