import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main, datetime
client = TestClient(main.app)

# Login as admin
client.post('/login', data={'who':'admin','password':'admin'})
# get admin id
r = client.get('/api/users')
users = r.json().get('users', [])
admin = [u for u in users if u.get('username') == 'admin'][0]
admin_id = admin.get('id')

# Clear admin activities
with main.db.connect() as conn:
    cur = conn.cursor()
    cur.execute('DELETE FROM activities WHERE user_id = ?', (admin_id,))
    conn.commit()

# Insert activities for today, yesterday, and day-before-yesterday
today = datetime.date.today()
dates = [today - datetime.timedelta(days=i) for i in range(3)]
with main.db.connect() as conn:
    cur = conn.cursor()
    for d in dates:
        cur.execute("INSERT INTO activities (user_id, category, subtype, co2_kg, note, quantity, unit, created_at) VALUES (?,?,?,?,?,?,?,?)",
                    (admin_id, 'Transport', 'car', 1.0, 'test', 1.0, 'trip', d.isoformat() + ' 12:00:00'))
    conn.commit()

r = client.get('/api/metrics')
print('GET /api/metrics ->', r.status_code)
metrics = r.json().get('metrics', {})
print('streak_days ->', metrics.get('streak_days'))
print('achievements ->', metrics.get('achievements'))
print('last7 ->', metrics.get('last7'))

# Basic assertion
if metrics.get('streak_days') != 3:
    print('Test failed: expected streak_days == 3')
    sys.exit(2)
print('Test passed')
