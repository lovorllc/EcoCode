import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main
client = TestClient(main.app)
r = client.get('/signup')
print('status', r.status_code)
print('contains 123456789?', '123456789' in r.text)
print(r.text[r.text.find('phone-input')-200:r.text.find('phone-input')+200])
