import sys
import time
from pathlib import Path
from unittest.mock import patch
import sqlite3

sys.path.append(str(Path(__file__).parent))

import knowledge_manager
import llm_extractor

class Profiler:
    def __init__(self):
        self.queries = 0
        self.ollama = 0

prof = Profiler()

class MockCursor:
    def __init__(self, cursor):
        self._cursor = cursor
        
    def execute(self, *args, **kwargs):
        prof.queries += 1
        return self._cursor.execute(*args, **kwargs)

    def fetchall(self): return self._cursor.fetchall()
    def fetchone(self): return self._cursor.fetchone()
    
    def __iter__(self): return iter(self._cursor)
    def __next__(self): return next(self._cursor)
    
    def __getattr__(self, name):
        return getattr(self._cursor, name)

class MockConnection:
    def __init__(self, conn):
        self._conn = conn
        
    def cursor(self):
        return MockCursor(self._conn.cursor())
        
    def execute(self, *args, **kwargs):
        prof.queries += 1
        return MockCursor(self._conn.execute(*args, **kwargs))

    def __enter__(self):
        self._conn.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._conn.__exit__(exc_type, exc_val, exc_tb)
        
    def __getattr__(self, name):
        return getattr(self._conn, name)

orig_connect = sqlite3.connect
def mock_connect(*args, **kwargs):
    return MockConnection(orig_connect(*args, **kwargs))

orig_generate = llm_extractor.generate
def mock_generate(*args, **kwargs):
    prof.ollama += 1
    return orig_generate(*args, **kwargs)

db_path = Path(__file__).parent / "database" / "terms.db"

def run_benchmark(name, text):
    prof.queries = 0
    prof.ollama = 0
    
    t0 = time.perf_counter()
    with patch('sqlite3.connect', mock_connect), patch('llm_extractor.generate', mock_generate):
        knowledge_manager.process_transcript(text, db_path)
    total_ms = (time.perf_counter() - t0) * 1000
    
    print(f"\n--- {name} ---")
    print(f"Latency: {total_ms:.2f} ms")
    print(f"Database queries: {prof.queries}")
    print(f"Ollama calls: {prof.ollama}")

if __name__ == "__main__":
    print("Running Benchmarks...\n")
    
    # 1. Known term
    run_benchmark("1. Known Term", "Let's deploy to Kubernetes today.")
    
    # 2. Unknown valid term
    # LangGraph was already queried possibly. We need a random unknown term.
    run_benchmark("2. Unknown Valid Term", "We should probably implement Vectorization architecture.")
    
    # 3. Non-technical sentence
    run_benchmark("3. Non-technical sentence", "Let's go grab lunch and talk about the weekend.")
    
    # 4. Corporate jargon sentence
    run_benchmark("4. Corporate Jargon Sentence", "We need to circle back on these action items.")
