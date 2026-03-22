from pathlib import Path
import re

TEMPLATE_DIR = Path('templates')
logo_css = '''.logo-box {
            width: 77px; height: 77px;
            min-width: 77px; min-height: 77px;
            display: inline-flex; align-items: center; justify-content: center;
            border-radius: 16px;
            object-fit: contain;
            margin-top: -10px; margin-bottom: -10px;
        }'''

for f in TEMPLATE_DIR.glob('*.html'):
    text = f.read_text(encoding='utf-8')
    updated = re.sub(r'\.logo-box\s*\{[^}]*\}', logo_css, text, flags=re.DOTALL)
    if updated != text:
        f.write_text(updated, encoding='utf-8')
        print('updated', f.name)
