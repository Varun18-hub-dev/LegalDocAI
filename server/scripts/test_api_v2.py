import os
import sys
import time
import requests
from pathlib import Path

# Base URL for API
BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_tests():
    print("=" * 80)
    print("🚀  Starting LegalDocAI API Integration Tests")
    print("=" * 80)
    
    # -------------------------------------------------------------------------
    # 1. Verify Health check
    # -------------------------------------------------------------------------
    print("\n🩺 Checking health endpoint...")
    url = f"{BASE_URL}/health"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        print(f"   Health check status: {data['status']}")
        print(f"   Database: {data['sqlite']}, Vector Store: {data['chromadb']}, Gemini: {data['gemini']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        sys.exit(1)
        
    # -------------------------------------------------------------------------
    # 2. Query Global KB
    # -------------------------------------------------------------------------
    print("\n🔍 Querying Global Knowledge Base...")
    url = f"{BASE_URL}/kb/query"
    payload = {"question": "consequences of breach of contract compensation"}
    try:
        start = time.time()
        r = requests.post(url, json=payload, timeout=40)
        r.raise_for_status()
        data = r.json()
        duration = (time.time() - start) * 1000
        print(f"   Query complete in {duration:.2f} ms")
        print(f"   Intent: {data['metadata']['intent']}")
        print(f"   Citations Count: {len(data['citations'])}")
        print(f"   Answer snippet: {data['answer'][:200]}...")
        
        # Verify citations are present
        if not data['citations']:
            print("❌ Failure: Expected citations in global KB query response, but found none.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Global KB query failed: {e}")
        sys.exit(1)
        
    # -------------------------------------------------------------------------
    # 3. Upload User Document
    # -------------------------------------------------------------------------
    print("\n📥 Uploading user document...")
    pdf_path = Path(__file__).resolve().parent.parent / "NewCriminalLaws.pdf"
    if not pdf_path.exists():
        print(f"❌ Test PDF not found at: {pdf_path}")
        sys.exit(1)
        
    url = f"{BASE_URL}/documents/upload"
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            r = requests.post(url, files=files, timeout=10)
            r.raise_for_status()
            data = r.json()
            doc_id = data["document_id"]
            print(f"   Document uploaded successfully. Assigned ID: {doc_id}")
    except Exception as e:
        print(f"❌ Document upload failed: {e}")
        sys.exit(1)
        
    # -------------------------------------------------------------------------
    # 4. Poll Document Status
    # -------------------------------------------------------------------------
    print("\n⏳ Polling processing status...")
    status_url = f"{BASE_URL}/documents/{doc_id}/status"
    status = "uploading"
    attempts = 0
    max_attempts = 15
    while status != "processed" and attempts < max_attempts:
        attempts += 1
        time.sleep(2)
        try:
            r = requests.get(status_url, timeout=5)
            r.raise_for_status()
            data = r.json()
            status = data["status"]
            print(f"   [Attempt {attempts}] Status: {status} | Chunks: {data.get('total_chunks')}")
            if status == "failed":
                print("❌ Document processing marked as FAILED in background task.")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Status poll failed: {e}")
            sys.exit(1)
            
    if status != "processed":
        print(f"❌ Document processing timed out after {max_attempts * 2} seconds.")
        sys.exit(1)
        
    # -------------------------------------------------------------------------
    # 5. Query Document (RAG QA)
    # -------------------------------------------------------------------------
    print("\n💬 Querying document (QA)...")
    query_url = f"{BASE_URL}/documents/{doc_id}/query"
    session_id = "test_session_123"
    payload = {
        "question": "What is the new criminal law details?",
        "session_id": session_id
    }
    try:
        r = requests.post(query_url, json=payload, timeout=40)
        r.raise_for_status()
        data = r.json()
        print(f"   Answer snippet: {data['answer'][:200]}...")
        print(f"   Citations: {len(data['citations'])} found.")
    except Exception as e:
        print(f"❌ Document query failed: {e}")
        sys.exit(1)
        
    # -------------------------------------------------------------------------
    # 6. Summarize Document
    # -------------------------------------------------------------------------
    print("\n📝 Summarizing document...")
    summary_url = f"{BASE_URL}/documents/{doc_id}/summary"
    try:
        r = requests.get(summary_url, timeout=40)
        r.raise_for_status()
        data = r.json()
        print(f"   Summary snippet: {data['summary'][:200]}...")
    except Exception as e:
        print(f"❌ Document summary failed: {e}")
        sys.exit(1)
        
    # -------------------------------------------------------------------------
    # 7. Compare Documents
    # -------------------------------------------------------------------------
    print("\n⚖️ Comparing document to itself...")
    compare_url = f"{BASE_URL}/documents/compare"
    payload = {
        "doc_id_1": doc_id,
        "doc_id_2": doc_id
    }
    try:
        r = requests.post(compare_url, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        print(f"   Comparison snippet: {data['comparison_summary'][:200]}...")
    except Exception as e:
        print(f"❌ Document comparison failed: {e}")
        sys.exit(1)
        
    # -------------------------------------------------------------------------
    # 8. Check Chat History Session
    # -------------------------------------------------------------------------
    print("\n📜 Checking chat history persistence...")
    chat_url = f"{BASE_URL}/chat/{session_id}"
    try:
        r = requests.get(chat_url, timeout=5)
        r.raise_for_status()
        data = r.json()
        print(f"   Chat logs found: {len(data['history'])}")
        if not data['history']:
            print("❌ Failure: Chat history is empty.")
            sys.exit(1)
        print(f"   First question: '{data['history'][0]['question']}'")
        
        # Clear history
        requests.delete(chat_url, timeout=5)
        print("   Cleared chat logs.")
    except Exception as e:
        print(f"❌ Chat history verification failed: {e}")
        sys.exit(1)
        
    # -------------------------------------------------------------------------
    # 9. Delete Document
    # -------------------------------------------------------------------------
    print("\n🗑️ Deleting document...")
    delete_url = f"{BASE_URL}/documents/{doc_id}"
    try:
        r = requests.delete(delete_url, timeout=5)
        r.raise_for_status()
        print("   Document deleted successfully.")
        
        # Confirm deleted (should return 404)
        r_confirm = requests.get(status_url, timeout=5)
        if r_confirm.status_code != 404:
            print("❌ Failure: Status endpoint still returning document after deletion.")
            sys.exit(1)
        print("   Confirmed 404 status post deletion.")
    except Exception as e:
        print(f"❌ Document deletion failed: {e}")
        sys.exit(1)
        
    print("\n" + "=" * 80)
    print("✅  All API integration tests completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
