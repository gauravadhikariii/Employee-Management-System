import os, sqlite3
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / 'database.db'
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
class HybridRow:
    def __init__(self, names, values): self._values, self._mapping = tuple(values), dict(zip(names, values))
    def __getitem__(self, key): return self._values[key] if isinstance(key, int) else self._mapping[key]
    def keys(self): return self._mapping.keys()
    def __iter__(self): return iter(self._values)
    def __len__(self): return len(self._values)
def hybrid_row_factory(cursor):
    names = [col.name for col in cursor.description]
    return lambda values: HybridRow(names, values)
class PostgresConnection:
    def __init__(self, conn): self.conn = conn
    def execute(self, sql, params=()): return self.conn.execute(sql.replace('?', '%s'), params)
    def commit(self): return self.conn.commit()
    def close(self): return self.conn.close()
    def __enter__(self): self.conn.__enter__(); return self
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return self.conn.__exit__(exc_type, exc_value, traceback)
        finally:
            self.conn.close()
def get_db():
    if DATABASE_URL:
        import psycopg
        return PostgresConnection(psycopg.connect(DATABASE_URL, row_factory=hybrid_row_factory, connect_timeout=10))
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; conn.execute('PRAGMA foreign_keys = ON'); return conn
def init_db():
    from werkzeug.security import generate_password_hash
    with get_db() as conn:
        if DATABASE_URL:
            conn.execute("""CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, full_name TEXT NOT NULL DEFAULT 'Administrator', email TEXT NOT NULL DEFAULT '', theme TEXT NOT NULL DEFAULT 'light')""")
            conn.execute("""CREATE TABLE IF NOT EXISTS employees (id SERIAL PRIMARY KEY, employee_code TEXT NOT NULL UNIQUE, full_name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT DEFAULT '', department TEXT NOT NULL, position TEXT NOT NULL, salary DOUBLE PRECISION NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'Active', joining_date TEXT NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        else:
            conn.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, full_name TEXT NOT NULL DEFAULT 'Administrator', email TEXT NOT NULL DEFAULT '', theme TEXT NOT NULL DEFAULT 'light')""")
            conn.execute("""CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_code TEXT NOT NULL UNIQUE, full_name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT DEFAULT '', department TEXT NOT NULL, position TEXT NOT NULL, salary REAL NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'Active', joining_date TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        user = conn.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
        if not user:
            conn.execute('INSERT INTO users (username, password_hash, full_name, email) VALUES (?, ?, ?, ?)', ('admin', generate_password_hash('Admin@123'), 'Administrator', 'admin@example.com'))
        conn.commit()
