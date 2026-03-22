from pathlib import Path
import re

TEMPLATE_DIR = Path('templates')
logo_css = '''.logo {
            font-weight: 800; font-size: 1.5rem; color: var(--text-main);
            text-decoration: none; display: flex; align-items: center; gap: -10px;
        }'''

for f in TEMPLATE_DIR.glob('*.html'):
    text = f.read_text(encoding='utf-8')
    updated = re.sub(r'\.logo\s*\{[^}]*\}', logo_css, text, flags=re.DOTALL)
    if updated != text:
        f.write_text(updated, encoding='utf-8')
        print('updated', f.name)
