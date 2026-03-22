from pathlib import Path
T = Path('templates')
missing = []
for f in T.glob('*.html'):
    text = f.read_text(encoding='utf-8')
    if '<a href="/" class="logo"' in text and '/static/logo.png' not in text:
        missing.append(f.name)
print('\n'.join(missing) if missing else 'All good')
