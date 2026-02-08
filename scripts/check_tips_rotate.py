import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main
client = TestClient(main.app)

# Login as user (admin available)
r1 = client.post('/login', data={'who':'admin','password':'admin'}, follow_redirects=False)
print('first login ->', r1.status_code, r1.headers.get('location'))
home1 = client.get('/')
# extract first set of tips
import re
matches = re.findall(r'<ul>\s*(?:<li>(.*?)</li>\s*){1,3}', home1.text, re.S)
# simpler: look for the Today's tips section and extract li text
# Simple HTML parsing without extra dependency
import re
# find the Today's tips ul by header
m = re.search(r"<h4>Today(?:'s)? tips</h4>\s*<ul>(.*?)</ul>", home1.text, re.S|re.I)
if m:
    ul = m.group(1)
    tips1 = re.findall(r"<li>(.*?)</li>", ul, re.S)
else:
    # fallback: take first three li in main
    tips1 = re.findall(r"<main[\s\S]*?<ul>([\s\S]*?)</ul>", home1.text, re.S)
    if tips1:
        tips1 = re.findall(r"<li>(.*?)</li>", tips1[0], re.S)[:3]
    else:
        tips1 = []
print('tips1:', [t.strip() for t in tips1])

# logout and login again to get new tips
client.get('/logout')
r2 = client.post('/login', data={'who':'admin','password':'admin'}, follow_redirects=False)
print('second login ->', r2.status_code, r2.headers.get('location'))
home2 = client.get('/')
m2 = re.search(r"<h4>Today(?:'s)? tips</h4>\s*<ul>(.*?)</ul>", home2.text, re.S|re.I)
if m2:
    ul2 = m2.group(1)
    tips2 = re.findall(r"<li>(.*?)</li>", ul2, re.S)
else:
    tips2 = []
print('tips2:', [t.strip() for t in tips2])
print('different?', [t.strip() for t in tips1] != [t.strip() for t in tips2])