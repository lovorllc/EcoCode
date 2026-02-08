import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main
client = TestClient(main.app)

# Login as admin and fetch home
client.post('/login', data={'who':'admin','password':'admin'})
r = client.get('/')
print('GET / ->', r.status_code)
print('daily-co2 link present?', 'href="/daily-co2"' in r.text)
print('eco-score link present?', 'href="/eco-score?range=week"' in r.text)