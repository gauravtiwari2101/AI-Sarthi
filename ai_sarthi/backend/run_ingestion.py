import sys
sys.path.insert(0, '.')
from etl.ingest import run_ingestion
results = run_ingestion()
print()
print('=== QUALITY RESULTS ===')
for r in results:
    status = r['status']
    check = r['check']
    msg = r['message']
    print(f'  [{status}] {check}: {msg}')
