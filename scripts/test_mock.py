import sqlite3
from unittest.mock import patch

orig_connect = sqlite3.connect
queries = 0

def mock_connect(*args, **kwargs):
    conn = orig_connect(*args, **kwargs)
    orig_cursor = conn.cursor
    def mock_cursor(*cargs, **ckwargs):
        c = orig_cursor(*cargs, **ckwargs)
        orig_execute = c.execute
        def mock_execute(*eargs, **ekwargs):
            global queries
            queries += 1
            return orig_execute(*eargs, **ekwargs)
        c.execute = mock_execute
        return c
    conn.cursor = mock_cursor
    return conn

patch('sqlite3.connect', mock_connect).start()

import detect_terms # or just simulate
conn = sqlite3.connect(':memory:')
c = conn.cursor()
c.execute('CREATE TABLE test (id INT)')
print('Queries:', queries)
