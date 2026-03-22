from pathlib import Path
import re

TEMPLATE_DIR = Path('templates')
files = list(TEMPLATE_DIR.glob('*.html'))
for f in files:
    text = f.read_text(encoding='utf-8')
    changed = False

    old = '<div class="logo-box">EC</div>'
    new = '<img src="/static/logo.png" alt="EcoCode" class="logo-box">'
    if old in text:
        text = text.replace(old, new)
        changed = True

    pattern = re.compile(r'<div class="logo-box">.*?</div>', re.DOTALL)
    if pattern.search(text):
        text_new = pattern.sub(new, text)
        if text_new != text:
            text = text_new
            changed = True

    css_pattern = re.compile(r'\.logo-box\s*\{[^}]*\}', re.DOTALL)
    match = css_pattern.search(text)
    if match:
        new_css = '''.logo-box {
            width: 40px; height: 40px;
            display: inline-flex; align-items: center; justify-content: center;
            border-radius: 12px;
            object-fit: contain;
        }'''
        text_new = text[:match.start()] + new_css + text[match.end():]
        if text_new != text:
            text = text_new
            changed = True

    if changed:
        f.write_text(text, encoding='utf-8')
        print('Updated', f.name)
