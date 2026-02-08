import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient
import main
c = TestClient(main.app)
# Login as admin
resp = c.post('/login', data={'who':'admin','password':'admin'})
print('login status', resp.status_code)
# after login request, fetch users
r = c.get('/users')
print('status', r.status_code)
print('response length', len(r.text))
# print first 800 chars for debugging
print(r.text[:800])
print('Has Last Active column?', 'Last Active' in r.text)
