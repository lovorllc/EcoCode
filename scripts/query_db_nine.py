import sqlite3
conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
row = cur.execute("SELECT phone, phone_e164 FROM users WHERE username = ?", ('nine1',)).fetchone()
print(row['phone'], row['phone_e164'])
