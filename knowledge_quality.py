import re

def validate_definition(term, definition, category):
    """
    Validates the quality of a generated definition.
    Returns True if valid, False if rejected.
    """
    # Rule 5: Reject category "Other"
    if category.strip().lower() == "other":
        return False
        
    def_str = definition.strip()
    
    # Rule 3: Reject length < 5 words
    words = def_str.split()
    if len(words) < 5:
        return False
        
    # Rule 4: Reject starting with generic intros
    lower_def = def_str.lower()
    reject_starts = ["this refers to", "this is", "it is"]
    if any(lower_def.startswith(start) for start in reject_starts):
        return False
        
    # Rule 2: Reject generic phrases
    generic_phrases = [
        "a product created by an ai company",
        "used in many industries",
        "technology platform"
    ]
    if any(phrase in lower_def for phrase in generic_phrases):
        return False
        
    # Rule 1: Reject if definition contains the term itself repeatedly
    # Check if the exact term appears more than once in the definition
    term_pattern = r'\b' + re.escape(term.lower()) + r'\b'
    matches = re.findall(term_pattern, lower_def)
    if len(matches) > 1:
        return False
        
    return True

def validate_fake_term(term):
    """
    Protects against fake or hallucinated terms.
    Returns True if the term is valid (NOT a fake term), False if rejected.
    """
    # 1. Contains >3 consecutive uppercase sections (CamelCase with 4+ humps)
    if re.search(r'(?:[A-Z][a-z]+){4,}', term):
        return False
        
    # 2. Contains trailing year-like numbers (3 or more trailing digits)
    if re.search(r'\d{3,}$', term):
        return False
        
    # 3. Length > 25 chars and not a known acronym (acronyms are all upper)
    if len(term) > 25 and not term.isupper():
        return False
        
    return True
