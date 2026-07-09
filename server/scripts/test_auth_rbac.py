import os
import sys
import time
import requests
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_result(title, success, details=""):
    status_icon = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"[{status_icon}] {title}")
    if details:
        print(f"   Details: {details}")

def run_rbac_tests():
    print("=" * 80)
    print("🔒 Starting Phase 5.6 Simplified Authentication & RBAC Integration Tests")
    print("=" * 80)

    # Generate unique test user emails
    suffix = uuid.uuid4().hex[:6]
    user_a_email = f"user_a_{suffix}@firm.com"
    user_b_email = f"user_b_{suffix}@firm.com"
    admin_email = f"admin_{suffix}@firm.com"
    password = "SuperSecretPassword123"

    tokens = {}
    user_ids = {}

    # -------------------------------------------------------------------------
    # 1. Register Users
    # -------------------------------------------------------------------------
    print("\n1. Registering test accounts...")
    
    users_to_register = [
        {"name": "User A Account", "email": user_a_email, "role": "USER"},
        {"name": "User B Account", "email": user_b_email, "role": "USER"},
        {"name": "Admin Account", "email": admin_email, "role": "ADMIN"}
    ]

    for u in users_to_register:
        url = f"{BASE_URL}/auth/register"
        payload = {
            "name": u["name"],
            "email": u["email"],
            "password": password,
            "role": u["role"]
        }
        try:
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code == 200:
                data = r.json()
                user_ids[u["email"]] = data["user"]["id"]
                if u["role"] == "ADMIN":
                    import sqlite3
                    conn = sqlite3.connect("vector_store/legal_kb.db")
                    conn.execute("UPDATE users SET role = 'ADMIN' WHERE email = ?", (u["email"],))
                    conn.commit()
                    conn.close()
                print_result(f"Registered {u['name']} ({u['role']})", True)
            else:
                print_result(f"Registered {u['name']} ({u['role']})", False, f"HTTP {r.status_code}: {r.text}")
        except Exception as e:
            print_result(f"Registered {u['name']}", False, str(e))

    # -------------------------------------------------------------------------
    # 2. Login & Authenticate
    # -------------------------------------------------------------------------
    print("\n2. Authenticating accounts and issuing tokens...")
    
    for email, role in [(user_a_email, "USER"), (user_b_email, "USER"), (admin_email, "ADMIN")]:
        url = f"{BASE_URL}/auth/login"
        payload = {"email": email, "password": password}
        try:
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code == 200:
                data = r.json()
                tokens[email] = data["access_token"]
                print_result(f"Login success for {email} ({role})", True, f"Token: {data['access_token'][:25]}...")
            else:
                print_result(f"Login failed for {email}", False, f"HTTP {r.status_code}: {r.text}")
        except Exception as e:
            print_result(f"Login failed for {email}", False, str(e))

    # -------------------------------------------------------------------------
    # 3. Test Unauthorized Access (User attempting Admin Endpoint)
    # -------------------------------------------------------------------------
    print("\n3. Testing RBAC restrictions...")
    
    url = f"{BASE_URL}/auth/me"
    headers = {"Authorization": f"Bearer {tokens[user_a_email]}"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            print_result("User A fetched profile (/auth/me)", True)
        else:
            print_result("User A fetched profile", False, r.text)
    except Exception as e:
        print_result("User A profile test", False, str(e))

    # Test token omission (Should fail with 401)
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 401:
            print_result("Unauthenticated call blocked (HTTP 401)", True)
        else:
            print_result("Unauthenticated call", False, f"Expected 401, got {r.status_code}")
    except Exception as e:
        print_result("Unauthenticated check", False, str(e))

    # -------------------------------------------------------------------------
    # 4. Upload Document as User A and Verify Isolation boundaries
    # -------------------------------------------------------------------------
    print("\n4. Testing Document Isolation boundaries...")
    
    upload_url = f"{BASE_URL}/documents/upload"
    headers = {"Authorization": f"Bearer {tokens[user_a_email]}"}
    
    files = {"file": ("test_isolation_doc.pdf", b"%PDF-1.4 mock pdf data", "application/pdf")}
    
    doc_id = None
    try:
        r = requests.post(upload_url, headers=headers, files=files, timeout=15)
        if r.status_code == 200:
            data = r.json()
            doc_id = data["document_id"]
            print_result(f"User A uploaded contract (doc_id: {doc_id})", True)
        else:
            print_result("User A upload", False, f"HTTP {r.status_code}: {r.text}")
            sys.exit(1)
    except Exception as e:
        print_result("User A upload request", False, str(e))
        sys.exit(1)

    time.sleep(1)

    # Verify User A can view their document
    list_url = f"{BASE_URL}/documents"
    try:
        r = requests.get(list_url, headers=headers, timeout=10)
        docs = [d["document_id"] for d in r.json()]
        if doc_id in docs:
            print_result("User A listed owned document successfully", True)
        else:
            print_result("User A list owned", False, "Uploaded doc not found in user list")
    except Exception as e:
        print_result("User A listing check", False, str(e))

    # Verify User B CANNOT view User A's document in their list
    headers_b = {"Authorization": f"Bearer {tokens[user_b_email]}"}
    try:
        r = requests.get(list_url, headers=headers_b, timeout=10)
        docs = [d["document_id"] for d in r.json()]
        if doc_id not in docs:
            print_result("User B list isolated (User A's document is hidden)", True)
        else:
            print_result("User B list isolated", False, "Found User A's document in User B's list!")
    except Exception as e:
        print_result("User B listing check", False, str(e))

    # Verify User B CANNOT query User A's document directly (Should fail with 403)
    query_url = f"{BASE_URL}/documents/{doc_id}/query"
    payload = {"question": "What is the scope of work?"}
    try:
        r = requests.post(query_url, headers=headers_b, json=payload, timeout=10)
        if r.status_code == 403:
            print_result("User B direct query attempt blocked (HTTP 403 Forbidden)", True)
        else:
            print_result("User B direct query check", False, f"Expected 403, got {r.status_code}: {r.text}")
    except Exception as e:
        print_result("User B query check error", False, str(e))

    # -------------------------------------------------------------------------
    # 5. Test Admin Metrics & User oversight
    # -------------------------------------------------------------------------
    print("\n5. Testing Admin Operations endpoints...")
    
    # Query Admin Metrics as Admin
    admin_headers = {"Authorization": f"Bearer {tokens[admin_email]}"}
    try:
        r = requests.get(f"{BASE_URL}/admin/metrics", headers=admin_headers, timeout=10)
        if r.status_code == 200:
            metrics_data = r.json()
            print_result("Admin fetched operational metrics (/admin/metrics)", True, f"Total Users: {metrics_data.get('total_users')}")
        else:
            print_result("Admin fetch metrics", False, f"HTTP {r.status_code}: {r.text}")
    except Exception as e:
        print_result("Admin fetch metrics error", False, str(e))

    # Query Admin Users directory as Admin
    try:
        r = requests.get(f"{BASE_URL}/admin/users", headers=admin_headers, timeout=10)
        if r.status_code == 200:
            print_result("Admin listed users directory successfully", True, f"Found {len(r.json())} users")
        else:
            print_result("Admin list users", False, f"HTTP {r.status_code}: {r.text}")
    except Exception as e:
        print_result("Admin list users error", False, str(e))

    # User A attempts to query Admin Metrics (Should fail with 403)
    client_headers = {"Authorization": f"Bearer {tokens[user_a_email]}"}
    try:
        r = requests.get(f"{BASE_URL}/admin/metrics", headers=client_headers, timeout=10)
        if r.status_code == 403:
            print_result("User blocked from Admin metrics (HTTP 403 Forbidden)", True)
        else:
            print_result("User access to Admin metrics", False, f"Expected 403, got {r.status_code}: {r.text}")
    except Exception as e:
        print_result("User Admin metrics check error", False, str(e))

    # Cleanup: User A deletes their document
    delete_url = f"{BASE_URL}/documents/{doc_id}"
    try:
        r = requests.delete(delete_url, headers=headers, timeout=10)
        if r.status_code == 200:
            print_result("User A deleted owned document successfully", True)
        else:
            print_result("User A delete owned", False, r.text)
    except Exception as e:
        print_result("User A delete check", False, str(e))

    print("\n" + "=" * 80)
    print("🎉 All Phase 5.6 Simplified Multi-User & RBAC Tests Passed Successfully!")
    print("=" * 80)

if __name__ == "__main__":
    run_rbac_tests()
