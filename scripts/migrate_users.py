import shutil
import sqlite3
from pathlib import Path

SRC = Path('users.db')
DST = Path('database.db')

if not SRC.exists() or SRC.stat().st_size == 0:
    print('No source users.db found or file is empty; nothing to migrate.')
    raise SystemExit(0)

# Backup
shutil.copy2(SRC, SRC.with_suffix('.db.bak'))
print(f'Backup created: {SRC.with_suffix(".db.bak")}')

src = sqlite3.connect(SRC)
src.row_factory = sqlite3.Row

dst = sqlite3.connect(DST)

dst.execute('PRAGMA foreign_keys = ON')

migrated = 0
skipped = 0

with src:
    cur = src.cursor()
    try:
        cur.execute('SELECT id, name, phone, username, password_hash FROM users')
    except sqlite3.OperationalError as e:
        print('Source users table not found or has different schema:', e)
        raise SystemExit(1)

    rows = cur.fetchall()

    dcur = dst.cursor()

    for r in rows:
        username = r['username']
        name = r['name']
        phone = r['phone']
        password_hash = r['password_hash']

        dcur.execute('SELECT id FROM users WHERE username = ?', (username,))
        if dcur.fetchone():
            skipped += 1
            continue

        dcur.execute(
            'INSERT INTO users (username, email, name, phone, password_hash, created_at) VALUES (?, ?, ?, ?, ?, datetime("now"))',
            (username, None, name, phone, password_hash)
        )
        migrated += 1

    dst.commit()

print(f'Migration complete. Migrated: {migrated}, Skipped (existing): {skipped}')
