import json
import logging
from llm_service import generate

logger = logging.getLogger(__name__)

def batch_validate_and_define(candidates_list, transcript_context):
    """
    Takes a list of unknown candidates.
    Uses the LLM to validate them and generate definitions and metadata in ONE single batch call.
    Returns a dictionary mapping candidate -> {"definition": "", "category": "", "term_type": "", "difficulty": ""}
    """
    if not candidates_list:
        return {}
        
    prompt = f"""You are a strict technical glossary generator.

Below is a transcript context and a list of candidate terms extracted from it.
Your job is to validate each candidate and return definitions ONLY for genuine technical, cloud, security, AI, DevOps concepts, or corporate jargon.

NEVER define:
- Names (e.g. Rahul, Vetrivel)
- Locations (e.g. library)
- Days/Dates/Times (e.g. yesterday)
- Casual conversation (e.g. lunch plans)
- Verbs/Adjectives (e.g. failed, better)
- Generic nouns

For each VALID candidate, provide a beginner-friendly definition, the category, term type, and difficulty.
If a candidate is INVALID, omit it from the JSON completely.

Return a JSON object where keys are the valid terms, and values are objects with "definition", "category", "term_type", and "difficulty".

Allowed Categories: AI, Machine Learning, Data Science, DevOps, Backend, Cloud, Security, Product, Software Frameworks, Tools and Platforms, Corporate Jargon, Meeting Phrases, Business Terminology, Other.
Allowed Term Types: Framework, Tool, Platform, Technology, Programming Language, Database, Cloud Service, Security Concept, Metric, Methodology, Acronym, Corporate Jargon, Technical Term.
Allowed Difficulty: Beginner, Intermediate, Advanced.

Context:
{transcript_context}

Candidates:
{json.dumps(candidates_list)}

Return JSON object only. Example output format:
{{
  "Kubernetes": {{
    "definition": "An open-source system for automating deployment, scaling, and management of containerized applications.",
    "category": "DevOps",
    "term_object": "Tool",
    "difficulty": "Advanced"
  }},
  "circle back": {{
    "definition": "To return to a topic or discussion at a later time.",
    "category": "Corporate Jargon",
    "term_type": "Corporate Jargon",
    "difficulty": "Beginner"
  }}
}}
"""
    response = generate(prompt, format_json=True)
    if not response:
        return {}
        
    try:
        data = json.loads(response)
        if isinstance(data, dict):
            return data
        else:
            logger.error("LLM batch response is not a dictionary.")
            return {}
    except json.JSONDecodeError:
        logger.error("Failed to parse LLM batch response.")
        return {}
