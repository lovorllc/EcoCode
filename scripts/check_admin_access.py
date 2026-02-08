import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main
client = TestClient(main.app)

# Ensure admin exists (create directly if needed)
with main.db.connect() as conn:
    cur = conn.cursor()
    row = cur.execute('SELECT id FROM users WHERE username = ?', ('admin1',)).fetchone()
    if not row:
        pwd = main.pwd_context.hash('Strong1!')
        cur.execute('INSERT INTO users (username, email, name, phone, phone_e164, password_hash, user_type) VALUES (?,?,?,?,?,?,?)', ('admin1','admin1@example.com','Admin One','123456789','+1123456789',pwd,'admin'))
        conn.commit()

# Login as admin
r = client.post('/login', data={'who': 'admin1', 'password': 'Strong1!'}, follow_redirects=False)
print('login admin ->', r.status_code, r.headers.get('location'))
# Access devtools (should be allowed)
r2 = client.get('/devtools', follow_redirects=False)
print('GET /devtools as admin ->', r2.status_code)
# Access users (should be allowed)
r3 = client.get('/users', follow_redirects=False)
print('GET /users as admin ->', r3.status_code)

# Create a normal user and test access denied
with main.db.connect() as conn:
    cur = conn.cursor()
    row = cur.execute('SELECT id FROM users WHERE username = ?', ('user1',)).fetchone()
    if not row:
        pwd = main.pwd_context.hash('Strong1!')
        cur.execute('INSERT INTO users (username, email, name, phone, phone_e164, password_hash, user_type) VALUES (?,?,?,?,?,?,?)', ('user1','user1@example.com','User One','123456780','+1123456780',pwd,'user'))
        conn.commit()
# Login as user
r4 = client.post('/login', data={'who': 'user1', 'password': 'Strong1!'}, follow_redirects=False)
print('login user ->', r4.status_code, r4.headers.get('location'))
ru = client.get('/devtools', follow_redirects=False)
print('GET /devtools as user ->', ru.status_code, 'contains contact msg?', 'Contact admin to gain access' in ru.text)
ru2 = client.get('/users', follow_redirects=False)
print('GET /users as user ->', ru2.status_code, ru2.headers.get('location'))
