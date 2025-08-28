# Similarity Search Data Flow

This flowchart demonstrates how the MCP server processes text-based similarity searches, using NLP and optimization techniques for efficient ServiceNow queries.

```mermaid
flowchart TD
    A[User Query: 'Find similar incidents to network outage'] --> B[similarincidentsfortext]
    B --> C[extract_keywords using spaCy NLP]
    C --> D{Keywords Found?}
    D -->|Yes| E[Loop through keywords by priority]
    D -->|No| F[Return 'No records found']
    
    E --> G[Build ServiceNow Query]
    G --> H["/api/now/table/incident?<br/>sysparm_fields=number,short_description,priority,state<br/>&sysparm_query=short_descriptionCONTAINS{keyword}"]
    H --> I[make_nws_request with OAuth token]
    I --> J{Results Found?}
    J -->|Yes| K[Return Results - Early Exit]
    J -->|No| L[Try Next Keyword]
    L --> M{More Keywords?}
    M -->|Yes| E
    M -->|No| F
    
    subgraph "Performance Optimizations"
        N[Essential Fields Only<br/>4 fields vs 50+ available]
        O[Keyword Priority<br/>Most relevant terms first]
        P[Early Exit Strategy<br/>Stop on first match]
        Q[Cached OAuth Tokens<br/>Reuse for 3600 seconds]
        R[Async Operations<br/>Non-blocking I/O]
    end
    
    subgraph "NLP Processing Detail"
        S[Input Text] --> T[spaCy Pipeline]
        T --> U[Tokenization]
        U --> V[POS Tagging]
        V --> W[Named Entity Recognition]
        W --> X[Filter Nouns, Proper Nouns, Entities]
        X --> Y[Remove Stop Words]
        Y --> Z[Return Prioritized Keywords]
    end
    
    G --> N
    C --> O
    J --> P
    I --> Q
    B --> R
    C --> S
    
    style K fill:#d4edda
    style F fill:#f8d7da
    style P fill:#fff3cd
    style Q fill:#cce5ff
```

## Search Flow Steps

1. **Input Processing**: User provides natural language query
2. **NLP Analysis**: spaCy extracts meaningful keywords from text
3. **Query Construction**: Build optimized ServiceNow API queries
4. **Iterative Search**: Try keywords in priority order
5. **Early Exit**: Return immediately on first successful match
6. **Fallback**: Continue with remaining keywords if needed

## Optimization Strategies

### Performance Optimizations
- **Minimal Field Selection**: Only essential fields (number, short_description, priority, state)
- **Keyword Priority**: Most relevant terms searched first
- **Early Exit**: Stop searching on first match found
- **Connection Reuse**: OAuth tokens cached for 1 hour
- **Async Operations**: Non-blocking HTTP requests

### NLP Processing
- **Smart Tokenization**: Extract meaningful terms from natural language
- **Entity Recognition**: Identify technical terms, product names, locations
- **POS Filtering**: Focus on nouns and proper nouns
- **Stop Word Removal**: Filter out common words (the, and, or, etc.)
- **Relevance Ranking**: Prioritize keywords by importance

## Example Query Evolution

**Input**: "Find incidents similar to network outage in datacenter"

**Keywords Extracted**: ["network", "outage", "datacenter"]

**API Queries**:
1. `short_descriptionCONTAINSnetwork` ← Most likely to match
2. `short_descriptionCONTAINSoutage` ← If #1 fails
3. `short_descriptionCONTAINSdatacenter` ← If #1 and #2 fail