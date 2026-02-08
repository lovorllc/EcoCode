import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main
client = TestClient(main.app)

# Ensure admin exists
r = client.get('/users')
print('GET /users ->', r.status_code)
# Login as admin to perform operations
client.post('/login', data={'who':'admin','password':'admin'})
# Confirm admin present via API
r2 = client.get('/api/users')
print('GET /api/users ->', r2.status_code, 'content-type:', r2.headers.get('content-type'))
users = []
if r2.headers.get('content-type','').startswith('application/json'):
    users = r2.json().get('users', [])
else:
    print('api users response (non-json):', r2.text[:200])
admin = [u for u in users if u.get('username') == 'admin']
print('admin present?', bool(admin))
admin_id = admin[0]['id'] if admin else None
# Try to delete admin
if admin_id:
    r3 = client.post(f'/users/{admin_id}/delete', follow_redirects=False)
    print('attempt delete admin ->', r3.status_code, r3.headers.get('location'))

# Try to change admin type via edit (should remain admin)
if admin_id:
    r4 = client.post(f'/users/{admin_id}/edit', data={'name':'Admin Edit','username':'admin','email':'','user_type':'user'}, follow_redirects=False)
    print('attempt change admin type ->', r4.status_code, r4.headers.get('location'))
    # fetch admin row again to confirm type
    r5 = client.get('/api/users')
    users2 = []
    if r5.headers.get('content-type','').startswith('application/json'):
        users2 = r5.json().get('users', [])
    else:
        print('non-json /api/users after edit:', r5.status_code)
    admin2 = [u for u in users2 if u.get('username') == 'admin']
    print('admin type after edit:', admin2[0].get('user_type') if admin2 else None)

# Check new user creation with permanent flag
r_new = client.post('/users/new', data={'name':'Perm User','username':'permuser','email':'perm@example.com','password':'Pass1234!','user_type':'user','permanent':'1'}, follow_redirects=False)
print('create perm user ->', r_new.status_code, 'location:', r_new.headers.get('location'))
print('create response body snippet:', r_new.text[:2000])
if r_new.status_code != 303 and r_new.status_code != 200:
    print('create response body (full):', r_new.text)
# find the new user via API
r6 = client.get('/api/users')
if r6.headers.get('content-type','').startswith('application/json'):
    users3 = r6.json().get('users', [])
else:
    print('/api/users non-json after create:', r6.status_code)
    users3 = []
perm = [u for u in users3 if u.get('username') == 'permuser']
print('perm user present?', bool(perm), 'permanent flag:', perm[0].get('permanent') if perm else None)
perm_id = perm[0]['id'] if perm else None
# Attempt to delete permanent user
if perm_id:
    # First, fetch the confirmation page
    r_confirm = client.get(f'/users/{perm_id}/delete')
    print('GET confirm delete page ->', r_confirm.status_code, 'has prompt?', 'Admin password' in r_confirm.text)
    # Try with wrong password
    r_wrong = client.post(f'/users/{perm_id}/delete', data={'admin_password':'wrongpass'}, follow_redirects=False)
    print('attempt delete perm user (wrong pwd) ->', r_wrong.status_code)
    # Now try with the correct admin password
    r_ok = client.post(f'/users/{perm_id}/delete', data={'admin_password':'admin'}, follow_redirects=False)
    print('attempt delete perm user (correct pwd) ->', r_ok.status_code, r_ok.headers.get('location'))
    print('response snippet:', r_ok.text[:400])
    # fetch to confirm deletion
    r_after = client.get('/api/users')
    users_after = r_after.json().get('users', []) if r_after.headers.get('content-type','').startswith('application/json') else []
    perm_after = [u for u in users_after if u.get('username') == 'permuser']
    print('perm user still present after delete?', bool(perm_after))
# Check that the create page shows the permanent checkbox for admins
r_new_page = client.get('/users/new')
print('GET /users/new ->', r_new_page.status_code)
if r_new_page.status_code == 200:
    print('has permanent checkbox?', 'Permanent account' in r_new_page.text)
else:
    print('GET /users/new body:', r_new_page.text[:400])
