# ServiceNow OAuth 2.0 Setup Guide

This guide will walk you through setting up OAuth 2.0 Client Credentials authentication for your ServiceNow MCP integration, replacing the less secure username/password authentication.

## Benefits of OAuth 2.0

- **Enhanced Security**: No stored passwords, token-based authentication
- **Automatic Token Management**: Automatic token refresh and expiration handling
- **Better Audit Trail**: OAuth provides better logging and monitoring capabilities
- **Principle of Least Privilege**: Scoped access permissions
- **Industry Standard**: Widely adopted secure authentication protocol

## Prerequisites

- ServiceNow instance with Washington DC release or later (for inbound client credentials)
- Admin access to your ServiceNow instance
- Python environment with required dependencies

## Part 1: ServiceNow Configuration

### Step 1: Enable Client Credentials Grant Type

1. Navigate to **System Properties > Security**
2. Find and set: `glide.oauth.inbound.client.credential.grant_type.enabled = true`
3. This enables the Client Credentials flow for inbound authentication

### Step 2: Create OAuth Application Registry

1. Navigate to **System OAuth > Application Registry**
2. Click **New**
3. Select **"Create an OAuth API endpoint for external clients"**
4. Fill in the form:
   - **Name**: `MCP ServiceNow Integration` (or your preferred name)
   - **Client ID**: Will be auto-generated (copy this for later)
   - **Client Secret**: Will be auto-generated (copy this for later)
   - **Accessible from**: Select appropriate option (usually "All application scopes")
   - **Active**: ✓ Checked
   - **Public Client**: ❌ Leave unchecked (RFC 6749 requires confidential clients for client credentials flow)

5. **Save** the record

### Step 3: Configure OAuth Application User

1. Create a dedicated ServiceNow user account:
   - Navigate to **User Administration > Users**
   - Click **New**
   - Create user with appropriate permissions for your integration needs
   - Ensure the user is **Active** and **not locked out**
   - Assign necessary roles (e.g., `rest_api_explorer`, custom roles)

2. Return to your OAuth Application Registry record
3. Set **OAuth Application User** to the user you just created
4. **Save** the record

### Step 4: Configure Authorization Scopes (Optional)

1. In the OAuth Application Registry record
2. Navigate to **OAuth Entity Scopes** related list
3. Add appropriate scopes or use default `useraccount` scope
4. The `useraccount` scope provides full permissions of the assigned user

## Part 2: Application Configuration

### Step 1: Update Environment Variables

Create or update your `.env` file with OAuth credentials:

```env
# ServiceNow Instance Configuration
SERVICENOW_INSTANCE=https://your-instance.service-now.com

# OAuth 2.0 Configuration (NEW - Primary)
SERVICENOW_CLIENT_ID=your_client_id_from_step2
SERVICENOW_CLIENT_SECRET=your_client_secret_from_step2

# Basic Auth Configuration (Fallback - Optional)
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password
```

### Step 2: Install Additional Dependencies

The OAuth implementation requires base64 encoding support (included in Python standard library).

No additional package installations are required beyond existing dependencies.

### Step 3: Verify Configuration

The application will automatically:
1. **Prefer OAuth**: Use OAuth 2.0 if `SERVICENOW_CLIENT_ID` and `SERVICENOW_CLIENT_SECRET` are set
2. **Fallback to Basic Auth**: Use username/password if OAuth credentials are missing
3. **Automatic Token Management**: Handle token expiration and refresh automatically

## Part 3: Testing Your Setup

### Step 1: Test OAuth Connection

Use the new OAuth testing tools:

```python
# Test OAuth connection
await nowtestoauth()

# Get authentication info  
await nowauthinfo()
```

Expected successful response:
```json
{
    "status": "success",
    "message": "OAuth authentication successful", 
    "token_valid": true,
    "expires_at": "2025-01-15T10:30:00"
}
```

### Step 2: Test API Functionality

Run your existing tools to verify they work with OAuth:

```python
# These should now use OAuth automatically
await nowtest()
await nowtestauth() 
await similarincidentsfortext("test query")
```

### Step 3: Monitor Token Usage

The OAuth client automatically:
- **Caches tokens** until 5 minutes before expiration
- **Refreshes tokens** automatically when needed
- **Handles 401 errors** by requesting new tokens
- **Falls back** to basic auth if OAuth fails

## Part 4: Security Considerations

### Environment Variables Security

- **Never commit** `.env` files to version control
- Use **secure secret management** in production environments
- Consider using **Azure Key Vault**, **AWS Secrets Manager**, or similar

### ServiceNow User Permissions

- Create a **dedicated service account** for OAuth integration
- Apply **principle of least privilege** - only grant necessary roles
- **Regularly audit** the OAuth application user's permissions
- **Monitor access logs** for unusual activity

### Token Security

- Tokens are **stored in memory only** (not persisted to disk)
- **Automatic expiration** prevents long-lived token exposure  
- **Bearer tokens** are transmitted securely over HTTPS only

## Part 5: Troubleshooting

### Common Issues

#### "Unsupported OAuth grant type 'Client Credentials'"
- **Solution**: Ensure your ServiceNow instance is Washington DC or later
- **Check**: `glide.oauth.inbound.client.credential.grant_type.enabled` property is set to `true`

#### "Invalid client credentials" 
- **Solution**: Verify `SERVICENOW_CLIENT_ID` and `SERVICENOW_CLIENT_SECRET` match your OAuth Application Registry
- **Check**: OAuth Application Registry record is **Active**

#### "Access denied" or "Insufficient privileges"
- **Solution**: Check OAuth Application User has necessary roles/permissions
- **Verify**: User account is active and not locked out

#### OAuth falls back to Basic Auth
- **Check**: Environment variables are properly set
- **Verify**: No typos in `SERVICENOW_CLIENT_ID` or `SERVICENOW_CLIENT_SECRET`
- **Test**: Use `await nowauthinfo()` to verify OAuth configuration

### Debug Information

Use the `nowauthinfo()` tool to get current authentication status:

```json
{
    "oauth_enabled": true,
    "basic_auth_available": true, 
    "instance_url": "https://your-instance.service-now.com",
    "auth_method": "oauth"
}
```

## Part 6: Production Deployment

### Environment-Specific Configuration

Create separate OAuth Application Registry records for:
- **Development** environment
- **Testing** environment  
- **Production** environment

### Monitoring and Maintenance

- **Monitor token usage** and refresh patterns
- **Set up alerts** for authentication failures
- **Regularly rotate** client secrets (ServiceNow best practice)
- **Review and update** OAuth application user permissions

### Backup Authentication

The implementation maintains Basic Auth as fallback:
- OAuth credentials invalid → Falls back to username/password
- Useful during OAuth setup/debugging phase
- Remove Basic Auth credentials once OAuth is confirmed working

## Advanced Configuration

### Custom Token Endpoint

If using a custom token endpoint, modify `oauth_client.py`:

```python
self.token_endpoint = f"{self.instance_url}/your_custom_oauth_token.do"
```

### Extended Token Lifetime

ServiceNow OAuth tokens typically last 30 minutes. For longer sessions, the client automatically refreshes tokens as needed.

### Custom Scopes

Add specific OAuth scopes in ServiceNow OAuth Entity Scopes for more granular permissions than the default `useraccount` scope.

## Migration Timeline

1. **Week 1**: Set up OAuth in ServiceNow and test in development
2. **Week 2**: Deploy OAuth configuration to testing environment  
3. **Week 3**: Validate all functionality with OAuth in testing
4. **Week 4**: Deploy to production and remove Basic Auth fallback

This gradual approach ensures zero downtime during the security upgrade.