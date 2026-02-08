import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main
client = TestClient(main.app)

# Create admin via /users/new
r = client.post('/users/new', data={'name':'Admin1','country':'US','phone':'123456789','username':'admin1','email':'admin1@example.com','password':'Strong1!','user_type':'admin'}, follow_redirects=False)
print('/users/new ->', r.status_code, 'location:', r.headers.get('location'))
# Fetch users
r2 = client.get('/users')
print('/users list status', r2.status_code)
print('contains admin1?', 'admin1' in r2.text)

# Try login via email
r3 = client.post('/login', data={'who':'admin1@example.com','password':'Strong1!'}, follow_redirects=False)
print('/login via email ->', r3.status_code, r3.headers.get('location'))
# Try login via username
r4 = client.post('/login', data={'who':'admin1','password':'Strong1!'}, follow_redirects=False)
print('/login via username ->', r4.status_code, r4.headers.get('location'))
# Try login via phone
r5 = client.post('/login', data={'who':'123456789','password':'Strong1!'}, follow_redirects=False)
print('/login via phone ->', r5.status_code, r5.headers.get('location'))
