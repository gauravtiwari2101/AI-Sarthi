"""
AI Sarthi — Live End-to-End Test Suite
Tests 15 realistic questions against the running FastAPI backend.
"""
import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def http_get(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return resp.getcode(), json.loads(resp.read().decode('utf-8'))

def http_post(url, data):
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.getcode(), json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))

QUESTIONS = [
    {
        "id": 1,
        "title": "Nanded latest budget",
        "query": "How much healthcare budget was approved for Nanded in the latest available year?",
        "expected_district": "Nanded"
    },
    {
        "id": 2,
        "title": "Compare Pune and Nagpur",
        "query": "Compare Pune and Nagpur healthcare budgets.",
        "expected_district": "Pune"
    },
    {
        "id": 3,
        "title": "Nashik historical records",
        "query": "Show Nashik's available historical funding records.",
        "expected_district": "Nashik"
    },
    {
        "id": 4,
        "title": "Amravati budget percentage change",
        "query": "What percentage change occurred in Amravati's comparable budgets?",
        "expected_district": "Amravati"
    },
    {
        "id": 5,
        "title": "Highest documented allocations",
        "query": "Which districts have the highest documented approved healthcare allocations?",
        "expected_district": None
    },
    {
        "id": 6,
        "title": "Proposed vs approved for programme",
        "query": "How much was proposed versus approved for Maternal Health programme in Maharashtra?",
        "expected_district": None
    },
    {
        "id": 7,
        "title": "Nanded allocation recommendation",
        "query": "Recommend a planning allocation for Nanded using available historical and healthcare indicators.",
        "expected_district": "Nanded"
    },
    {
        "id": 8,
        "title": "Allocate 100 crore under constraints",
        "query": "How should an additional ₹100 crore be allocated under explicit constraints?",
        "expected_district": None
    },
    {
        "id": 9,
        "title": "Programme prioritization",
        "query": "Which healthcare programmes need prioritization based on the available evidence?",
        "expected_district": None
    },
    {
        "id": 10,
        "title": "Official source check",
        "query": "Show the official source for Maharashtra healthcare budget allocations in 2025-26.",
        "expected_district": None
    },
    {
        "id": 11,
        "title": "PIP vs ROP explanation",
        "query": "Explain the difference between PIP proposal and ROP approval.",
        "expected_district": None
    },
    {
        "id": 12,
        "title": "Infrastructure and staffing gaps",
        "query": "Summarize health infrastructure and staffing gaps in Gadchiroli district.",
        "expected_district": "Gadchiroli"
    },
    {
        "id": 13,
        "title": "Compare maternal health funding",
        "query": "Compare Thane and Palghar maternal health funding.",
        "expected_district": "Thane"
    },
    {
        "id": 14,
        "title": "Hindi query test",
        "query": "नांदेड़ जिले के लिए स्वास्थ्य बजट कितना आवंटित किया गया है?",
        "expected_district": "Nanded"
    },
    {
        "id": 15,
        "title": "Hinglish funding recommendation",
        "query": "Maharashtra ke tribal districts ke liye 50 crore ka healthcare allocation kaise karein?",
        "expected_district": None
    }
]

def run_tests():
    print("=================================================================")
    print("AI SARTHI — LIVE END-TO-END TEST SUITE EXECUTION")
    print("=================================================================")
    
    # 1. Health check
    code, h = http_get(f"{BASE_URL}/health")
    print(f"Server Health: {h}")
    assert h["status"] == "ok"
    
    # 2. Districts check
    code, d = http_get(f"{BASE_URL}/api/districts")
    print(f"Total Districts Verified: {d.get('total')}")
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    results = []
    
    for q in QUESTIONS:
        qid = q["id"]
        title = q["title"]
        query = q["query"]
        
        start_t = time.time()
        status_code, data = http_post(f"{BASE_URL}/api/chat", {"question": query})
        elapsed = time.time() - start_t
        
        intent = data.get("intent", "UNKNOWN")
        entities = data.get("entities", {})
        identified_district = entities.get("district")
        answer_text = data.get("answer", "") or data.get("response", "")
        sources = data.get("sources", [])
        sql_rows = len(data.get("sql_results", [])) if "sql_results" in data else (1 if data.get("sql_used") else 0)
        rag_passages = len(data.get("evidence", [])) if "evidence" in data else (1 if data.get("rag_used") else 0)
        
        passed = (status_code == 200 and len(answer_text) > 20)
        
        res = {
            "id": qid,
            "title": title,
            "status": "PASS" if passed else "FAIL",
            "status_code": status_code,
            "intent": intent,
            "district_identified": identified_district,
            "sources_count": len(sources),
            "rag_passages": rag_passages,
            "sql_rows": sql_rows,
            "elapsed_s": round(elapsed, 2),
            "snippet": answer_text[:160].replace("\n", " ") + "..."
        }
        results.append(res)
        
        print(f"\n[Test {qid:02d}] {title}")
        print(f"  Query: {query}")
        print(f"  Status: {res['status']} ({res['elapsed_s']}s) | Intent: {intent} | District: {identified_district}")
        print(f"  Sources: {len(sources)} | RAG Chunks: {rag_passages} | SQL Rows: {sql_rows}")
        print(f"  Snippet: {res['snippet']}")
        
    print("\n=================================================================")
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    print(f"TOTAL TESTS: {len(results)} | PASSED: {passed_count} | FAILED: {len(results) - passed_count}")
    print("=================================================================")
    
    with open("live_test_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Saved live_test_report.json")

if __name__ == "__main__":
    run_tests()
