import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main
client = TestClient(main.app)

# login as admin
client.post('/login', data={'who':'admin','password':'admin'})

# post using quantity for transport car (5 km) -> expected ~1.05 kg
r = client.post('/api/activities', data={'category':'Transport','subtype':'car','quantity':'5'})
print('POST by quantity ->', r.status_code, r.json())

# post using quantity for electricity (10 kWh) -> expected ~2.33 kg
r2 = client.post('/api/activities', data={'category':'Electricity','quantity':'10'})
print('POST electricity ->', r2.status_code, r2.json())

# list and print totals
r3 = client.get('/api/activities')
acts = r3.json().get('activities', [])
print('/api/activities count', len(acts))
print('Totals:', sum([float(a.get('co2_kg') or 0) for a in acts]))