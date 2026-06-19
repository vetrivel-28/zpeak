import logging
from pathlib import Path
import json
from knowledge_manager import process_transcript, get_kb_statistics

logging.basicConfig(level=logging.INFO)

db_path = Path("d:/zpeak/meeting-term-explainer/database/terms.db")

text = "The LangGraph workflow uses OpenTelemetry and DSPy."

import llm_extractor
print("LLM extracted:", llm_extractor.extract_technical_terms(text))

print("Running test...")
results = process_transcript(text, db_path)
print(json.dumps(results, indent=2))

print("Stats:")
print(json.dumps(get_kb_statistics(db_path), indent=2))
