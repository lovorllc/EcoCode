from pathlib import Path
import re

TEMPLATE_DIR = Path('templates')
logo_html = '<a href="/" class="logo"><img src="/static/logo.png" alt="EcoCode" class="logo-box"> EcoCode</a>'

for f in TEMPLATE_DIR.glob('*.html'):
    text = f.read_text(encoding='utf-8')
    if '/static/logo.png' not in text and '<a href="/" class="logo">' in text:
        text_new = re.sub(r'<a href="/" class="logo">\s*.*?\s*</a>', logo_html, text, flags=re.DOTALL, count=1)
        if text_new != text:
            # also update css block
            text_new = re.sub(r'\.logo-box\s*\{[^}]*\}', '''.logo-box {\n            width: 40px; height: 40px;\n            display: inline-flex; align-items: center; justify-content: center;\n            border-radius: 12px;\n            object-fit: contain;\n        }''', text_new, flags=re.DOTALL)
            f.write_text(text_new, encoding='utf-8')
            print('Updated', f.name)

