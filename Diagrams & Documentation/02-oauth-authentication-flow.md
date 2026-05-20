# OAuth 2.0 Authentication Flow

This sequence diagram illustrates how the MCP server handles OAuth 2.0 Client Credentials authentication with ServiceNow, including automatic token management and refresh.

> **v4.0 update**: the v3 `oauth_client.py` class was split into `oauth/token_store.py` + `oauth/request_executor.py` composed by a façade at `oauth/client.py`. The `oauth_client.py` shim retains the module-level singleton (`get_oauth_client`, `make_oauth_request`) for backwards compat. Sequence below collapses the subsystems under the façade for readability — see `01-architecture-overview.md` for the layered view.

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as MCP Server
    participant OAuth as oauth/client.py (façade)
    participant Store as oauth/token_store.py
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