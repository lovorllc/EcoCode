from pathlib import Path
import re

TEMPLATE_DIR = Path('templates')

topbar_css = '''#topbar {
            background: var(--card-bg);
            backdrop-filter: blur(15px);
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 4%;
            height: 66px;
            position: sticky;
            top: 0;
            z-index: 1000;
            border-bottom: 1px solid var(--glass-border);
        }'''

for f in TEMPLATE_DIR.glob('*.html'):
    text = f.read_text(encoding='utf-8')
    updated = re.sub(r'#topbar\s*\{[^}]*\}', topbar_css, text, flags=re.DOTALL)
    if updated != text:
        f.write_text(updated, encoding='utf-8')
        print('updated', f.name)
