import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient
import main
client = TestClient(main.app)
# Signup with 9-digit national phone
r = client.post('/signup', data={'name':'Nine','email':'nine@example.com','country':'HR','phone':'123456789','username':'nine1','password':'Strong1!','password_confirm':'Strong1!'}, follow_redirects=False)
print('/signup nine ->', r.status_code, r.headers.get('location'))
row = main.db.connect().cursor().execute('SELECT phone, phone_e164 FROM users WHERE username = ?', ('nine1',)).fetchone()
print('stored phone / e164:', row)
