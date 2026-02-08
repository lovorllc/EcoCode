import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main
client = TestClient(main.app)

# login as admin
client.post('/login', data={'who':'admin','password':'admin'})

# ensure empty list starts
r = client.get('/api/activities')
print('/api/activities ->', r.status_code, 'count:', len(r.json().get('activities', [])))

# add a transport activity
r1 = client.post('/api/activities', data={'category':'Transport','subtype':'car','co2_kg':'2.5','note':'Test drive'})
print('/api/activities POST ->', r1.status_code, r1.json())

# add a food activity
r2 = client.post('/api/activities', data={'category':'Food','subtype':'meat','co2_kg':'1.2','note':'Beef meal'})
print('/api/activities POST ->', r2.status_code, r2.json())

# list activities
r3 = client.get('/api/activities')
acts = r3.json().get('activities', [])
print('/api/activities GET ->', r3.status_code, 'count:', len(acts))
for a in acts[:5]:
    print(a)

# ensure co2 totals reflection
total = sum([float(a.get('co2_kg') or 0) for a in acts])
print('Total co2 in activities:', total)