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
            height: 56px;
            position: sticky;
            top: 0;
            z-index: 1000;
            border-bottom: 1px solid var(--glass-border);
        }'''

logo_css = '''.logo-box {
            width: 72px; height: 72px;
            min-width: 72px; min-height: 72px;
            display: inline-flex; align-items: center; justify-content: center;
            border-radius: 16px;
            object-fit: contain;
            margin-top: -8px; margin-bottom: -8px;
        }'''

for f in TEMPLATE_DIR.glob('*.html'):
    text=f.read_text(encoding='utf-8')
    updated=text
    updated=re.sub(r'#topbar\s*\{[^}]*\}', topbar_css, updated, flags=re.DOTALL)
    updated=re.sub(r'\.logo-box\s*\{[^}]*\}', logo_css, updated, flags=re.DOTALL)
    if updated!=text:
        f.write_text(updated, encoding='utf-8')
        print('updated', f.name)
