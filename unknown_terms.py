import re
import sqlite3
import logging
from pathlib import Path
from detect_terms import get_all_terms

# Set up logging for detailed output as requested
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def extract_candidate_terms(text):
    """
    Extracts potential technical terms using heuristics.
    """
    logger.info(f"Extracting candidate terms from text: '{text}'")
    candidates = set()
    
    # 1. Acronyms / Mixed Acronyms (e.g., CPU, HTTP, JWT, LLM, DSPy, XGBoost)
    acronyms = re.findall(r'\b[A-Z]{2,}[a-zA-Z0-9\-]*\b', text)
    for a in acronyms:
        # Avoid matching simple hyphens or numbers alone
        if any(c.isalpha() for c in a):
            logger.info(f"Candidate found [Acronym/Mixed]: {a}")
            candidates.add(a)
            
    # 2. CamelCase / PascalCase words (e.g., LangGraph, CrewAI, AutoGen)
    camel_case = re.findall(r'\b[A-Z][a-z]+[A-Z][a-zA-Z]*\b', text)
    for c in camel_case:
        logger.info(f"Candidate found [CamelCase]: {c}")
        candidates.add(c)
        
    # 3. Hyphenated technical words (e.g., ROC-AUC)
    hyphenated = re.findall(r'\b[A-Z][a-zA-Z0-9]*-[A-Z][a-zA-Z0-9]*\b', text)
    for h in hyphenated:
        logger.info(f"Candidate found [Hyphenated]: {h}")
        candidates.add(h)
        
    # 4. Alphanumeric terms (e.g., k8s, b2b)
    alphanumeric = re.findall(r'\b(?:[a-zA-Z]+[0-9]+[a-zA-Z0-9]*|[0-9]+[a-zA-Z]+[a-zA-Z0-9]*)\b', text)
    for a in alphanumeric:
        if not a.isupper():  # Avoid double logging acronyms
            logger.info(f"Candidate found [Alphanumeric]: {a}")
            candidates.add(a)
            
    # 5. Capitalized words inside sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for sentence in sentences:
        words = sentence.split()
        if len(words) > 1:
            # Skip the first word of the sentence
            for word in words[1:]:
                clean_word = word.strip('.,!?;:()[]{}')
                # Check if it starts with capital and isn't fully uppercase (handled by acronyms)
                if clean_word and clean_word[0].isupper() and not clean_word.isupper():
                    if clean_word not in candidates:
                        logger.info(f"Candidate found [Capitalized Inside Sentence]: {clean_word}")
                        candidates.add(clean_word)
                        
    return list(candidates)

def process_unknown_terms(text, db_path, matched_known_terms):
    """
    Identifies unknown terms by extracting candidates and filtering out known terms.
    """
    logger.info("--- Starting Unknown Term Detection ---")
    
    # 1. Mask known terms to avoid partial matches
    text_masked = text
    for known in matched_known_terms:
        matched_str = known['matched_text']
        # Mask case-insensitively
        pattern = re.compile(r'\b' + re.escape(matched_str) + r'\b', re.IGNORECASE)
        text_masked = pattern.sub(' ' * len(matched_str), text_masked)
        
    # 2. Extract candidates from the masked text
    candidates = extract_candidate_terms(text_masked)
    
    # 3. Load known terms to filter out exact matches
    terms_dict = get_all_terms(db_path)
    known_lower = set()
    for term, data in terms_dict.items():
        known_lower.add(term.lower())
        for alias in data["aliases"]:
            if alias:
                known_lower.add(alias.lower())
                
    unknown_terms = []
    for candidate in candidates:
        clean = candidate.strip('.,!?;:()[]{}')
        if not clean:
            continue
        if clean.lower() not in known_lower:
            logger.info(f"Classified as UNKNOWN: {clean}")
            unknown_terms.append(clean)
        else:
            logger.info(f"Classified as KNOWN (filtered out): {clean}")
            
    logger.info("--- Unknown Term Detection Complete ---\n")
    return sorted(list(set(unknown_terms)))

def add_to_review_queue(unknown_terms, db_path):
    """Inserts or increments frequency of missing terms in the database."""
    if not unknown_terms:
        return
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for term in unknown_terms:
            cursor.execute("SELECT id, frequency FROM missing_terms WHERE term = ?", (term,))
            row = cursor.fetchone()
            
            if row:
                new_freq = row[1] + 1
                cursor.execute("UPDATE missing_terms SET frequency = ? WHERE id = ?", (new_freq, row[0]))
                logger.info(f"Incremented frequency for '{term}' to {new_freq}")
            else:
                cursor.execute("INSERT INTO missing_terms (term, frequency) VALUES (?, 1)", (term,))
                logger.info(f"Inserted new unknown term '{term}' into review queue")
                
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Database error while adding to review queue: {e}")
