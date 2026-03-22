from pathlib import Path
import re

TEMPLATE_DIR = Path('templates')

logo_html = '<a href="/" class="logo"><img src="/static/logo.png" alt="EcoCode" class="logo-box"> EcoCode</a>'

for f in TEMPLATE_DIR.glob('*.html'):
    text = f.read_text(encoding='utf-8')
    modified=False

    # ensure topbar anchor has image
    def replace_logo(match):
        nonlocal modified
        block = match.group(0)
        if '/static/logo.png' in block:
            return block
        modified=True
        return logo_html

    text_new = re.sub(r'<a\s+href="/"\s+class="logo">.*?</a>', replace_logo, text, flags=re.DOTALL)
    text = text_new

    # normalize logo-box css block
    new_css = '''.logo-box {
            width: 40px; height: 40px;
            display: inline-flex; align-items: center; justify-content: center;
            border-radius: 12px;
            object-fit: contain;
        }'''

    text_new, n = re.subn(r'\.logo-box\s*\{[^}]*\}', new_css, text, flags=re.DOTALL)
    if n > 0 and text_new != text:
        text = text_new
        modified=True

    if modified:
        f.write_text(text, encoding='utf-8')
        print(f'Updated {f.name}')

