import re

def clean_text(text: str) -> str:
    """
    Cleans up extracted raw text to prepare it for the LLM.
    Removes excessive whitespace, empty lines, and normalizes spacing.
    """
    if not text:
        return ""
        
    # Replace carriage returns with standard newlines
    text = text.replace('\r', '\n')
    
    # Replace multiple spaces/tabs with a single space
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Replace multiple newlines with double newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Strip leading/trailing whitespace
    return text.strip()
