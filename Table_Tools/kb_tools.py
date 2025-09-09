
from service_now_api_oauth import make_nws_request, NWS_API_BASE
from typing import Any, List, Optional
from utils import extract_keywords, refine_query
import re

# Common fields for KB queries
COMMON_KB_FIELDS = [
    "number",
    "short_description",
    "kb_knowledge_base",
    "kb_category",
    "sys_created_on",
    "state",
    "assigned_to",
    "assignment_group"
]

async def similar_knowledge_for_text(input_text: str, kb_base: Optional[str] = None, category: Optional[str] = None) -> dict[str, Any] | str:
    """Search for knowledge articles based on input text, optionally filtered by knowledge base or category.
    
    Args:
        input_text: The text to search for relevant knowledge articles.
        kb_base: Optional knowledge base sys_id or name to filter results.
        category: Optional category to filter results.
    
    Returns:
        A dictionary of knowledge articles or an error message.
    """
    refined_query, clarification = refine_query(input_text)
    if clarification:
        return clarification
    
    keywords = extract_keywords(refined_query, context="knowledge")
    if not keywords:
        return "No relevant keywords found in input text."
    
    # Build the query with optional filters
    query_parts = [f"short_descriptionCONTAINS{keyword}" for keyword in keywords]
    if kb_base:
        query_parts.append(f"kb_knowledge_base={kb_base}")
    if category:
        query_parts.append(f"kb_category={category}")
    
    query = "^".join(query_parts) if query_parts else "short_descriptionISNOTEMPTY"
    
    url = f"{NWS_API_BASE}/api/now/table/kb_knowledge?sysparm_fields={','.join(COMMON_KB_FIELDS)}&sysparm_query={query}"
    data = await make_nws_request(url)
    if data and data.get('result'):
        return data
    return "Unable to fetch knowledge articles or no articles found."

async def get_knowledge_details(input_kb: str) -> dict[str, Any] | str:
    """Get detailed information for a given knowledge article based on input KB number.
    
    Args:
        input_kb: The knowledge article number (e.g., 'KB0000001').
    
    Returns:
        A dictionary containing knowledge article details or an error message.
    """
    # Validate KB number format
    if not re.match(r'^KB\d+$', input_kb, re.IGNORECASE):
        return "Invalid knowledge article number format. Expected format: KB followed by digits (e.g., KB0000001)."
    
    fields = COMMON_KB_FIELDS + [
        "text",
        "category",
        "workflow_state",
        "valid_to",
        "article_type",
        "author",
        "sys_updated_on"
    ]
    url = f"{NWS_API_BASE}/api/now/table/kb_knowledge?sysparm_fields={','.join(fields)}&sysparm_query=number={input_kb}"
    data = await make_nws_request(url)
    if data and data.get('result'):
        results = data['result']
        # If results is a non-empty list, return the first item
        if isinstance(results, list) and results:
            return results[0]
        # If results is a dict, return it directly
        elif isinstance(results, dict):
            return results
    return "Unable to fetch knowledge article details or no article found."

async def get_knowledge_by_category(category: str, kb_base: Optional[str] = None) -> dict[str, Any] | str:
    """Retrieve knowledge articles by category, optionally filtered by knowledge base.
    
    Args:
        category: The category to filter articles (e.g., 'IT', 'HR').
        kb_base: Optional knowledge base sys_id or name to filter results.
    
    Returns:
        A dictionary of knowledge articles or an error message.
    """
    if not category:
        return "Category is required."
    
    query_parts = [f"kb_category={category}"]
    if kb_base:
        query_parts.append(f"kb_knowledge_base={kb_base}")
    
    query = "^".join(query_parts)
    url = f"{NWS_API_BASE}/api/now/table/kb_knowledge?sysparm_fields={','.join(COMMON_KB_FIELDS)}&sysparm_query={query}"
    data = await make_nws_request(url)
    if data and data.get('result'):
        return data
    return "Unable to fetch knowledge articles for the specified category."

async def get_active_knowledge_articles(input_text: str) -> dict[str, Any] | str:
    """Search for active (non-expired) knowledge articles based on input text.
    
    Args:
        input_text: The text to search for relevant knowledge articles.
    
    Returns:
        A dictionary of active knowledge articles or an error message.
    """
    refined_query, clarification = refine_query(input_text)
    if clarification:
        return clarification
    
    keywords = extract_keywords(refined_query, context="knowledge")
    if not keywords:
        return "No relevant keywords found in input text."
    
    query_parts = [f"short_descriptionCONTAINS{keyword}" for keyword in keywords]
    query_parts.append("valid_to>=javascript:gs.nowDateTime()^ORvalid_toISNULL")
    
    query = "^".join(query_parts)
    fields = COMMON_KB_FIELDS + ["valid_to"]
    url = f"{NWS_API_BASE}/api/now/table/kb_knowledge?sysparm_fields={','.join(fields)}&sysparm_query={query}"
    data = await make_nws_request(url)
    if data and data.get('result'):
        return data
    return "Unable to fetch active knowledge articles or no articles found."