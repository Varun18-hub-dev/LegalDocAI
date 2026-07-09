"""
LegalDocAI - Configuration
All settings, paths, and API keys are managed here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

# ============================================================
# PATHS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# Check for production Railway mounted volume
DATA_DIR_ENV = os.getenv("DATA_DIR")
if DATA_DIR_ENV:
    DATA_DIR = Path(DATA_DIR_ENV)
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    VECTOR_STORE_DIR = DATA_DIR / "sqlite"
    SQLITE_DB_PATH = VECTOR_STORE_DIR / "legaldocai.db"
    CHROMA_PERSIST_DIR = str(DATA_DIR / "chromadb")
    UPLOAD_DIR = DATA_DIR / "uploads"
    LOG_DIR = DATA_DIR / "logs"
else:
    # Local fallback
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    VECTOR_STORE_DIR = BASE_DIR / "vector_store"
    SQLITE_DB_PATH = VECTOR_STORE_DIR / "legal_kb.db"
    CHROMA_PERSIST_DIR = str(VECTOR_STORE_DIR / "chromadb")
    UPLOAD_DIR = DATA_DIR / "raw" / "uploaded"
    LOG_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, Path(SQLITE_DB_PATH).parent, Path(CHROMA_PERSIST_DIR), Path(UPLOAD_DIR), Path(LOG_DIR)]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============================================================
# API KEYS
# ============================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ============================================================
# EMBEDDING MODEL
# ============================================================
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# ============================================================
# CHROMADB
# ============================================================
# CHROMA_PERSIST_DIR is configured dynamically above based on DATA_DIR
CHROMA_COLLECTION_LEGAL_KB = "legal_knowledge_base"
CHROMA_COLLECTION_CASE_DOCS = "case_documents"

# ============================================================
# CHUNKING
# ============================================================
CHUNK_SIZE = 500          # tokens per chunk
CHUNK_OVERLAP = 50        # overlapping tokens between chunks

# ============================================================
# DATA SOURCES - URLs for downloading legal documents
# ============================================================
DATA_SOURCES = {
    "constitution": {
        "name": "Constitution of India",
        "url": "https://www.constituteproject.org/constitution/India_2016.pdf",
        "backup_url": "https://cdnbbsr.s3waas.gov.in/s380537a945c7aaa788f04571e18c5f259/uploads/2024/01/2024011024.pdf",
        "filename": "constitution_of_india.pdf",
        "category": "constitution",
    },
    "bns": {
        "name": "Bharatiya Nyaya Sanhita 2023 (New IPC)",
        "url": "https://www.mha.gov.in/sites/default/files/250883_english_01042024.pdf",
        "backup_url": "https://egazette.gov.in/WriteReadData/2023/248045.pdf",
        "filename": "bns_2023.pdf",
        "category": "criminal_law",
    },
    "bnss": {
        "name": "Bharatiya Nagarik Suraksha Sanhita 2023 (New CrPC)",
        "url": "https://www.mha.gov.in/sites/default/files/2024-04/250884_2_english_01042024.pdf",
        "backup_url": "https://egazette.gov.in/WriteReadData/2023/248049.pdf",
        "filename": "bnss_2023.pdf",
        "category": "criminal_procedure",
    },
    "bsa": {
        "name": "Bharatiya Sakshya Adhiniyam 2023 (New Evidence Act)",
        "url": "https://egazette.gov.in/WriteReadData/2023/250882.pdf",
        "backup_url": "https://www.indiacode.nic.in/bitstream/123456789/20060/1/aa2023-47.pdf",
        "filename": "bsa_2023.pdf",
        "category": "evidence_law",
    },
}

# ============================================================
# MONGODB (for later phases)
# ============================================================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = "legaldocai"
