# Similarity Search & Intelligent Query Flow (v3.0)

This flowchart demonstrates the search flow in v3.0, showing both the generic `search_records` tool (replacing per-table wrappers) and the AI-powered `intelligent_search` tool, including the new performance and encoding enhancements.

## Search Flow

```mermaid
flowchart TD
    A["User Query: 'Find incidents about network outage'"] --> B{Search Type}
    B -->|Generic Search| C["search_records(table='incident', query='network outage')"]
    B -->|AI-Powered| D["intelligent_search(table='incident', query='...')"]

    C --> VAL{Table in TABLE_CONFIGS?}
    VAL -->|No| VALERR[Return: unsupported table error]
    VAL -->|Yes| E[query_table_by_text]

    D --> F[Query Intelligence Engine]

    E --> G[extract_keywords - Compiled Regex]
    F --> H[Natural Language Processing]

    G --> I{Keywords Found?}
    H --> J[Smart Filter Builder]

    I -->|Yes| K[Iterative Search Loop]
    I -->|No| L[Return: no records found]

    J --> M[Security Validation]
    M --> N{Input Safe?}
    N -->|Yes| O[Template Matching]
    N -->|No| P[Security Alert + Safe Processing]

    K --> Q[Build sysparm_query<br/>short_descriptionCONTAINSkeyword]
    O --> R[Execute Enhanced Query]
    P --> R

    Q --> CAT[Apply Category Filters<br/>incident/sc_req_item exclusions]
    CAT --> PAG

    R --> PAG[_make_paginated_request]

    PAG --> SORT[_inject_sort_order<br/>Append ^ORDERBYDESCsys_created_on]
    SORT --> API[make_nws_request]
    API --> ENCODE[_ensure_query_encoded<br/>Percent-encode sysparm_query]
    ENCODE --> PERF[_add_default_params<br/>+ exclude_reference_link<br/>+ no_count<br/>+ display_value]
    PERF --> OAUTH[OAuth 2.0 → ServiceNow API]

    OAUTH --> T{Results Found?}
    T -->|Yes| U[Extract Display Values + Return]
    T -->|No, Traditional| V[Try Next Keyword]
    T -->|No, AI| W[Generate Intelligence Report]

    U --> X[Return Results]
    V --> Y{More Keywords?}
    W --> Z[Return with AI Insights]

    Y -->|Yes| K
    Y -->|No| L

    subgraph "v3.0: API Enhancements"
        SORT
        ENCODE
        PERF
    end

    subgraph "AI Intelligence Features"
        AI1[Confidence Scoring]
        AI2[Query Explanation]
        AI3[SQL Generation]
        AI4[Improvement Suggestions]

        H --> AI1
        H --> AI2
        H --> AI3
        H --> AI4
    end

    style C fill:#e8f5e8,stroke:#4caf50,stroke-width:3px
    style D fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    style SORT fill:#e1f5fe,stroke:#2196f3,stroke-width:2px
    style ENCODE fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    style PERF fill:#fce4ec,stroke:#e91e63,stroke-width:2px
    style X fill:#e8f5e8,stroke:#4caf50
    style L fill:#ffebee,stroke:#f44336
```

## Search Flow Steps

### Generic Search (search_records)
1. **Table Validation**: Validate `table` parameter against `TABLE_CONFIGS` (8 supported tables)
2. **Keyword Extraction**: Compiled regex tokenizes input, filters stop words
3. **Query Construction**: Build `short_descriptionCONTAINSkeyword` for each keyword
4. **Category Filtering**: Apply incident/sc_req_item exclusion filters if enabled
5. **Paginated Request**: Offset-based pagination with deterministic sort order
6. **URL Encoding**: `_ensure_query_encoded()` percent-encodes special characters
7. **Performance Params**: `sysparm_exclude_reference_link=true` + `sysparm_no_count=true`
8. **Early Exit**: Return on first keyword match with results

### AI-Powered Search (intelligent_search)
1. **NLP Processing**: Advanced query parsing with context awareness
2. **Security Validation**: Input sanitization, ReDoS protection
3. **Template Matching**: Enterprise-grade pre-built filter patterns
4. **Smart Filter Generation**: AI-powered ServiceNow syntax creation
5. **Confidence Scoring**: 0.0-1.0 confidence with intelligence metadata
6. **Query Explanation**: Human-readable explanations and SQL equivalents

## v3.0 API Enhancement Details

### Deterministic Pagination (Step 4)
- `_inject_sort_order()` appends `^ORDERBYDESCsys_created_on` to all paginated queries
- Prevents records from being skipped or duplicated across pages
- Respects any existing `ORDERBY` clause in the query
- Callers can override or disable via `default_sort` parameter

### URL Encoding (Step 3)
- `_ensure_query_encoded()` in `make_nws_request()` centralizes encoding
- Unquotes first to prevent double-encoding, then applies `quote(value, safe='=<>&^():@!')`
- Fixes: queries with `&`, `=`, `^`, `#`, or spaces no longer cause silent full-table returns

### Performance Parameters (Step 2)
- `_add_default_params()` injects on all read requests:
  - `sysparm_exclude_reference_link=true` — removes unused reference URLs (reduces token usage)
  - `sysparm_no_count=true` — skips `SELECT COUNT(*)` (reduces latency)
  - `sysparm_display_value=true` — returns human-readable values

## Query Evolution Example

### v3.0 Generic Search
**Input**: `search_records(table="incident", query="network outage in datacenter")`

**Processing**:
1. Table validation: `incident` is in `TABLE_CONFIGS`
2. Keywords extracted: `["network", "outage", "datacenter"]`
3. First query: `short_descriptionCONTAINSnetwork`
4. Category filter applied (if enabled)
5. Sort appended: `^ORDERBYDESCsys_created_on`
6. URL encoded, performance params added
7. Paginated results returned

**Final API URL**:
```
/api/now/table/incident?sysparm_fields=number,short_description,...
&sysparm_query=short_descriptionCONTAINSnetwork^ORDERBYDESCsys_created_on
&sysparm_display_value=true&sysparm_exclude_reference_link=true&sysparm_no_count=true
&sysparm_limit=50&sysparm_offset=0
```

### AI-Powered Search
**Input**: `intelligent_search(table="incident", query="high priority incidents from last week")`

**AI Processing**:
- Time detection: "last week" → date range filter
- Priority intelligence: "high priority" → `priorityIN1,2`
- Confidence: 0.92
- SQL equivalent: `SELECT * FROM incident WHERE priority IN (1,2) AND sys_created_on BETWEEN ...`

---

*The v3.0 search architecture combines generic parameterized tools with centralized API enhancements for reliable, performant queries across all supported tables.*
