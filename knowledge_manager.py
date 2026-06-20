import sqlite3
import logging
from datetime import date
from detect_terms import detect_terms, get_all_terms
import llm_extractor
from fast_extractor import extract_candidates
from technical_validator import validate_candidate, validate_llm_output
from stopwords import check_rejection
import knowledge_quality
import time

logger = logging.getLogger(__name__)

def is_known_term(term, db_path, known_cache=None):
    """Checks if a term (or its aliases) exists in the database."""
    if known_cache is None:
        terms_dict = get_all_terms(db_path)
        known_cache = set()
        for t, data in terms_dict.items():
            known_cache.add(t.lower())
            for a in data["aliases"]:
                if a:
                    known_cache.add(a.lower())
    return term.lower() in known_cache

def insert_new_term(term, definition, category, term_type, difficulty, db_path):
    """Inserts a newly learned term into the database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO terms (term, definition, category, term_type, difficulty, aliases, source, status) VALUES (?, ?, ?, ?, ?, '', 'AI Extraction', 'active')",
            (term, definition, category, term_type, difficulty)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        logger.warning(f"Term '{term}' already exists during insert.")
    except sqlite3.Error as e:
        logger.error(f"Database error while inserting '{term}': {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def process_transcript(text, db_path):
    """
    Orchestrates the new fast pipeline:
    1. Regex detection
    2. Fast Candidate extraction
    3. Filtering & DB Lookup
    4. Batch LLM Processing for unknowns
    """
    logger.info("Starting fast hybrid extraction...")

    t_start = time.perf_counter()

    # Database Lookup (Once)
    t0_db = time.perf_counter()
    terms_dict = get_all_terms(db_path)
    db_ms = (time.perf_counter() - t0_db) * 1000

    # 1. Regex Detection (Fast) & Candidate Extraction
    t0_ext = time.perf_counter()
    known_terms_regex = detect_terms(text, db_path, terms_dict=terms_dict)
    found_regex_lower = {item['term'].lower() for item in known_terms_regex}
    candidates = extract_candidates(text, db_path)
    ext_ms = (time.perf_counter() - t0_ext) * 1000

    # Filtering Candidates
    t0_val = time.perf_counter()
    known_cache = set()
    for t, data in terms_dict.items():
        known_cache.add(t.lower())
        for a in data["aliases"]:
            if a:
                known_cache.add(a.lower())

    unknown_candidates = []
    
    for term in candidates:
        t_lower = term.lower()
        if t_lower in found_regex_lower:
            continue
            
        if t_lower in known_cache:
            # Re-map to canonical
            canonical = None
            for db_term, data in terms_dict.items():
                if t_lower == db_term.lower() or t_lower in [a.lower() for a in data["aliases"] if a]:
                    canonical = db_term
                    break
            
            if canonical and canonical.lower() not in found_regex_lower:
                known_terms_regex.append({
                    "term": canonical,
                    "matched_text": term,
                    "definition": terms_dict[canonical]["definition"],
                    "category": terms_dict[canonical]["category"],
                    "term_type": terms_dict[canonical].get("term_type", "Other"),
                    "source": "Regex Match",
                    "confidence": "High"
                })
                found_regex_lower.add(canonical.lower())
        else:
            if validate_candidate(term):
                if t_lower not in [c.lower() for c in unknown_candidates]:
                    unknown_candidates.append(term)
    val_ms1 = (time.perf_counter() - t0_val) * 1000

    # 3. Batch LLM Processing
    t0_llm = time.perf_counter()
    newly_learned = []
    unresolved_unknowns = []
    llm_results = {}

    if unknown_candidates:
        logger.info(f"Batch validating {len(unknown_candidates)} candidates via LLM")
        llm_results = llm_extractor.batch_validate_and_define(unknown_candidates, text)
    llm_ms = (time.perf_counter() - t0_llm) * 1000
        
    t0_val2 = time.perf_counter()
    save_ms = 0.0
    known_cache_lower = {t.lower() for t in known_cache}
    
    if unknown_candidates:
        for term in unknown_candidates:
            if term in llm_results:
                data = llm_results[term]
                definition = data.get("definition", "")
                category = data.get("category", "Other")
                term_type = data.get("term_type", "Other")
                difficulty = data.get("difficulty", "Intermediate")
                
                is_valid_technical = validate_llm_output(
                    term, definition, category, term_type, 
                    difficulty=difficulty, confidence="Medium", db_cache=known_cache_lower
                )
                is_valid_quality = knowledge_quality.validate_definition(term, definition, category)
                is_valid_fake = knowledge_quality.validate_fake_term(term)
                
                is_valid = is_valid_technical and is_valid_quality and is_valid_fake
                source = "AI Extraction"
                
                if is_valid:
                    confidence = "Medium"
                    t0_save = time.perf_counter()
                    insert_new_term(term, definition, category, term_type, difficulty, db_path)
                    save_ms += (time.perf_counter() - t0_save) * 1000
                else:
                    confidence = "Low"
                    
                newly_learned.append({
                    "term": term,
                    "definition": definition,
                    "category": category,
                    "term_type": term_type,
                    "difficulty": difficulty,
                    "source": source,
                    "confidence": confidence,
                    "saved": is_valid
                })
            else:
                unresolved_unknowns.append(term)
                
    val_ms2 = (time.perf_counter() - t0_val2) * 1000 - save_ms
    total_ms = (time.perf_counter() - t_start) * 1000
    
    print("[PERF]")
    print(f"Database: {db_ms:.0f} ms")
    print(f"Extraction: {ext_ms:.0f} ms")
    print(f"LLM: {llm_ms:.0f} ms")
    print(f"Validation: {(val_ms1 + val_ms2):.0f} ms")
    print(f"Save: {save_ms:.0f} ms")
    print(f"Total: {total_ms:.0f} ms")
                
    return {
        "known_terms": known_terms_regex,
        "newly_learned_terms": newly_learned,
        "unknown_terms": unresolved_unknowns
    }

def get_kb_statistics(db_path):
    """Fetches stats for the admin dashboard, including health metrics."""
    stats = {
        "total_terms": 0,
        "ai_generated": 0,
        "manual_terms": 0,
        "flagged_terms": 0,
        "deleted_terms": 0,
        "health_percent": 100,
        "top_categories": []
    }
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # We only count active terms in total_terms
        cursor.execute("SELECT COUNT(*) FROM terms WHERE status='active'")
        stats["total_terms"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM terms WHERE source='AI Extraction' AND status='active'")
        stats["ai_generated"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM terms WHERE source='manual' AND status='active'")
        stats["manual_terms"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM terms WHERE status='deleted'")
        stats["deleted_terms"] = cursor.fetchone()[0]
        
        # Check for flagged terms (simulate the cleanup tool)
        cursor.execute("SELECT term FROM terms WHERE status='active'")
        flagged_count = 0
        for row in cursor.fetchall():
            term = row[0]
            if check_rejection(term)[0] or len(term) < 2 or term.isnumeric():
                flagged_count += 1
        stats["flagged_terms"] = flagged_count
        
        if stats["total_terms"] > 0:
            stats["health_percent"] = max(0, 100 - int((flagged_count / stats["total_terms"]) * 100))
        
        cursor.execute("SELECT category, COUNT(*) as count FROM terms WHERE status='active' GROUP BY category ORDER BY count DESC LIMIT 5")
        stats["top_categories"] = [{"category": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Database error fetching stats: {e}")
        
    return stats
