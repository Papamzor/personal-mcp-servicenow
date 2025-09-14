from typing import List, Optional
import re

# Compiled regex patterns for performance
_SERVICENOW_RECORD_PATTERNS = [
    re.compile(r'\bchg\d+\b', re.IGNORECASE),
    re.compile(r'\binc\d+\b', re.IGNORECASE), 
    re.compile(r'\bkb\d+\b', re.IGNORECASE),
    re.compile(r'\britm\d+\b', re.IGNORECASE),
    re.compile(r'\bvtb\d+\b', re.IGNORECASE)
]

# Common stop words to filter out
_STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
    'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
}

def extract_keywords(input_text: str, context: str = "general", max_keywords: int = 3) -> List[str]:
    """Extract relevant keywords from input text using lightweight regex patterns.
    
    Args:
        input_text: The raw input text to process.
        context: The context for keyword extraction (unused in simplified version).
        max_keywords: Maximum number of keywords to return.
    
    Returns:
        A list of top keywords limited by max_keywords.
    """
    if not input_text or not input_text.strip():
        return []
    
    input_text = input_text.strip().lower()
    
    # Check for ServiceNow record numbers first (highest priority)
    record_matches = _extract_record_numbers(input_text)
    if record_matches:
        return record_matches[:1]  # Return only first match
    
    # Extract content keywords using simplified approach
    content_keywords = _extract_content_keywords(input_text, max_keywords)
    return content_keywords

def _extract_record_numbers(text: str) -> List[str]:
    """Extract ServiceNow record numbers from text."""
    matches = []
    for pattern in _SERVICENOW_RECORD_PATTERNS:
        found = pattern.findall(text)
        if found:
            matches.extend(found)
    return matches

def _extract_content_keywords(text: str, max_keywords: int) -> List[str]:
    """Extract content keywords using basic text processing."""
    # Split into words and filter
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text)  # Words 4+ chars, letters only
    
    # Filter out stop words and convert to lowercase
    keywords = [
        word.lower() for word in words 
        if word.lower() not in _STOP_WORDS
    ]
    
    # Remove duplicates while preserving order
    unique_keywords = list(dict.fromkeys(keywords))
    return unique_keywords[:max_keywords]

def refine_query(input_text: str) -> tuple[str, Optional[str]]:
    """Refine input text for search queries."""
    input_text = " ".join(input_text.strip().lower().split())
    
    if not input_text or len(input_text) < 3:
        return "", "Input too short."
    
    # Use optimized keyword extraction
    keywords = extract_keywords(input_text, max_keywords=2)
    
    if not keywords:
        return input_text, "Please provide specific terms."
    
    return " ".join(keywords), None