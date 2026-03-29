from database import Database
db = Database('database.db')

# Check if there's an admin user
conn = db.connect()
cursor = conn.cursor()
cursor.execute("SELECT id, username, user_type FROM users WHERE user_type = 'admin' LIMIT 5")
admin_users = cursor.fetchall()
print(f"Admin users in database: {len(admin_users)}")
for user in admin_users:
    print(f"  - ID: {user[0]}, Username: {user[1]}, Type: {user[2]}")

cursor.execute("SELECT COUNT(*) FROM activities")
activity_count = cursor.fetchone()[0]
print(f"\nTotal activities in database: {activity_count}")
conn.close()
