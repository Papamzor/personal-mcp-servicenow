# MCP ServiceNow Server - Architecture Documentation

This folder contains Mermaid diagrams documenting the architecture and workflows of the Personal MCP ServiceNow server.

## 📋 Diagram Index

| File | Description | Diagram Type |
|------|-------------|--------------|
| [01-architecture-overview.md](./01-architecture-overview.md) | High-level system architecture showing all major components | Component Diagram |
| [02-oauth-authentication-flow.md](./02-oauth-authentication-flow.md) | OAuth 2.0 authentication sequence with ServiceNow | Sequence Diagram |
| [03-tool-organization.md](./03-tool-organization.md) | Tool categorization and generic layer architecture | Graph Diagram |
| [04-similarity-search-flow.md](./04-similarity-search-flow.md) | NLP-powered similarity search workflow with optimizations | Flowchart |

## 🔧 How to View Diagrams

### VS Code (Recommended)
1. Install the **Mermaid Preview** extension
2. Open any `.md` file in this folder
3. Use `Ctrl+Shift+V` to preview with rendered diagrams

### GitHub
- Diagrams render automatically when viewing files on GitHub
- Click on any `.md` file to see the rendered Mermaid charts

### Mermaid Live Editor
1. Copy the mermaid code block from any file
2. Paste into [Mermaid Live Editor](https://mermaid.live/)
3. View, edit, and export as needed

## 📊 System Overview

The MCP ServiceNow server provides:

- **35+ Tools** across 7 ServiceNow table types
- **OAuth 2.0 Only Authentication** with automatic token management
- **NLP-Powered Search** using spaCy for keyword extraction
- **Performance Optimized** queries with minimal field selection
- **Generic Architecture** reducing code duplication by 80%

## 🏗️ Architecture Highlights

### Modular Design
- **Tool Layer**: Table-specific tools with consistent interfaces
- **Generic Layer**: Reusable functions for common operations
- **API Layer**: OAuth-secured ServiceNow integration
- **NLP Layer**: spaCy-powered text processing

### Performance Features
- Essential field selection (4-9 fields vs 50+ available)
- Keyword-based search with priority ordering
- Early exit on first match found
- OAuth token caching (1-hour expiry)
- Async/await for non-blocking operations

### Security
- OAuth 2.0 Client Credentials flow
- Environment-based configuration
- Automatic token refresh
- No hardcoded credentials

## 🔄 Typical Workflow

1. **Client Request** → MCP Protocol → FastMCP Server
2. **Authentication** → Check/refresh OAuth token
3. **Text Processing** → Extract keywords using NLP
4. **API Query** → Optimized ServiceNow REST calls
5. **Response** → Processed results back to client

## 📈 Supported Operations

- **Similarity Search**: Find related records using text analysis
- **Detail Retrieval**: Get comprehensive record information
- **Filtered Queries**: Advanced search with custom criteria
- **CRUD Operations**: Create, read, update for private tasks
- **CMDB Discovery**: Configuration item search and analysis

---

*Last Updated: January 2025*
*Project: Personal MCP ServiceNow Server*