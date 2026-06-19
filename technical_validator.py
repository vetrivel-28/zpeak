import os
from stopwords import check_rejection

DEBUG_MODE = True
LOG_FILE = "debug_rejections.log"

def log_rejection(candidate, reason):
    if DEBUG_MODE:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{candidate} -> {reason}\n")

ALLOWED_TERM_TYPES = {
    "Framework", "Tool", "Platform", "Technology", "Programming Language",
    "Database", "Cloud Service", "Security Concept", "Metric", "Methodology",
    "Acronym", "Corporate Jargon", "Technical Term", "Term"
}

def validate_candidate(term):
    """
    Validates a raw candidate before sending to LLM.
    Returns True if valid, False if it should be rejected.
    """
    if not term or len(term) < 2:
        log_rejection(term, "too short")
        return False
    
    is_rej, reason = check_rejection(term)
    if is_rej:
        log_rejection(term, reason)
        return False
        
    # Ignore purely numeric or special character strings
    clean = "".join(c for c in term if c.isalnum())
    if not clean or clean.isnumeric():
        log_rejection(term, "numeric or special characters")
        return False
        
    return True

def validate_llm_output(term, definition, category, term_type, difficulty="Intermediate", confidence="Medium", db_cache=None):
    """
    Validates the LLM output before Auto-Saving to the database.
    """
    if not term or not definition:
        log_rejection(term, "missing term or definition")
        return False
        
    if len(definition.split()) < 5:
        log_rejection(term, "definition < 5 words")
        return False
        
    if len(term) < 2:
        log_rejection(term, "term too short")
        return False
        
    if term_type not in ALLOWED_TERM_TYPES:
        log_rejection(term, f"invalid term type: {term_type}")
        return False
        
    if confidence == "Low":
        log_rejection(term, "low confidence")
        return False
        
    is_rej, reason = check_rejection(term)
    if is_rej:
        log_rejection(term, f"post-llm rejection: {reason}")
        return False
        
    if db_cache and term.lower() in db_cache:
        log_rejection(term, "already in database")
        return False
        
    return True
