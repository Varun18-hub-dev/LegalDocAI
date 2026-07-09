import sqlite3
import json
import sys
from pathlib import Path
from contextlib import contextmanager

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from app.config import SQLITE_DB_PATH

@contextmanager
def get_db_conn():
    """Context manager for SQLite database connection."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Initialize database tables."""
    with get_db_conn() as conn:
        # Create documents table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            document_type TEXT NOT NULL,  -- 'Central Act', 'Rule', 'Judgment', 'Notification'
            title TEXT NOT NULL,
            short_title TEXT,
            year INTEGER,
            source_url TEXT,
            publication_date TEXT,
            effective_date TEXT,
            is_current INTEGER DEFAULT 1,
            metadata TEXT  -- stored as JSON string
        );
        """)

        # Create document_hierarchy table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS document_hierarchy (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            node_type TEXT NOT NULL,      -- 'part', 'chapter', 'section', 'subsection', 'proviso', 'explanation', 'illustration', 'clause'
            node_number TEXT,             -- 'Part III', 'Section 14'
            title TEXT,
            text_content TEXT NOT NULL,
            parent_node_id TEXT,          -- self-reference
            index_order INTEGER,
            chroma_id TEXT,
            FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
            FOREIGN KEY (parent_node_id) REFERENCES document_hierarchy (id) ON DELETE CASCADE
        );
        """)

        # Create document_versions table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS document_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            version_label TEXT NOT NULL,  -- 'Original', 'Amended', 'Current'
            amended_by TEXT,              -- Act or Notification ID
            text_content TEXT NOT NULL,
            effective_from TEXT,
            effective_to TEXT,
            FOREIGN KEY (node_id) REFERENCES document_hierarchy (id) ON DELETE CASCADE
        );
        """)

        # Create cross_references table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS cross_references (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_node_id TEXT NOT NULL,
            target_node_id TEXT,          -- nullable if external
            citation_text TEXT NOT NULL,  -- e.g. 'Article 21'
            reference_type TEXT,          -- 'cites_statute', 'relies_upon_case', 'amends'
            FOREIGN KEY (source_node_id) REFERENCES document_hierarchy (id) ON DELETE CASCADE,
            FOREIGN KEY (target_node_id) REFERENCES document_hierarchy (id) ON DELETE SET NULL
        );
        """)
        
        # Create users table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,           -- 'ADMIN', 'USER'
            status TEXT DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_login TEXT,
            email_verified INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        );
        """)

        # Migrate existing LAWYER or CLIENT roles to USER
        conn.execute("UPDATE users SET role = 'USER' WHERE role = 'LAWYER' OR role = 'CLIENT';")

        # Create user_documents table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS user_documents (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            status TEXT NOT NULL,         -- 'uploading', 'processing', 'processed', 'failed'
            total_pages INTEGER,
            total_chunks INTEGER,
            uploaded_at TEXT NOT NULL,
            metadata TEXT,                 -- stored as JSON string
            user_id TEXT,
            owner_name TEXT,
            visibility TEXT DEFAULT 'PRIVATE',
            created_by TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
        """)
        
        # Apply alters dynamically in case table existed without user_id / visibility columns
        for col, col_type in [("user_id", "TEXT"), ("owner_name", "TEXT"), ("visibility", "TEXT DEFAULT 'PRIVATE'"), ("created_by", "TEXT")]:
            try:
                conn.execute(f"ALTER TABLE user_documents ADD COLUMN {col} {col_type};")
            except sqlite3.OperationalError:
                pass # Column already exists

        # Create user_document_chunks table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS user_document_chunks (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES user_documents (id) ON DELETE CASCADE
        );
        """)

        # Create chat_sessions table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            pinned INTEGER DEFAULT 0,
            favorite INTEGER DEFAULT 0,
            tags TEXT,                    -- JSON list of strings
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
        """)

        # Create chat_messages table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,           -- 'user', 'assistant'
            message TEXT NOT NULL,
            citations TEXT,               -- JSON list of citations
            token_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
        );
        """)

        # Create chat_history table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            sources TEXT NOT NULL,        -- JSON list of source references
            created_at TEXT NOT NULL
        );
        """)
        
        print(f"  [OK] SQLite database initialized at: {SQLITE_DB_PATH}")

def clear_db():
    """Wipe all tables in the database."""
    with get_db_conn() as conn:
        conn.execute("DROP TABLE IF EXISTS cross_references;")
        conn.execute("DROP TABLE IF EXISTS document_versions;")
        conn.execute("DROP TABLE IF EXISTS document_hierarchy;")
        conn.execute("DROP TABLE IF EXISTS documents;")
        print("  [CLEARED] All SQLite tables cleared.")
    init_db()

# ------------------------------------------------------------
# Ingestion Operations
# ------------------------------------------------------------

def insert_document(doc_id, document_type, title, short_title=None, year=None, 
                    source_url=None, publication_date=None, effective_date=None, 
                    is_current=1, metadata_dict=None):
    """Insert or replace a document record."""
    meta_str = json.dumps(metadata_dict or {})
    with get_db_conn() as conn:
        conn.execute("""
        INSERT OR REPLACE INTO documents (id, document_type, title, short_title, year, source_url, publication_date, effective_date, is_current, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (doc_id, document_type, title, short_title, year, source_url, publication_date, effective_date, is_current, meta_str))

def insert_hierarchy_node(node_id, document_id, node_type, node_number, title, text_content, 
                          parent_node_id=None, index_order=0, chroma_id=None):
    """Insert a hierarchical node of a document."""
    with get_db_conn() as conn:
        conn.execute("""
        INSERT OR REPLACE INTO document_hierarchy (id, document_id, node_type, node_number, title, text_content, parent_node_id, index_order, chroma_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (node_id, document_id, node_type, node_number, title, text_content, parent_node_id, index_order, chroma_id))

def insert_document_version(node_id, version_label, text_content, amended_by=None, effective_from=None, effective_to=None):
    """Insert a historical or current version of a node's text."""
    with get_db_conn() as conn:
        conn.execute("""
        INSERT INTO document_versions (node_id, version_label, amended_by, text_content, effective_from, effective_to)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (node_id, version_label, amended_by, text_content, effective_from, effective_to))

def insert_cross_reference(source_node_id, citation_text, target_node_id=None, reference_type=None):
    """Insert a cross-reference between document nodes."""
    with get_db_conn() as conn:
        # Avoid duplicate links
        cursor = conn.execute("""
        SELECT id FROM cross_references 
        WHERE source_node_id = ? AND citation_text = ? AND (target_node_id = ? OR (target_node_id IS NULL AND ? IS NULL))
        """, (source_node_id, citation_text, target_node_id, target_node_id))
        
        if cursor.fetchone():
            return # Duplicate reference exists, skip
            
        conn.execute("""
        INSERT INTO cross_references (source_node_id, target_node_id, citation_text, reference_type)
        VALUES (?, ?, ?, ?)
        """, (source_node_id, target_node_id, citation_text, reference_type))

# ------------------------------------------------------------
# Query Operations
# ------------------------------------------------------------

def get_document(doc_id):
    """Retrieve a document record."""
    with get_db_conn() as conn:
        cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        if row:
            doc = dict(row)
            doc['metadata'] = json.loads(doc['metadata'])
            return doc
    return None

def get_document_nodes(doc_id):
    """Retrieve all hierarchy nodes for a document sorted by order."""
    with get_db_conn() as conn:
        cursor = conn.execute("""
        SELECT * FROM document_hierarchy 
        WHERE document_id = ? 
        ORDER BY index_order ASC
        """, (doc_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_node(node_id):
    """Retrieve a single hierarchy node."""
    with get_db_conn() as conn:
        cursor = conn.execute("SELECT * FROM document_hierarchy WHERE id = ?", (node_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_node_versions(node_id):
    """Retrieve version history for a node."""
    with get_db_conn() as conn:
        cursor = conn.execute("""
        SELECT * FROM document_versions 
        WHERE node_id = ? 
        ORDER BY id DESC
        """, (node_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_node_references(node_id):
    """Retrieve all references starting from this node."""
    with get_db_conn() as conn:
        cursor = conn.execute("""
        SELECT r.*, h.node_number as target_number, d.title as target_doc_title
        FROM cross_references r
        LEFT JOIN document_hierarchy h ON r.target_node_id = h.id
        LEFT JOIN documents d ON h.document_id = d.id
        WHERE r.source_node_id = ?
        """, (node_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_incoming_references(node_id):
    """Retrieve all references citing this node."""
    with get_db_conn() as conn:
        cursor = conn.execute("""
        SELECT r.*, h.node_number as source_number, h.document_id as source_doc_id, d.title as source_doc_title
        FROM cross_references r
        JOIN document_hierarchy h ON r.source_node_id = h.id
        JOIN documents d ON h.document_id = d.id
        WHERE r.target_node_id = ?
        """, (node_id,))
        return [dict(row) for row in cursor.fetchall()]

def insert_user_document(doc_id, filename, file_path, status="uploading", total_pages=None, total_chunks=None, metadata_dict=None, user_id=None, owner_name=None, visibility="PRIVATE", created_by=None):
    import datetime
    meta_str = json.dumps(metadata_dict or {})
    uploaded_at = datetime.datetime.now().isoformat()
    with get_db_conn() as conn:
        conn.execute("""
        INSERT OR REPLACE INTO user_documents (id, filename, file_path, status, total_pages, total_chunks, uploaded_at, metadata, user_id, owner_name, visibility, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (doc_id, filename, file_path, status, total_pages, total_chunks, uploaded_at, meta_str, user_id, owner_name, visibility, created_by))

def update_user_document_status(doc_id, status, total_pages=None, total_chunks=None):
    with get_db_conn() as conn:
        if total_pages is not None and total_chunks is not None:
            conn.execute("""
            UPDATE user_documents SET status = ?, total_pages = ?, total_chunks = ? WHERE id = ?
            """, (status, total_pages, total_chunks, doc_id))
        else:
            conn.execute("""
            UPDATE user_documents SET status = ? WHERE id = ?
            """, (status, doc_id))

def get_user_document(doc_id):
    with get_db_conn() as conn:
        row = conn.execute("SELECT * FROM user_documents WHERE id = ?", (doc_id,)).fetchone()
        if row:
            doc = dict(row)
            doc["metadata"] = json.loads(doc["metadata"] or "{}")
            return doc
    return None

def get_all_user_documents(user_id=None):
    with get_db_conn() as conn:
        if user_id:
            rows = conn.execute("""
            SELECT * FROM user_documents 
            WHERE user_id = ? OR visibility = 'PUBLIC'
            ORDER BY uploaded_at DESC
            """, (user_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM user_documents ORDER BY uploaded_at DESC").fetchall()
        docs = []
        for r in rows:
            d = dict(r)
            d["metadata"] = json.loads(d["metadata"] or "{}")
            docs.append(d)
        return docs

def delete_user_document_db(doc_id):
    with get_db_conn() as conn:
        conn.execute("DELETE FROM user_documents WHERE id = ?", (doc_id,))

# ------------------------------------------------------------
# User Accounts Helpers
# ------------------------------------------------------------

def insert_user(user_id, name, email, password_hash, role, status='ACTIVE'):
    import datetime
    created_at = datetime.datetime.now().isoformat()
    updated_at = created_at
    with get_db_conn() as conn:
        conn.execute("""
        INSERT INTO users (id, name, email, password_hash, role, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, email.lower().strip(), password_hash, role.upper().strip(), status, created_at, updated_at))

def get_user_by_email(email):
    with get_db_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id):
    with get_db_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

def get_all_users():
    with get_db_conn() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

def update_user_role(user_id, role):
    import datetime
    updated_at = datetime.datetime.now().isoformat()
    with get_db_conn() as conn:
        conn.execute("UPDATE users SET role = ?, updated_at = ? WHERE id = ?", (role.upper(), updated_at, user_id))

def delete_user_db(user_id):
    with get_db_conn() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

# ------------------------------------------------------------
# Multi-User Chat Session Helpers
# ------------------------------------------------------------

def create_chat_session(session_id, user_id, title, tags_list=None):
    import datetime
    created_at = datetime.datetime.now().isoformat()
    updated_at = created_at
    tags_str = json.dumps(tags_list or [])
    with get_db_conn() as conn:
        conn.execute("""
        INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at, tags)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, user_id, title, created_at, updated_at, tags_str))

def get_chat_sessions_by_user(user_id):
    with get_db_conn() as conn:
        rows = conn.execute("""
        SELECT * FROM chat_sessions 
        WHERE user_id = ? 
        ORDER BY pinned DESC, updated_at DESC
        """, (user_id,)).fetchall()
        sessions = []
        for r in rows:
            s = dict(r)
            s["tags"] = json.loads(s["tags"] or "[]")
            sessions.append(s)
        return sessions

def get_chat_session(session_id):
    with get_db_conn() as conn:
        row = conn.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
        if row:
            s = dict(row)
            s["tags"] = json.loads(s["tags"] or "[]")
            return s
    return None

def insert_chat_message(session_id, role, message, citations_list=None, token_count=0):
    import datetime
    citations_str = json.dumps(citations_list or [])
    created_at = datetime.datetime.now().isoformat()
    with get_db_conn() as conn:
        conn.execute("""
        INSERT INTO chat_messages (session_id, role, message, citations, token_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, role, message, citations_str, token_count, created_at))
        
        # Touch chat_session update timestamp
        conn.execute("UPDATE chat_sessions SET updated_at = ? WHERE id = ?", (created_at, session_id))

def get_chat_messages(session_id):
    with get_db_conn() as conn:
        rows = conn.execute("""
        SELECT * FROM chat_messages 
        WHERE session_id = ? 
        ORDER BY created_at ASC
        """, (session_id,)).fetchall()
        messages = []
        for r in rows:
            m = dict(r)
            m["citations"] = json.loads(m["citations"] or "[]")
            messages.append(m)
        return messages

def delete_chat_session_db(session_id):
    with get_db_conn() as conn:
        conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))

def update_chat_session_title(session_id, title):
    import datetime
    updated_at = datetime.datetime.now().isoformat()
    with get_db_conn() as conn:
        conn.execute("UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?", (title, updated_at, session_id))

def toggle_pin_session(session_id, pinned):
    with get_db_conn() as conn:
        conn.execute("UPDATE chat_sessions SET pinned = ? WHERE id = ?", (1 if pinned else 0, session_id))

def toggle_favorite_session(session_id, favorite):
    with get_db_conn() as conn:
        conn.execute("UPDATE chat_sessions SET favorite = ? WHERE id = ?", (1 if favorite else 0, session_id))

# ------------------------------------------------------------
# Deprecated Log Helpers (Single User Compatibility)
# ------------------------------------------------------------

def insert_chat_log(session_id, question, answer, sources_list):
    import datetime
    sources_str = json.dumps(sources_list)
    created_at = datetime.datetime.now().isoformat()
    with get_db_conn() as conn:
        conn.execute("""
        INSERT INTO chat_history (session_id, question, answer, sources, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (session_id, question, answer, sources_str, created_at))

def get_chat_history(session_id):
    with get_db_conn() as conn:
        rows = conn.execute("""
        SELECT * FROM chat_history 
        WHERE session_id = ? 
        ORDER BY created_at ASC
        """, (session_id,)).fetchall()
        history = []
        for r in rows:
            h = dict(r)
            h["sources"] = json.loads(h["sources"] or "[]")
            history.append(h)
        return history

def delete_chat_history(session_id):
    with get_db_conn() as conn:
        conn.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))

# ------------------------------------------------------------
# System Metrics & Oversight Helpers (Admin Dashboard)
# ------------------------------------------------------------

def get_admin_metrics():
    with get_db_conn() as conn:
        total_users = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'USER'").fetchone()[0]
        total_admins = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'ADMIN'").fetchone()[0]
        total_documents = conn.execute("SELECT COUNT(*) FROM user_documents").fetchone()[0]
        
        # Calculate daily queries
        queries_today = conn.execute("""
        SELECT COUNT(*) FROM chat_messages 
        WHERE role = 'user' AND created_at >= date('now')
        """).fetchone()[0]
        
        return {
            "total_users": total_users + total_admins,
            "total_lawyers": 0, # Deprecated
            "total_clients": total_users, # USER role acts as clients
            "total_documents": total_documents,
            "queries_today": queries_today or 0,
            "average_latency_ms": 240,       # Simulated system latency
            "cache_hit_rate": 84.5,         # Simulated operational metric
            "tokens_used_today": 14208,     # Simulated tokens counter
            "errors_today": 0
        }

def insert_user_document_chunk(chunk_id: str, document_id: str, page_number: int, chunk_index: int, chunk_text: str):
    with get_db_conn() as conn:
        conn.execute("""
        INSERT OR REPLACE INTO user_document_chunks (id, document_id, page_number, chunk_index, chunk_text)
        VALUES (?, ?, ?, ?, ?)
        """, (chunk_id, document_id, page_number, chunk_index, chunk_text))

def get_user_document_chunks(document_id: str) -> list[dict]:
    with get_db_conn() as conn:
        rows = conn.execute("""
        SELECT id, document_id, page_number, chunk_index, chunk_text
        FROM user_document_chunks
        WHERE document_id = ?
        """, (document_id,)).fetchall()
        return [dict(r) for r in rows]

