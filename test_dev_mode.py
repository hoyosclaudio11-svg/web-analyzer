"""Test DEV_MODE download bypass."""
import sys, os
sys.path.insert(0, 'E:/DelMonte/web-analyzer')

# Simulate loading .env before app import
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('E:/DelMonte/web-analyzer/.env'))

from app import app

client = app.test_client()

# Analyze
resp = client.post('/api/analyze', json={'url': 'google.com'})
data = resp.get_json()
print(f'Analysis: {resp.status_code}, hash={data.get("report_hash")}')

# Try download
sols = data.get('soluciones', [])
zip_sol = [s for s in sols if s['tipo'] == 'zip']
if zip_sol:
    name = zip_sol[0]['nombre']
    rhash = data['report_hash']
    print(f'Download: {name}?report_hash={rhash}')
    resp2 = client.get(f'/api/download/{name}?report_hash={rhash}')
    print(f'Status: {resp2.status_code}')
    if resp2.status_code == 200:
        print(f'OK: {len(resp2.data)} bytes')
    else:
        print(f'Error: {resp2.get_json()}')
else:
    print('No zip in solutions')
