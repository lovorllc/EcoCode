import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main
from database import Database
from passlib.context import CryptContext

client = TestClient(main.app)

pwd = CryptContext(schemes=["bcrypt"])  # use same schemes

# login as admin
client.post('/login', data={'who':'admin','password':'admin'})

# create activity as admin
r = client.post('/api/activities', data={'category':'Transport','subtype':'car','quantity':'3'})
print('Admin POST activity ->', r.status_code, r.json())
act_id = r.json().get('id')

# delete as admin (should work)
r2 = client.post(f'/api/activities/{act_id}/delete')
print('Admin delete ->', r2.status_code, r2.json())

# create a normal user and login as them
# create a user via signup endpoint
username = 'deleter_user'
resp = client.post('/signup', data={'name':'Deleter','email':'deleter@example.com','phone':'123456789','username':username,'password':'Strong1!','password_confirm':'Strong1!'})
print('/signup ->', resp.status_code)
# login as normal user
client.post('/login', data={'who': username, 'password': 'Strong1!'})

# create activity as normal user
r3 = client.post('/api/activities', data={'category':'Food','subtype':'beef','quantity':'1'})
print('User POST activity ->', r3.status_code, r3.json())
user_act_id = r3.json().get('id')

# delete own activity (should work)
r4 = client.post(f'/api/activities/{user_act_id}/delete')
print('User delete own ->', r4.status_code, r4.json())

# ensure cannot delete other user's activity
# re-login as admin to create an activity
client.post('/login', data={'who':'admin','password':'admin'})
r5 = client.post('/api/activities', data={'category':'Food','subtype':'pork','quantity':'1'})
other_id = r5.json().get('id')
print('Admin created another ->', r5.status_code, r5.json())

# login as deleter_user
client.post('/login', data={'who': username, 'password': 'Strong1!'})
# list activities to inspect owner
r_list = client.get('/api/activities')
print('Activities snapshot count', len(r_list.json().get('activities', [])))
for a in r_list.json().get('activities', [])[:5]:
    print('act', a.get('id'), 'user_id', a.get('user_id'))

# attempt delete by non-owner
r6 = client.post(f'/api/activities/{other_id}/delete')
print('User deleting others ->', r6.status_code, r6.json())