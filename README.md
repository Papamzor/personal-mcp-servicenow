# 🚀 Personal MCP ServiceNow Integration

A Model Context Protocol (MCP) server for ServiceNow integration, featuring **AI-powered natural language processing**, consolidated architecture, and **enterprise-grade security** across multiple ServiceNow tables with **zero functional regression**.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![ServiceNow](https://img.shields.io/badge/ServiceNow-REST%20API-green.svg)](https://servicenow.com)
[![OAuth 2.0](https://img.shields.io/badge/Auth-OAuth%202.0%20Only-orange.svg)](https://oauth.net/2/)
[![AI Powered](https://img.shields.io/badge/AI-Natural%20Language%20Processing-purple.svg)](#)
[![Security](https://img.shields.io/badge/Security-ReDoS%20Protected-red.svg)](#)

---

## 💖 Support This Project

If this ServiceNow MCP integration is valuable to your workflow, consider supporting its continued development:

[![PayPal](https://img.shields.io/badge/PayPal-Support%20Development-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.me/papamzor)

Your support helps maintain and improve this project with new features, bug fixes, and better documentation.

---

## Installation

### Option 1: Binary (Recommended)

Download the latest binary for your platform from [Releases](../../releases):

| Platform | Download |
|----------|----------|
| macOS (Apple Silicon) | `mcp-servicenow-darwin-arm64` |
| macOS (Intel) | `mcp-servicenow-darwin-x86_64` |
| Linux | `mcp-servicenow-linux-amd64` |
| Windows | `mcp-servicenow-windows-amd64.exe` |

**macOS/Linux Setup:**
```bash
# Download and install
chmod +x mcp-servicenow-darwin-arm64
sudo mv mcp-servicenow-darwin-arm64 /usr/local/bin/mcp-servicenow

# Run setup wizard
mcp-servicenow --setup

# Verify
mcp-servicenow --version
```

**Windows Setup:**
```powershell
# Move to a directory in your PATH
Move-Item mcp-servicenow-windows-amd64.exe C:\Users\$env:USERNAME\AppData\Local\bin\mcp-servicenow.exe

# Run setup wizard
mcp-servicenow.exe --setup
```

### Claude Code Configuration

Add to your Claude Code MCP configuration (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "servicenow": {
      "command": "/usr/local/bin/mcp-servicenow"
    }
  }
}
```

### Option 2: From Source

```bash
git clone <repo-url>
cd mcp-servicenow
pip install -r requirements.txt
python personal_mcp_servicenow_main.py
```

---

## 🆕 What's New in v3.0

**v3.0 is a quality-of-life and performance release** with no breaking API changes for end users.

| Change | Impact |
|--------|--------|
| **Tool consolidation** | 24 table-specific wrappers replaced by 5 generic tools (`search_records`, `get_record`, `get_record_summary`, `find_similar`, `filter_records`) — pass any supported table name as a parameter. Total tools reduced from 55 to 36. |
| **Faster API responses** | All requests now include `sysparm_exclude_reference_link=true` and `sysparm_no_count=true`, reducing payload size and eliminating unnecessary server-side COUNT queries. |
| **Deterministic pagination** | Paginated queries automatically sort by `sys_created_on DESC`, preventing records from being skipped or duplicated across pages. |
| **Centralized URL encoding** | `sysparm_query` values are percent-encoded in a single place, fixing edge cases where special characters caused silent over-fetching. |
| **Correct HTTP semantics** | Partial updates to private tasks now use `PATCH` instead of `PUT`. |

Upgrading from v2.x requires no configuration changes.

---

## 🚨 Version 2.0 - BREAKING CHANGES (from v1.x)

If you're upgrading from v1.x:

- 📖 **Read the Migration Guide**: [`MIGRATION_V2.md`](MIGRATION_V2.md) - Complete step-by-step migration instructions
- 📋 **Review Breaking Changes**: [`CHANGELOG.md`](CHANGELOG.md) - Full list of changes and new features
- 🔧 **OAuth 2.0 Required**: Basic authentication has been removed - OAuth setup is mandatory

**New Installations**: Start directly with v3.0 - follow the setup instructions below.

## ✨ Features

### 🧠 **AI-Powered Natural Language Processing (NEW)**

- **Conversational Queries** - "Show me high priority incidents from last week" automatically converted to ServiceNow syntax
- **Confidence Scoring** - 0.0-1.0 confidence ratings with intelligence metadata
- **Smart Templates** - Enterprise-grade pre-built filter patterns for common scenarios
- **Query Explanation** - Human-readable explanations and SQL equivalents for every query
- **Filter Intelligence** - Automatic validation, correction, and improvement suggestions

### 🛡️ **Enterprise-Grade Security (Enhanced)**

- **OAuth 2.0 Exclusive** - Enhanced security with no basic auth fallback
- **ReDoS Protection** - Windows-compatible protection against Regular Expression Denial of Service attacks
- **Input Validation** - Pre-validation of all text inputs to prevent malicious attacks
- **Attack Resistance** - Comprehensive protection against SQL injection, XSS, and path traversal
- **Security Monitoring** - Real-time validation with intelligent safety warnings

### 📦 **Consolidated Architecture (v3.0)**

- **55 → 36 tools** - 24 near-duplicate wrappers replaced by 5 generic parameterized tools
- **Unified Interface** - `search_records(table, query)` works across all 8 supported tables
- **Zero Regression** - Generic tools delegate to the same core engine and API path
- **Performance optimized** - All requests include performance params, centralized URL encoding, deterministic pagination
- **AI Integration** - Natural language processing seamlessly integrated throughout

### 🗄️ **Comprehensive Table Support (Enhanced)**

- **Incidents** - AI-enhanced similarity search, intelligent filtering, and priority queries
- **Change Requests** - Complete change management with natural language processing
- **User Requests** - Service catalog handling with smart filter generation
- **Knowledge Base** - Article search with AI-powered category intelligence
- **Private Tasks** - Full CRUD operations with intelligent validation
- **CMDB Configuration Items** - 100+ CI types with AI-enhanced discovery and search

### ⚡ **Performance Revolution (5x Improvement)**

- **5x Faster Processing** - Compiled regex patterns vs SpaCy NLP (47MB → <1MB)
- **Enhanced Field Selection** - Smart field optimization (60% data reduction)
- **Pagination Support** - Complete result retrieval preventing data loss
- **OAuth Token Caching** - 1-hour token reuse with automatic refresh
- **Early Exit Strategy** - Return first successful match for efficiency
- **Async Architecture** - Non-blocking operations with optimized concurrency

### 📊 **CMDB Discovery & Management (Enhanced)**

- **AI-Enhanced Discovery** - Intelligent CI type detection and categorization
- **100+ CI Type Support** - Servers, databases, applications, storage, networking, cloud resources
- **Multi-Attribute Search** - Natural language queries across name, IP, location, status
- **Relationship Analysis** - AI-powered similar CI detection and dependency mapping
- **Business Service Mapping** - Complete infrastructure-to-service relationships with intelligence

### 🏗️ **Code Quality & Architecture Excellence**

- **SonarCloud Compliance** - All cognitive complexity violations resolved (≤15 limit)
- **PEP 8 Standards** - Complete snake_case naming convention adherence
- **Modular Design** - Single responsibility principle applied throughout
- **Helper Functions** - Enhanced maintainability and testability
- **Constants Module** - Centralized configuration eliminating hardcoded values
- **Query Validation** - Built-in ServiceNow syntax validation with intelligent corrections

## 🛠️ Available Tools (36)

### **📦 Generic Table Tools (5) — NEW in v3.0**

These replace 24 table-specific wrappers. Pass any supported table: `incident`, `change_request`, `sc_req_item`, `sc_task`, `universal_request`, `kb_knowledge`, `vtb_task`, `task_sla`.

- `search_records(table, query)` - Text similarity search across any supported table
- `get_record_summary(table, number)` - Short description for a single record
- `get_record(table, number)` - Full detail fields for a single record
- `find_similar(table, number)` - Find records similar to an existing record
- `filter_records(table, filters, fields)` - Query with field-value filters, operators, and date ranges

### **🧠 Intelligent Query Tools (5)**

- `intelligent_search(query, table, context)` - Natural language search: "high priority incidents from last week"
- `build_smart_servicenow_filter(query, table, context)` - Convert natural language to ServiceNow syntax
- `explain_servicenow_filters(filters, table)` - Human-readable explanations of complex filters
- `get_servicenow_filter_templates()` - Pre-built filters for common scenarios
- `get_query_examples()` - Natural language examples that work with intelligent search

### **🔧 Server & Authentication (5)**

- `nowtest()` - Server connectivity verification
- `now_test_oauth()` - OAuth 2.0 authentication testing
- `now_auth_info()` - Current authentication method info
- `nowtestauth()` - ServiceNow API endpoint validation
- `nowtest_auth_input(table)` - Table description retrieval

### **🔥 Priority Incidents (1)**

- `get_priority_incidents(priorities, start_date, end_date, additional_filters, include_metadata)` - Priority queries with date range filtering and metadata

### **📚 Knowledge Base (3)**

- `similar_knowledge_for_text(input_text, kb_base, category)` - Article search with optional category/knowledge base filtering
- `get_knowledge_by_category(category, kb_base)` - Category-based article retrieval
- `get_active_knowledge_articles(input_text)` - Published knowledge articles

### **📝 Private Task CRUD (2)**

- `create_private_task(task_data)` - Create new private tasks (vtb_task)
- `update_private_task(task_number, update_data)` - Update existing tasks via PATCH

### **⏱️ SLA Management (10)**

- `similar_slas_for_text(input_text)` - SLA search by text
- `get_slas_for_task(task_number)` - All SLAs for a specific task
- `get_sla_details(sla_sys_id)` - Detailed SLA information
- `get_breaching_slas(time_threshold_minutes)` - SLAs at risk of breaching
- `get_breached_slas(filters, days)` - Already breached SLAs
- `get_slas_by_stage(stage, additional_filters)` - SLAs by stage
- `get_active_slas(filters)` - Currently active SLAs
- `get_sla_performance_summary(filters, days)` - SLA performance metrics
- `get_recent_breached_slas(days)` - Recently breached SLAs
- `get_critical_sla_status()` - High-priority SLA dashboard

### **🖥️ CMDB Configuration Items (6)**

- `find_cis_by_type(ci_type)` - Find CIs by type (100+ types supported)
- `search_cis_by_attributes(name, ip_address, location, status)` - Multi-attribute CI search
- `get_ci_details(ci_number)` - Comprehensive CI details
- `similar_cis_for_ci(ci_number)` - Find similar configuration items
- `get_all_ci_types()` - List all available CI types
- `quick_ci_search(search_term)` - Fast CI search by name, IP, or number

### **Supported CI Types** (Auto-Discovered)

```
Core Infrastructure    Cloud & Virtualization    Storage & Networking
├── cmdb_ci_server      ├── cmdb_ci_vm_object      ├── cmdb_ci_storage_device
├── cmdb_ci_database    ├── cmdb_ci_vpc            ├── cmdb_ci_san
├── cmdb_ci_hardware    ├── cmdb_ci_subnet         ├── cmdb_ci_ip_network
└── cmdb_ci_service     └── cmdb_ci_cloud_*        └── cmdb_ci_load_balancer

Applications           Facilities                  Specialized Equipment  
├── cmdb_ci_appl       ├── cmdb_ci_datacenter     ├── cmdb_ci_ups_*
├── cmdb_ci_business_* ├── cmdb_ci_rack           ├── cmdb_ci_monitoring_*
└── cmdb_ci_cluster    └── cmdb_ci_computer_room  └── 80+ more types...
```

## 📋 Prerequisites

- **Python 3.8+**
- **ServiceNow Instance** (Developer, Enterprise, or higher)
- **API Access** - REST API enabled with appropriate permissions
- **OAuth 2.0 Credentials**: `CLIENT_ID` and `CLIENT_SECRET` (contact maintainer)

## 🚀 Quick Start

### 1. **Installation**

```bash
git clone https://github.com/Papamzor/personal-mcp-servicenow.git
cd personal-mcp-servicenow

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. **Configuration**

Create `.env` file in project root:

```bash
# OAuth 2.0 Authentication (Required)
SERVICENOW_INSTANCE=https://your-instance.service-now.com
SERVICENOW_CLIENT_ID=your_oauth_client_id
SERVICENOW_CLIENT_SECRET=your_oauth_client_secret
```

⚠️ **OAuth 2.0 Credentials Required**: This application exclusively uses OAuth 2.0 authentication for security. Contact the project maintainer to obtain OAuth client credentials for your ServiceNow instance.

### 3. **OAuth 2.0 Setup**

See [OAUTH_SETUP_GUIDE.md](OAUTH_SETUP_GUIDE.md) for complete ServiceNow OAuth configuration, or contact the maintainer for pre-configured credentials.

### 4. **Verification**

```bash
# Test environment setup (local test - no ServiceNow connection needed), expected result 2/3 pass (.env file should not be readable)
python -m Testing.test_oauth_simple

# Test actual ServiceNow connectivity by running some CMDB tools (requires valid .env configuration)
python -m Testing.test_cmdb_tools

# Test OAuth with your ServiceNow instance (requires OAuth setup), should return token validity details
python -c "import asyncio; from utility_tools import now_test_oauth; print(asyncio.run(now_test_oauth()))"
```

**Verification Steps Explained:**

- **Step 1**: Tests OAuth client creation and environment variables (offline test)
- **Step 2**: Tests actual ServiceNow API connectivity and CMDB functionality
- **Step 3**: Tests OAuth authentication flow with your ServiceNow instance

### 5. **Claude Desktop Integration**

To use this MCP server with Claude Desktop, add the following configuration to your Claude Desktop settings:

**Location of config file:**

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Add this configuration:**

```json
{
  "mcpServers": {
    "servicenow": {
      "command": "python",
      "args": ["/full/path/to/personal-mcp-servicenow/tools.py"],
      "env": {
        "SERVICENOW_INSTANCE": "https://your-instance.service-now.com",
        "SERVICENOW_CLIENT_ID": "your_oauth_client_id",
        "SERVICENOW_CLIENT_SECRET": "your_oauth_client_secret"
      }
    }
  }
}
```

**Important Notes:**

- Replace `/full/path/to/personal-mcp-servicenow/` with your actual installation path
- Replace the environment variables with your actual ServiceNow credentials
- Restart Claude Desktop after adding this configuration
- The server will auto-start when Claude Desktop launches

**Alternative: Using .env file (Recommended)**
If you prefer to keep credentials in your `.env` file:

```json
{
  "mcpServers": {
    "servicenow": {
      "command": "python",
      "args": ["/full/path/to/personal-mcp-servicenow/tools.py"]
    }
  }
}
```

### 6. **Standalone Server (Optional)**

To run the MCP server independently:

```bash
python tools.py
```

## 🏗️ Architecture

```
MCP Server (FastMCP — 36 tools)
├── Tool Layer
│   ├── Generic Wrappers (generic_tool_wrappers.py — 5 tools for 8 tables)
│   ├── Consolidated Tools (consolidated_tools.py — priority, knowledge, SLA)
│   ├── Private Task CRUD (vtb_task_tools.py — create, update via PATCH)
│   ├── CMDB Tools (cmdb_tools.py — 6 tools, 100+ CI types)
│   └── Intelligent Query Tools (intelligent_query_tools.py — NLP)
├── Core Engine
│   ├── Generic Table Tools (generic_table_tools.py — pagination, sorting, filtering)
│   └── Query Intelligence (query_intelligence.py — regex NLP)
├── API Layer
│   ├── OAuth 2.0 Client (oauth_client.py — token management)
│   └── HTTP Client (service_now_api_oauth.py — perf params, URL encoding)
└── Utilities
    ├── Server Tools (utility_tools.py)
    ├── Date Utils (date_utils.py)
    └── Constants & Config (constants.py, config_loader.py)
```

## 🧪 Testing Infrastructure

The project includes comprehensive testing capabilities:

### **Test Categories**

- **OAuth Testing** - OAuth 2.0 client creation and environment validation
- **CMDB Testing** - Configuration Item discovery and ServiceNow connectivity
- **Integration Testing** - End-to-end OAuth authentication with ServiceNow

### **Run Tests**

```bash
# Test environment setup (offline)
python -m Testing.test_oauth_simple

# Test ServiceNow connectivity and CMDB functionality
python -m Testing.test_cmdb_tools
```

## 📈 Performance & Code Quality

- **50-60% Token Usage Reduction** - Optimized field selection and query efficiency
- **Async Operations** - Non-blocking API calls with proper error handling
- **Smart Field Selection** - Essential vs. detailed modes for optimal performance
- **Efficient Error Handling** - Graceful degradation and meaningful error messages
- **Resource Management** - Configurable limits and intelligent caching
- **SonarCloud Compliance** - Cognitive complexity reduced from 20 to ≤8 in critical functions
- **PEP 8 Standards** - Complete snake_case naming convention compliance
- **Modular Architecture** - Helper functions improve maintainability and testability
- **ServiceNow Query Reliability** - Comprehensive pagination and result validation preventing missing critical incidents
- **Constants Module** - Centralized configuration eliminating hardcoded strings and magic values
- **Query Validation Framework** - Built-in ServiceNow syntax validation with completeness checks

## 🔧 Advanced Configuration

### **Field Customization**

```python
# Essential fields (fast queries)
ESSENTIAL_FIELDS = ["number", "short_description", "priority", "state"]

# Detailed fields (comprehensive data)
DETAILED_FIELDS = [..., "work_notes", "comments", "assigned_to", "sys_created_on"]
```

### **Date Filtering**

```python
# Multiple date formats supported
filters = {
    "sys_created_on_gte": "2024-01-01",  # Standard format
    "sys_created_on": ">=javascript:gs.daysAgoStart(14)",  # ServiceNow JS
    "state": "1",  # Active state
    "priority": "1"  # High priority
}
```

### **CMDB Discovery**

The system automatically discovers all CMDB tables in your ServiceNow instance and updates the supported CI types list. No manual configuration required!

## 🤝 Contributing

Contributions welcome! Please see [Contributing Guidelines](CONTRIBUTING.md).

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📚 Documentation

- [**OAuth Setup Guide**](OAUTH_SETUP_GUIDE.md) - Complete OAuth 2.0 configuration
- [**Project Documentation**](CLAUDE.md) - Comprehensive technical documentation
- [**ServiceNow Query Guide**](SERVICENOW_QUERY_GUIDE.md) - Proper ServiceNow syntax and best practices
- [**Test Documentation**](Testing/TEST_PROMPTS.md) - Testing procedures and scenarios
- [**Optimization Guide**](OPTIMIZATION_SUMMARY.md) - Performance improvements and token usage

## 🔐 Security

- **OAuth 2.0 Exclusive** - No username/password authentication supported
- **Zero Password Storage** - Enhanced security through OAuth-only approach
- **Automatic Token Management** - Secure token refresh and expiration handling
- **Environment-Based Config** - All credentials via environment variables only
- **Proper API Scoping** - Controlled permissions and access management
- **No Credential Exposure** - Comprehensive error handling without information disclosure

## 📊 Project Statistics

- **36 MCP Tools** covering 8 ServiceNow tables + CMDB (100+ CI types)
- **537 tests passing** with 80% overall code coverage
- **OAuth 2.0 Exclusive** - Enhanced security with single authentication method
- **SonarCloud Compliant** - All cognitive complexity violations resolved (CC ≤ 15)
- **PEP 8 Compliant** - 100% snake_case naming convention adherence

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

⭐ **Star this project** if you find it useful!

🐛 **Found a bug?** Please [open an issue](https://github.com/Papamzor/personal-mcp-servicenow/issues).

💡 **Have a feature request?** We'd love to hear from you!
