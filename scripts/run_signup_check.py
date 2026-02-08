import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main
client = TestClient(main.app)

# test invalid phone
r = client.post('/signup', data={'name':'Bad','email':'bad123@example.com','country':'HR','phone':'123','username':'bad123','password':'Strong1!','password_confirm':'Strong1!'}, follow_redirects=False)
print('status', r.status_code)
print('contains phone error?', 'Phone number must' in r.text)
print('error msg snippet:', r.text[:400])

# test short phone '000'
r2 = client.post('/signup', data={'name':'Smoke2','email':'smoke2@example.com','country':'HR','phone':'000','username':'smoke2','password':'Strong1!','password_confirm':'Strong1!'}, follow_redirects=False)
print('status 000', r2.status_code)
print('contains phone error?', 'Phone number must' in r2.text or 'Invalid phone number' in r2.text)
print('r2 text snippet:', r2.text[:400])

# test valid 9-digit phone
r3 = client.post('/signup', data={'name':'Good','email':'good1@example.com','country':'HR','phone':'123456789','username':'good1','password':'Strong1!','password_confirm':'Strong1!'}, follow_redirects=False)
print('status good', r3.status_code)
print('redirect?', r3.headers.get('location'))

