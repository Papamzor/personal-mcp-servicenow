# Output MCP Server Start confirmation in stderr for Claude Desktop or CLI
import sys
print("Personal ServiceNow MCP Server started.", file=sys.stderr)

# Configure structlog before any module-level structlog.get_logger() call.
# The MCP stdio transport reserves stdout for JSON-RPC frames, so every log
# line must go to stderr. personal_mcp_servicenow_main.py configures this
# too, but MCP launchers that invoke tools.py directly bypass that entry
# point and would otherwise inherit structlog's stdout default — corrupting
# the frame stream on every audit log line.
import structlog
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)

from fastmcp import FastMCP
from auth_middleware import AuthMiddleware
from audit_middleware import AuditMiddleware
from Table_Tools.generic_tool_wrappers import (
    search_records, get_record, find_similar, filter_records
)
from Table_Tools.consolidated_tools import (
    # Priority incidents (unique date logic)
    get_priority_incidents,
    # Knowledge-specific tool (version-collapsing state rollup)
    get_kb_articles_by_state,
    # SLA tools (v4.0: 10 -> 5 consolidated; v5.0: -similar_slas_for_text)
    get_sla_details,
    query_slas_by_task, query_slas_by_status, query_slas_custom,
)
from Table_Tools.vtb_task_tools import create_private_task, update_private_task
from Table_Tools.kb_article_tools import (
    update_knowledge_article,
    publish_knowledge_article,
    publish_knowledge_articles,
    retire_knowledge_article,
    check_kb_duplicates,
)
from Table_Tools.cmdb_tools import (
    find_cis_by_type, search_cis_by_attributes, get_ci_details, similar_cis_for_ci, get_all_ci_types, quick_ci_search
)
from utility_tools import health_check
from Table_Tools.intelligent_query_tools import get_query_syntax_help
from tool_registry import register_tools

# v5.0 "Boron" Tier 3.3: get_priority_incidents no longer needs a hand-rolled
# **kwargs-stripping shim — it dropped **deprecated_kwargs and registers directly.


mcp = FastMCP("personalmcpservicenow")
mcp.add_middleware(AuthMiddleware())
mcp.add_middleware(AuditMiddleware())

# Register tools — 55 -> 37 (v3.0) -> 32 (v4.0) -> 38 (v4.1 KB expansion)
# -> 39 (get_query_syntax_help) -> 25 (v5.0 "Boron" Tier 2 cull).
# tests/test_integration.py asserts the count.
tools = [
    # Diagnostic (v5.0: 5 auth/health tools collapsed into one)
    health_check,

    # Generic table tools (replace 24 table-specific wrappers)
    search_records, get_record, find_similar, filter_records,

    # Priority incidents (unique date logic) — registers directly (no **kwargs shim)
    get_priority_incidents,

    # Knowledge read (version-collapsing state rollup)
    get_kb_articles_by_state,

    # Private Task CRUD
    create_private_task, update_private_task,

    # KB Article write tools (update content, publish, batch publish, retire, dup-check)
    update_knowledge_article, publish_knowledge_article, publish_knowledge_articles,
    retire_knowledge_article, check_kb_duplicates,

    # SLA tools (v4.0: 10 -> 5 consolidated; presets exposed via query_slas_by_status)
    get_sla_details,
    query_slas_by_task, query_slas_by_status, query_slas_custom,

    # CMDB tools
    find_cis_by_type, search_cis_by_attributes, get_ci_details, similar_cis_for_ci, get_all_ci_types, quick_ci_search,

    # Query-syntax reference
    get_query_syntax_help
]

# Inject the structured selection-guidance footer (tool_registry.TOOL_GUIDANCE)
# into each docstring, then register. Fails loudly if any tool lacks guidance.
register_tools(mcp, tools)

if __name__ == "__main__":
    mcp.run()
