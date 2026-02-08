import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main
client = TestClient(main.app)

# Login as admin
client.post('/login', data={'who':'admin','password':'admin'})
# get admin id
r = client.get('/api/users')
users = r.json().get('users', [])
admin = [u for u in users if u.get('username') == 'admin'][0]
admin_id = admin.get('id')

r1 = client.get(f'/api/users/{admin_id}/daily_co2')
print('/api/users/{}/daily_co2 (default hour) ->'.format(admin_id), r1.status_code)
print('hours count:', len(r1.json().get('hours',[])))

r1b = client.get(f'/api/users/{admin_id}/daily_co2?range=hour')
print('/api/users/{}/daily_co2?range=hour ->'.format(admin_id), r1b.status_code)
print('hours count (explicit):', len(r1b.json().get('hours',[])))

r_week = client.get(f'/api/users/{admin_id}/daily_co2?range=week')
print('/api/users/{}/daily_co2?range=week ->'.format(admin_id), r_week.status_code)
print('points count (week):', len(r_week.json().get('points',[])))

r_month = client.get(f'/api/users/{admin_id}/daily_co2?range=month')
print('/api/users/{}/daily_co2?range=month ->'.format(admin_id), r_month.status_code)
print('points count (month):', len(r_month.json().get('points',[])))

r_year = client.get(f'/api/users/{admin_id}/daily_co2?range=year')
print('/api/users/{}/daily_co2?range=year ->'.format(admin_id), r_year.status_code)
print('points count (year):', len(r_year.json().get('points',[])))

r2 = client.get(f'/api/users/{admin_id}/eco_scores')
print('/api/users/{}/eco_scores (week) ->'.format(admin_id), r2.status_code)
print('scores (week) length:', len(r2.json().get('scores',[])))

r3 = client.get(f'/eco-score')
print('GET /eco-score ->', r3.status_code)

r4 = client.get('/daily-co2')
print('GET /daily-co2 ->', r4.status_code)