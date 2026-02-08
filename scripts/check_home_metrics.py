import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main
client = TestClient(main.app)

# Login as admin
client.post('/login', data={'who':'admin','password':'admin'})
# find admin id
r = client.get('/api/users')
users = r.json().get('users', [])
admin = [u for u in users if u.get('username') == 'admin'][0]
admin_id = admin.get('id')

r2 = client.get(f'/api/users/{admin_id}/metrics')
print('/api/users/{}/metrics ->'.format(admin_id), r2.status_code)
if r2.status_code == 200:
    data = r2.json()
    print('keys:', sorted(data.keys()))
    print('daily_co2:', data.get('daily_co2'))
    print('last7 len:', len(data.get('last7', [])))
else:
    print('body:', r2.text)