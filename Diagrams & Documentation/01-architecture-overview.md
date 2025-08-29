# MCP Server Architecture Overview

This diagram shows the high-level architecture of the Personal MCP ServiceNow server, illustrating how components interact from the MCP client down to the ServiceNow API.

```mermaid
graph TB
    subgraph "MCP Client"
        A[Claude/Client] --> B[MCP Protocol]
    end
    
    subgraph "MCP Server Core"
        B --> C[tools.py - FastMCP Server]
        C --> D[Tool Registration]
    end
    
    subgraph "Tool Categories"
        D --> E[Utility Tools]
        D --> F[Incident Tools]
        D --> G[Change Tools]
        D --> H[User Request Tools]
        D --> I[Knowledge Tools]
        D --> J[CMDB Tools]
        D --> K[Private Task Tools]
    end
    
    subgraph "Core Components"
        E --> L[utility_tools.py]
        F --> M[consolidated_tools.py]
        G --> M
        H --> M
        I --> M
        J --> M
        K --> M
        M --> N[generic_table_tools.py]
    end
    
    subgraph "ServiceNow Integration"
        N --> O[service_now_api_oauth.py]
        L --> O
        O --> P[oauth_client.py]
        P --> Q[ServiceNow Instance]
    end
    
    subgraph "Support Modules"
        N --> R[utils.py - Text Processing]
        R --> S[spaCy NLP Engine]
    end
```

## Key Components

- **MCP Client**: External clients (like Claude) communicating via MCP protocol
- **FastMCP Server**: Core server handling tool registration and routing
- **Tool Categories**: 25+ tools organized by ServiceNow table type (snake_case compliant)
- **Generic Layer**: Reusable functions to minimize code duplication
- **OAuth 2.0 Only**: Exclusive OAuth authentication with automatic token management
- **NLP Processing**: spaCy-powered text analysis for similarity matching

## Code Quality Features

- **SonarCloud Compliant**: All cognitive complexity violations resolved (≤15 limit)
- **PEP 8 Standards**: Complete snake_case naming convention adherence
- **Modular Architecture**: Helper functions improve maintainability and testability
- **Low Complexity**: API functions refactored from complexity 20 to ≤8
- **Enhanced Readability**: Single responsibility principle applied throughout