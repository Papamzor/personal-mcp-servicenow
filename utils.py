import spacy
from typing import List, Optional
import re
import sys

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Error: SpaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'.", file=sys.stderr)
    raise

def extract_keywords(input_text: str, context: str = "general") -> List[str]:
    """Extract relevant keywords from input text using spaCy.
    
    Args:
        input_text: The raw input text to process.
        context: The context for keyword extraction (e.g., 'knowledge' for knowledge articles).
    
    Returns:
        A list of cleaned and relevant keywords.
    """
    # Normalize input text
    input_text = input_text.strip().lower()
    
    # Process text with spaCy
    doc = nlp(input_text)
    
    # Extract tokens, excluding stop words, punctuation, and short tokens
    keywords = [
        token.lemma_ for token in doc 
        if not token.is_stop and not token.is_punct and len(token.text) > 2
    ]
    
    # Add specific identifiers based on context
    number_patterns = [r'chg\d+', r'inc\d+', r'kb\d+']
    matches = []
    for pattern in number_patterns:
        matches.extend(re.findall(pattern, input_text, re.IGNORECASE))
    
    # Knowledge-specific terms
    if context == "knowledge":
        matches.extend(re.findall(r'it|hr|facilities|sla|ritm', input_text, re.IGNORECASE))
    
    keywords.extend(matches)
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(keywords))

async def refine_query(input_text: str) -> tuple[str, Optional[str]]:
    """Refine unclear input text and suggest clarifications if needed.
    
    Args:
        input_text: The raw input text to refine.
    
    Returns:
        A tuple of (refined query, clarification message or None).
    """
    # Normalize input
    input_text = " ".join(input_text.strip().lower().split())
    
    # Check for empty or very short input
    if not input_text or len(input_text) < 3:
        return "", "Input is too short or empty. Please provide more details."
    
    # Check for specific identifiers (e.g., CHG, INC, KB numbers)
    number_patterns = [r'chg\d+', r'inc\d+', r'kb\d+']
    identifiers = []
    for pattern in number_patterns:
        matches = re.findall(pattern, input_text, re.IGNORECASE)
        identifiers.extend(matches)
    
    # If an identifier is found, prioritize it
    if identifiers:
        return identifiers[0], None
    
    # Process with spaCy for keyword extraction
    keywords = extract_keywords(input_text, context="general")
    
    # If no meaningful keywords, request clarification
    if not keywords:
        return input_text, "Input is unclear. Please provide specific terms or identifiers (e.g., KB0000001, incident description)."
    
    # Join keywords for refined query
    refined_query = " ".join(keywords)
    return refined_query, None