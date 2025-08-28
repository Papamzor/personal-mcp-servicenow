import spacy
from typing import List, Optional
import re
import sys

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Error: SpaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'.", file=sys.stderr)
    raise

def extract_keywords(input_text: str, context: str = "general", max_keywords: int = 3) -> List[str]:
    """Extract relevant keywords from input text using spaCy.
    
    Args:
        input_text: The raw input text to process.
        context: The context for keyword extraction.
        max_keywords: Maximum number of keywords to return.
    
    Returns:
        A list of top keywords limited by max_keywords.
    """
    input_text = input_text.strip().lower()
    
    # Quick regex check for record numbers first
    number_patterns = [r'chg\d+', r'inc\d+', r'kb\d+', r'ritm\d+']
    for pattern in number_patterns:
        matches = re.findall(pattern, input_text, re.IGNORECASE)
        if matches:
            return matches[:1]  # Return only first match
    
    # Process with spaCy for content keywords
    doc = nlp(input_text)
    
    # Prioritize NOUN and ADJ tokens, filter more aggressively
    keywords = [
        token.lemma_ for token in doc 
        if (token.pos_ in ['NOUN', 'ADJ'] and 
            not token.is_stop and 
            not token.is_punct and 
            len(token.text) > 3 and
            token.text.isalpha())
    ]
    
    # Remove duplicates and limit results
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