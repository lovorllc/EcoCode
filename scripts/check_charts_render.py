import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main
client = TestClient(main.app)

# Login
client.post('/login', data={'who':'admin','password':'admin'})
# Check daily-co2 page
r = client.get('/daily-co2')
print('/daily-co2 ->', r.status_code, 'has canvas?', '<canvas id="dailyChart"' in r.text)
# Check eco-score page
r2 = client.get('/eco-score')
print('/eco-score ->', r2.status_code, 'has canvas?', '<canvas id="scoreChart"' in r2.text)
# Check Track page
r3 = client.get('/track')
print('/track ->', r3.status_code, 'has Track text?', 'Track your activities' in r3.text)
# Check that Chart.js is included in both pages
print('chart.js in daily:', 'cdn.jsdelivr.net/npm/chart.js' in client.get('/daily-co2').text)
print('chart.js in score:', 'cdn.jsdelivr.net/npm/chart.js' in client.get('/eco-score').text)