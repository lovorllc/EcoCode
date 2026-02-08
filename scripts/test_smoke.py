import sys, pathlib
# Ensure project root is on sys.path
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main
print('main imported, db methods:', [m for m in dir(main.db) if not m.startswith('_')])
client = TestClient(main.app)
r_root = client.get('/')
print('GET / ->', r_root.status_code, r_root.text[:200])
r_users = client.get('/users')
print('GET /users ->', r_users.status_code, r_users.text[:200])
# try signup
resp = client.post('/signup', data={'name':'Smoke','email':'smoke@example.com','phone':'000','username':'smoke','password':'Strong1!','password_confirm':'Strong1!'}, follow_redirects=False)
print('/signup ->', resp.status_code, resp.headers.get('location'))
print('user smoke in db:', main.db.connect().cursor().execute('SELECT * FROM users WHERE username = ?', ('smoke',)).fetchone())
# try auth register (JSON body)
resp2 = client.post('/auth/register', json={'username':'apiuser','email':'api@example.com','password':'Strong1!'})
print('/auth/register ->', resp2.status_code, resp2.json() if resp2.status_code==200 else resp2.text)
print('apiuser in db:', main.db.connect().cursor().execute('SELECT * FROM users WHERE username = ?', ('apiuser',)).fetchone())

# Test /login (form) for 'smoke'
r3 = client.post('/login', data={'username':'smoke','password':'pwd'}, follow_redirects=False)
print('/login ->', r3.status_code, r3.headers.get('location'))

# Test /auth/login (OAuth2 password flow) for 'apiuser'
r4 = client.post('/auth/login', data={'username':'apiuser','password':'pwd'})
print('/auth/login ->', r4.status_code, r4.json() if r4.status_code==200 else r4.text)

# Test phone normalization for Croatia examples
r5 = client.post('/signup', data={'name':'Cro1','email':'cro1@example.com','country':'HR','phone':'123456789','username':'cro1','password':'Strong1!','password_confirm':'Strong1!'}, follow_redirects=False)
print('/signup cro1 ->', r5.status_code, r5.headers.get('location'))
print('cro1 response text (short):', r5.text[:300])
row = main.db.connect().cursor().execute('SELECT phone, phone_e164 FROM users WHERE username = ?', ('cro1',)).fetchone()
print('cro1 stored phone / e164:', row)

r6 = client.post('/signup', data={'name':'Cro2','email':'cro2@example.com','country':'HR','phone':'123456789','username':'cro2','password':'Strong1!','password_confirm':'Strong1!'}, follow_redirects=False)
print('/signup cro2 ->', r6.status_code, r6.headers.get('location'))
print('cro2 response text (short):', r6.text[:300])
row2 = main.db.connect().cursor().execute('SELECT phone, phone_e164 FROM users WHERE username = ?', ('cro2',)).fetchone()
print('cro2 stored phone / e164:', row2)

# Try a bad phone (should render the signup page with an error)
r_bad = client.post('/signup', data={'name':'Bad','email':'bad@example.com','country':'HR','phone':'123','username':'bad','password':'Strong1!','password_confirm':'Strong1!'}, follow_redirects=False)
print('/signup bad ->', r_bad.status_code)
print('bad signup response snippet:', r_bad.text[:200])

# Try weak password (should be rejected)
r_weak = client.post('/signup', data={'name':'Weak','email':'weak@example.com','country':'HR','phone':'0996662838','username':'weakuser','password':'pwd','password_confirm':'pwd'}, follow_redirects=False)
print('/signup weak ->', r_weak.status_code)
print('weak signup contains password message?', 'Password must' in r_weak.text or 'Password is required' in r_weak.text)

