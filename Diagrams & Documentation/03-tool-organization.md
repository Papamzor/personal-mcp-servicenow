# Tool Organization & Consolidation (v3.0)

This diagram shows the v3.0 architectural transformation: 24 near-duplicate per-table wrappers replaced by 5 generic parameterized tools, reducing from 55 to 36 total tools with zero functional loss.

## Before vs After: v3.0 Consolidation
```mermaid
graph TB
    subgraph "BEFORE: 24 Per-Table Wrappers"
        OLD1[similar_incidents_for_text]
        OLD2[similar_changes_for_text]
        OLD3[similar_ur_for_text]
        OLD4[get_incident_details]
        OLD5[get_change_details]
        OLD6[get_short_desc_for_incident]
        OLD7["... 18 more 1-line wrappers"]
    end

    subgraph "AFTER: 5 Generic Tools"
        NEW1["search_records(table, query)"]
        NEW2["get_record(table, number)"]
        NEW3["get_record_summary(table, number)"]
        NEW4["find_similar(table, number)"]
        NEW5["filter_records(table, filters, fields)"]
    end

    OLD1 --> NEW1
    OLD2 --> NEW1
    OLD3 --> NEW1
    OLD4 --> NEW2
    OLD5 --> NEW2
    OLD6 --> NEW3
    OLD7 --> NEW4

    NEW1 --> GTT[generic_table_tools.py]
    NEW2 --> GTT
    NEW3 --> GTT
    NEW4 --> GTT
    NEW5 --> GTT

    style NEW1 fill:#e8f5e8,stroke:#4caf50,stroke-width:3px
    style NEW2 fill:#e8f5e8,stroke:#4caf50,stroke-width:2px
    style NEW3 fill:#e8f5e8,stroke:#4caf50,stroke-width:2px
    style NEW4 fill:#e8f5e8,stroke:#4caf50,stroke-width:2px
    style NEW5 fill:#e8f5e8,stroke:#4caf50,stroke-width:2px
    style OLD7 fill:#ffebee,stroke:#f44336,stroke-width:2px
```

## v3.0 Tool Categories Overview
```mermaid
graph LR
    subgraph "36 MCP Tools"
        A[Generic Table Tools<br/>5 tools - parameterized]
        B[Incident Tools<br/>1 tool - priority + dates]
        C[Knowledge Tools<br/>3 tools - category filtering]
        D[CMDB Tools<br/>6 tools - CI discovery]
        E[Private Task Tools<br/>2 tools - CRUD]
        F[SLA Tools<br/>10 tools - specialised queries]
        G[Utility Tools<br/>5 tools - auth/connectivity]
        H[Intelligent Query Tools<br/>5 tools - NLP]
    end

    A --> I[generic_tool_wrappers.py]
    B --> J[consolidated_tools.py]
    C --> J
    F --> J
    D --> K[cmdb_tools.py]
    E --> L[vtb_task_tools.py]
    G --> M[utility_tools.py]
    H --> N[intelligent_query_tools.py]

    I --> O[generic_table_tools.py]
    J --> O
    K --> P[service_now_api_oauth.py]
    L --> Q[_make_authenticated_request]
    N --> O
    O --> P
    P --> R[ServiceNow API]
    Q --> R

    style I fill:#e8f5e8,stroke:#4caf50,stroke-width:3px
    style O fill:#e1f5fe,stroke:#2196f3,stroke-width:2px
    style P fill:#fce4ec,stroke:#e91e63,stroke-width:2px
```

## Generic Tool Wrapper Pattern (v3.0)
```mermaid
graph TB
    subgraph "MCP Tool Call"
        CALL["search_records(table='incident', query='server down')"]
    end

    subgraph "generic_tool_wrappers.py"
        VAL{table in TABLE_CONFIGS?}
        CALL --> VAL
        VAL -->|No| ERR[Return error: unsupported table]
        VAL -->|Yes| DELEGATE[Call generic function]
    end

    subgraph "generic_table_tools.py"
        DELEGATE --> QBT[query_table_by_text]
        QBT --> KW[extract_keywords]
        KW --> BUILD[Build sysparm_query]
        BUILD --> FILTER[Apply category filters]
    end

    subgraph "Pagination + API"
        FILTER --> PAG[_make_paginated_request]
        PAG --> SORT[_inject_sort_order<br/>^ORDERBYDESCsys_created_on]
        SORT --> REQ[make_nws_request]
        REQ --> PARAMS[_add_default_params<br/>+ _ensure_query_encoded]
        PARAMS --> OAUTH[OAuth 2.0 → ServiceNow]
    end

    subgraph "Supported Tables"
        T1[incident]
        T2[change_request]
        T3[sc_req_item]
        T4[sc_task]
        T5[universal_request]
        T6[kb_knowledge]
        T7[vtb_task]
        T8[task_sla]
    end

    style VAL fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    style SORT fill:#e8f5e8,stroke:#4caf50,stroke-width:2px
    style PARAMS fill:#e1f5fe,stroke:#2196f3,stroke-width:2px
```

## Tool Categories Detail

### Generic Table Tools (5 tools — generic_tool_wrappers.py)
Each validates `table` against `TABLE_CONFIGS` and delegates to `generic_table_tools.py`:
- **search_records(table, query)** → `query_table_by_text()` — text-based search
- **get_record(table, number)** → `get_record_details()` — full record by number
- **get_record_summary(table, number)** → `get_record_description()` — short description
- **find_similar(table, number)** → `find_similar_records()` — similarity matching
- **filter_records(table, filters, fields)** → `query_table_with_filters()` — structured filtering

### Consolidated Tools (14 tools — consolidated_tools.py)
Tools with unique logic that cannot be replaced by generic wrappers:
- **Priority Incidents** (1): Complex date logic, metadata, convenience helpers
- **Knowledge** (3): Category/kb_base filtering, active articles
- **SLA** (10): Each has specialised query patterns (breaching, stage, performance, etc.)

### CMDB Tools (6 tools — cmdb_tools.py)
Separate architecture with 100+ CI table types:
- `find_cis_by_type`, `search_cis_by_attributes`, `get_ci_details`
- `similar_cis_for_ci`, `get_all_ci_types`, `quick_ci_search`

### Intelligent Query Tools (5 tools — intelligent_query_tools.py)
NLP-based query processing:
- `intelligent_search`, `explain_servicenow_filters`, `build_smart_servicenow_filter`
- `get_servicenow_filter_templates`, `get_query_examples`

### Utility Tools (5 tools)
- `nowtest`, `now_test_oauth`, `now_auth_info`, `nowtestauth`, `nowtest_auth_input`

### Private Task CRUD (2 tools — vtb_task_tools.py)
- `create_private_task`, `update_private_task` (uses PATCH for partial updates)

## Consolidation Benefits

### Metrics
- **Tools**: 55 → 36 (35% reduction, zero functional loss)
- **Wrappers removed**: 24 one-line functions deleted
- **Dead code removed**: 5 duplicate functions from vtb_task_tools.py
- **Tests**: 537 passing, 80% coverage

### v3.0 API Improvements
- **Performance params**: `sysparm_exclude_reference_link=true` + `sysparm_no_count=true` on all reads
- **URL encoding**: Centralized `sysparm_query` encoding in `make_nws_request()`
- **Deterministic pagination**: `^ORDERBYDESCsys_created_on` appended to all paginated queries
- **HTTP semantics**: PUT → PATCH for partial updates

### Extensibility
1. Add table config to `constants.py`
2. All 5 generic tools automatically support the new table
3. No code duplication required
