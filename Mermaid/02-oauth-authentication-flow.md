# OAuth 2.0 Authentication Flow

This sequence diagram illustrates how the MCP server handles OAuth 2.0 Client Credentials authentication with ServiceNow, including automatic token management and refresh.

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as MCP Server
    participant OAuth as oauth_client.py
    participant SN as ServiceNow API
    
    Client->>Server: Tool Request
    Server->>OAuth: Check Token Status
    
    alt Token Valid
        OAuth->>Server: Return Cached Token
    else Token Expired/Missing
        OAuth->>SN: POST /oauth_token.do
        Note over OAuth,SN: Client Credentials Flow<br/>grant_type=client_credentials<br/>client_id + client_secret
        SN->>OAuth: Access Token + Expires
        OAuth->>OAuth: Cache Token & Expiry
        OAuth->>Server: Return New Token
    end
    
    Server->>SN: API Request with Bearer Token
    alt Success
        SN->>Server: Response Data
        Server->>Client: Processed Results
    else Auth Error
        SN->>Server: 401 Unauthorized
        Server->>OAuth: Force Token Refresh
        OAuth->>SN: POST /oauth_token.do
        SN->>OAuth: New Access Token
        Server->>SN: Retry API Request
        SN->>Server: Response Data
        Server->>Client: Processed Results
    end
```

## Authentication Features

- **Client Credentials Flow**: Secure machine-to-machine authentication
- **Automatic Token Management**: Tokens cached until near expiry
- **Thread-Safe Operations**: Async locks prevent concurrent token requests
- **Error Recovery**: Automatic retry on authentication failures
- **Environment Configuration**: Credentials loaded from `.env` file

## Security Benefits

- No hardcoded credentials in source code
- Tokens automatically expire and refresh
- Bearer token authentication (more secure than Basic Auth)
- Encrypted HTTPS communication with ServiceNow