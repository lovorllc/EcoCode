from pathlib import Path
import re

TEMPLATE_DIR = Path('templates')

def fix_topbar_css(text):
    # set smaller topbar padding while retaining existing styling
    return re.sub(r'#topbar\s*\{[^}]*\}', '#topbar {\n            background: var(--card-bg);\n            backdrop-filter: blur(15px);\n            display: flex;\n            justify-content: space-between;\n            align-items: center;\n            padding: 0.5rem 4%;\n            position: sticky;\n            top: 0;\n            z-index: 1000;\n            border-bottom: 1px solid var(--glass-border);\n        }', text, flags=re.DOTALL)

for f in TEMPLATE_DIR.glob('*.html'):
    text = f.read_text(encoding='utf-8')
    updated = fix_topbar_css(text)
    if updated != text:
        f.write_text(updated, encoding='utf-8')
        print('updated', f.name)
