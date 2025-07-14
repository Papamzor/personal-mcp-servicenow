def getKeywords(inputText: str) -> list[str]:
    """Extract keywords from the input text."""
    # Simple keyword extraction logic (can be improved with NLP libraries)
    keywords = inputText.split()
    return [keyword.strip().lower() for keyword in keywords if keyword.strip()]
