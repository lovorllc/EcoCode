from pathlib import Path
import re

TEMPLATE_DIR = Path('templates')

logo_css = '''.logo {
            font-weight: 800; font-size: 1.5rem; color: var(--text-main);
            text-decoration: none; display: flex; align-items: center; gap: 0px;
        }'''

logo_box_css = '''.logo-box {
            width: 95px; height: 95px;
            min-width: 95px; min-height: 95px;
            display: inline-flex; align-items: center; justify-content: center;
            border-radius: 16px;
            object-fit: contain;
            margin-top: -10px; margin-bottom: -10px;
        }'''

for f in TEMPLATE_DIR.glob('*.html'):
    text = f.read_text(encoding='utf-8')
    updated = text
    updated = re.sub(r'\.logo\s*\{[^}]*\}', logo_css, updated, flags=re.DOTALL)
    updated = re.sub(r'\.logo-box\s*\{[^}]*\}', logo_box_css, updated, flags=re.DOTALL)
    if updated != text:
        f.write_text(updated, encoding='utf-8')
        print('updated', f.name)
