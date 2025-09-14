# Changelog

All notable changes to the Personal MCP ServiceNow project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-14

### 🚨 BREAKING CHANGES

This is a major architectural overhaul with significant breaking changes. Migration guide available in `MIGRATION_V2.md`.

#### **Deleted Files (Breaking Changes)**
- **REMOVED**: `Table_Tools/incident_tools.py` - Use `consolidated_tools.py` functions instead
- **REMOVED**: `Table_Tools/change_tools.py` - Use `consolidated_tools.py` functions instead
- **REMOVED**: `Table_Tools/kb_tools.py` - Use `consolidated_tools.py` functions instead
- **REMOVED**: `Table_Tools/ur_tools.py` - Use `consolidated_tools.py` functions instead

#### **Authentication Changes**
- **OAuth 2.0 Only**: Removed basic authentication fallback for enhanced security
- **Required Environment Variables**: `SERVICENOW_CLIENT_ID` and `SERVICENOW_CLIENT_SECRET` now mandatory

#### **API Changes**
- **Tool Registration**: Consolidated from 25+ individual tools to unified approach
- **Function Names**: All MCP tools now use snake_case naming convention
- **Return Types**: Standardized return formats across all functions

### 🚀 NEW FEATURES

#### **AI-Powered Natural Language Queries**
- **Intelligent Search**: `intelligent_search()` - Natural language to ServiceNow queries
- **Query Explanation**: `explain_servicenow_filters()` - AI explanations of what filters will do
- **Smart Filter Building**: `build_smart_servicenow_filter()` - Convert natural language to ServiceNow syntax
- **Predefined Templates**: `get_servicenow_filter_templates()` - Ready-to-use filter patterns
- **Query Examples**: `get_query_examples()` - Natural language query examples

#### **Enhanced Generic Table Operations**
- **Universal Functions**: `query_table_intelligently()` - AI-powered queries for any table
- **Advanced Filtering**: `query_table_with_filters()` with intelligent natural language parsing
- **Priority Queries**: `get_records_by_priority()` - Generic priority filtering for any table
- **Generic CRUD**: Complete Create, Read, Update operations for supported tables

#### **Natural Language Intelligence**
- **Date Range Parsing**:
  - "Week 35 2025" → Proper BETWEEN syntax with calculated dates
  - "August 25-31, 2025" → Month range parsing
  - "2025-08-25 to 2025-08-31" → ISO date range
- **Priority Parsing**:
  - "1,2" → "priority=1^ORpriority=2" (proper OR syntax)
  - "P1,P2" → "priority=1^ORpriority=2" (P-notation conversion)
- **Caller Exclusion Parsing**:
  - "logicmonitor" → Automatic sys_id lookup and exclusion

### 🛡️ SECURITY ENHANCEMENTS

#### **ReDoS Protection**
- **Input Validation**: Pre-validation of all text inputs to prevent malicious patterns
- **Timeout Protection**: `timeout_protection()` context manager for regex operations
- **Length Limits**: Automatic rejection of overly long input strings

#### **Enhanced Authentication**
- **OAuth 2.0 Exclusive**: Improved security through OAuth-only approach
- **Automatic Token Refresh**: Intelligent token management and expiration handling

### ⚡ PERFORMANCE IMPROVEMENTS

#### **Optimized Architecture**
- **Code Reduction**: Net reduction of 142 lines while adding significant functionality
- **Pagination**: `_make_paginated_request()` with configurable limits and complete result retrieval
- **Smart Caching**: Automatic token caching and reuse
- **Query Optimization**: Intelligent query building with handler registry pattern

#### **Enhanced API Integration**
- **URL Encoding Preservation**: Maintains ServiceNow JavaScript functions during encoding
- **Proper OR Syntax**: Correct ServiceNow query syntax for multiple priorities
- **JavaScript Date Functions**: Perfect BETWEEN syntax with ServiceNow date functions

### 📚 DOCUMENTATION & TESTING

#### **Comprehensive Documentation**
- **Architecture Diagrams**: Complete system architecture documentation
- **AI Intelligence Flow**: Detailed documentation of natural language processing
- **Tool Organization**: Clear mapping of all available tools and capabilities
- **API Examples**: Extensive examples of natural language queries

#### **Enhanced Testing**
- **Consolidated Tool Tests**: `Testing/test_consolidated_tools.py` with 417 new lines
- **Query Intelligence Tests**: Enhanced `Testing/test_query_intelligence.py`
- **Comprehensive Validation**: `Testing/test_filtering_fixes.py` with 100% success rate
- **CMDB Testing**: Updated `Testing/test_cmdb_tools.py`

### 🏗️ ARCHITECTURAL IMPROVEMENTS

#### **Code Quality Enhancements**
- **Cognitive Complexity Reduction**: All functions now under complexity limit ≤15
- **Helper Function Extraction**: Modular design with single-responsibility functions
- **Constants Consolidation**: Enhanced `constants.py` with centralized configuration
- **Error Message Standardization**: All duplicated literals moved to constants

#### **Maintainability**
- **Single Responsibility**: Clear separation of concerns across modules
- **Enhanced Testability**: Individual components can be tested independently
- **Modular Design**: Reusable functions with consistent interfaces

### 🔧 INFRASTRUCTURE

#### **New Dependencies**
- Enhanced `requirements.txt` with AI/ML processing capabilities
- Natural language processing support
- Advanced regex processing with safety features

#### **Tool Registration Optimization**
- **Streamlined Registration**: Unified tool registration in `tools.py`
- **Intelligent Query Tools**: 5 new AI-powered MCP tools
- **Zero Functional Regression**: All existing functionality maintained

### 📈 METRICS

- **Lines Added**: 2,781
- **Lines Removed**: 1,146
- **Net Change**: +1,635 lines of enhanced functionality
- **Files Modified**: 29
- **Files Deleted**: 4 (consolidated into generic functions)
- **Files Created**: 7 (documentation, tests, new features)

### 🔄 MIGRATION GUIDE

See `MIGRATION_V2.md` for detailed migration instructions from v1.x to v2.0.

### 🙏 ACKNOWLEDGMENTS

This release represents one of the largest architectural changes in the project's history, implementing cutting-edge AI integration while maintaining zero functional regression.

---

## [1.0.0] - Previous Release

Previous release information maintained for historical reference.