import re
from detect_terms import get_all_terms
from stopwords import check_rejection

CORPORATE_JARGON_DICT = [
    "circle back", "touch base", "stakeholder", "roadmap", "bandwidth",
    "alignment", "blocker", "deep dive", "action item", "deliverable",
    "ownership", "follow up", "synergy", "low hanging fruit", "escalation",
    "stakeholders", "action items", "deliverables", "blockers",
    "retrospective", "sprint planning", "postmortem"
]

def extract_candidates(text, db_path=None):
    """
    Fast candidate extraction without using LLM.
    Returns a list of raw string candidates that MIGHT be technical terms.
    """
    candidates = set()
    
    # 1. Acronyms & Capitalized Tokens
    # Splitting by spaces to evaluate words
    words = text.split()
    for i, word in enumerate(words):
        # Clean punctuation from the edges
        clean_word = word.strip(".,;:!?\"'()[]{}")
        if not clean_word:
            continue
            
        is_rej, _ = check_rejection(clean_word)
        if is_rej:
            continue
            
        # Acronym detection (2 or more uppercase letters, numbers allowed)
        if re.fullmatch(r'[A-Z0-9]{2,}', clean_word) and any(c.isalpha() for c in clean_word):
            candidates.add(clean_word)
            continue
            
        # CamelCase / PascalCase
        if re.search(r'[a-z][A-Z]', clean_word):
            candidates.add(clean_word)
            continue
            
        # Just Capitalized (e.g., Kubernetes, Helm)
        if clean_word[0].isupper() and i > 0:
            candidates.add(clean_word)

    # 2. Hyphenated term detection
    hyphenated = re.findall(r'\b[a-zA-Z]+-[a-zA-Z]+\b', text)
    for h in hyphenated:
        is_rej, _ = check_rejection(h)
        if not is_rej:
            candidates.add(h)
            
    # 3. Multi-word phrase matching (Corporate Jargon)
    for jargon in CORPORATE_JARGON_DICT:
        # Simple word boundary check
        pattern = r'\b' + re.escape(jargon) + r'\b'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # We found a match, extract the jargon in its found casing
            candidates.add(match.group(0))
            
    return list(candidates)
