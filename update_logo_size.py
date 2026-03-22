from pathlib import Path
import re

TEMPLATE_DIR=Path('templates')

for f in TEMPLATE_DIR.glob('*.html'):
    text=f.read_text(encoding='utf-8')
    new_text=re.sub(r'\.logo-box\s*\{[^}]*\}', '.logo-box {\n            width: 56px; height: 56px;\n            display: inline-flex; align-items: center; justify-content: center;\n            border-radius: 12px;\n            object-fit: contain;\n        }', text, flags=re.DOTALL)
    if new_text!=text:
        f.write_text(new_text, encoding='utf-8')
        print('updated', f.name)

