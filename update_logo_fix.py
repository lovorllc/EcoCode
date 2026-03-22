from pathlib import Path
import re

TEMPLATE_DIR=Path('templates')
logo_html='<a href="/" class="logo"><img src="/static/logo.png" alt="EcoCode" class="logo-box"> EcoCode</a>'

for f in TEMPLATE_DIR.glob('*.html'):
    text=f.read_text(encoding='utf-8')
    updated=text

    # Replace any existing logo anchor block with standardized html
    updated=re.sub(r'<a\s+href="/"\s+class="logo">.*?</a>', logo_html, updated, flags=re.DOTALL)

    # Ensure .logo-box style exists and correct
    updated=re.sub(r'\.logo-box\s*\{[^}]*\}', '.logo-box {\n            width: 40px; height: 40px;\n            display: inline-flex; align-items: center; justify-content: center;\n            border-radius: 12px;\n            object-fit: contain;\n        }', updated, flags=re.DOTALL)

    if updated != text:
        f.write_text(updated, encoding='utf-8')
        print('updated', f.name)

