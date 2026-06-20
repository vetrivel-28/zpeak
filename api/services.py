import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List

import knowledge_manager
import llm_extractor
import detect_terms
import technical_validator
import knowledge_quality

logger = logging.getLogger(__name__)

# Resolve database path relative to root directory
DB_PATH = Path(__file__).parent.parent / "database" / "terms.db"

def explain_text(text: str) -> Dict[str, Any]:
    """
    Processes the transcript to find known, new, and unknown terms.
    Includes native performance timing instrumentation from knowledge_manager.
    """
    results = knowledge_manager.process_transcript(text, DB_PATH)
        
    return {
        "known_terms": results.get("known_terms", []),
        "new_terms": results.get("newly_learned_terms", []),
        "unknown_terms": results.get("unknown_terms", [])
    }

def explain_single_term(term: str) -> Dict[str, str]:
    """
    Explains a single term. Looks up SQLite once locally. If not found, falls back to LLM.
    """
    # 1. Look up SQLite directly
    terms_dict = detect_terms.get_all_terms(DB_PATH)
    t_lower = term.lower()
    
    for db_term, data in terms_dict.items():
        if t_lower == db_term.lower() or t_lower in [a.lower() for a in data["aliases"] if a]:
            return {
                "term": db_term,
                "definition": data["definition"],
                "category": data["category"],
                "source": "database"
            }

    print("[TERM VALIDATION]")
    print(f"Input: {term}")

    # 2. Before LLM: Check fake term
    if not knowledge_quality.validate_fake_term(term):
        print("[LLM BLOCKED]")
        return {
            "term": term,
            "definition": "Unable to verify technical term",
            "category": "Unknown",
            "saved": False,
            "source": "rejected"
        }
        
    print("[LLM ALLOWED]")

    # 3. If not found: use LLM
    llm_results = llm_extractor.batch_validate_and_define([term], "")
    
    if term in llm_results:
        data = llm_results[term]
        definition = data.get("definition", "")
        category = data.get("category", "Other")
        term_type = data.get("term_type", "Other")
        difficulty = data.get("difficulty", "Intermediate")
        
        # Validate the generated term
        known_cache_lower = {t.lower() for t in terms_dict.keys()}
        for data_ in terms_dict.values():
            for a in data_["aliases"]:
                if a: known_cache_lower.add(a.lower())
                
        is_valid_technical = technical_validator.validate_llm_output(
            term, definition, category, term_type,
            difficulty=difficulty, confidence="Medium", db_cache=known_cache_lower
        )
        is_valid_quality = knowledge_quality.validate_definition(term, definition, category)
        is_valid_fake = knowledge_quality.validate_fake_term(term)
        
        is_valid = is_valid_technical and is_valid_quality and is_valid_fake
        
        # 4. Save valid term
        if is_valid:
            knowledge_manager.insert_new_term(term, definition, category, term_type, difficulty, DB_PATH)
            
        return {
            "term": term,
            "definition": definition,
            "category": category,
            "saved": is_valid,
            "source": "llm" if is_valid else "AI Extraction"
        }
        
    return {
        "term": term,
        "definition": "Could not generate a valid definition for this term.",
        "category": "Unknown",
        "saved": False,
        "source": "llm"
    }

def search_terms(query: str) -> List[Dict[str, str]]:
    """
    Searches SQLite for a specific term or alias.
    """
    results = []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if aliases column exists
        cursor.execute("PRAGMA table_info(terms)")
        columns = [info[1] for info in cursor.fetchall()]
        has_aliases = "aliases" in columns
        
        search_query = f"%{query}%"
        
        if has_aliases:
            cursor.execute(
                "SELECT term, definition, category, source FROM terms WHERE term LIKE ? OR aliases LIKE ? LIMIT 50",
                (search_query, search_query)
            )
        else:
            cursor.execute(
                "SELECT term, definition, category, source FROM terms WHERE term LIKE ? LIMIT 50",
                (search_query,)
            )
            
        for row in cursor.fetchall():
            results.append({
                "term": row[0],
                "definition": row[1],
                "category": row[2],
                "source": row[3]
            })
        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Database error during search: {e}")
        
    return results

def get_stats() -> Dict[str, Any]:
    """
    Retrieves knowledge base statistics.
    """
    stats = knowledge_manager.get_kb_statistics(DB_PATH)
    
    categories_dict = {cat["category"]: cat["count"] for cat in stats.get("top_categories", [])}
    
    return {
        "total_terms": stats.get("total_terms", 0),
        "categories": categories_dict,
        "ai_generated": stats.get("ai_generated", 0)
    }
