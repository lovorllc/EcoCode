from pathlib import Path
import re

TEMPLATE_DIR = Path('templates')
logo_css = '''.logo-box {
            width: 56px; height: 56px;
            display: inline-flex; align-items: center; justify-content: center;
            border-radius: 14px;
            object-fit: contain;
        }'''

for f in TEMPLATE_DIR.glob('*.html'):
    text = f.read_text(encoding='utf-8')
    updated = re.sub(r'\.logo-box\s*\{[^}]*\}', logo_css, text, flags=re.DOTALL)
    if updated != text:
        f.write_text(updated, encoding='utf-8')
        print('updated', f.name)
