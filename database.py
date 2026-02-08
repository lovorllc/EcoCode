import sqlite3
from pathlib import Path
import sys, os
import uuid

# Support running from a PyInstaller bundle: if frozen, resources are in sys._MEIPASS
if getattr(sys, 'frozen', False):
    DB_PATH = Path(getattr(sys, '_MEIPASS', '.')) / 'database.db'
else:
    DB_PATH = Path("database.db")


class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._create_tables()
        # Ensure schema migrations are applied (add missing columns if needed)
        self._migrate_schema()

    def _migrate_schema(self):
        """Apply schema migrations to ensure the users table has expected columns.
        If the existing table has rows, migrate carefully; if empty, recreate it.
        """
        with self.connect() as conn:
            cursor = conn.cursor()

            # Ensure activities table has quantity and unit columns if missing (independent of users schema)
            try:
                cursor.execute("PRAGMA table_info(activities)")
                a_cols = [row[1] for row in cursor.fetchall()]
                if 'quantity' not in a_cols:
                    try:
                        cursor.execute("ALTER TABLE activities ADD COLUMN quantity REAL")
                        conn.commit()
                    except Exception:
                        pass
                if 'unit' not in a_cols:
                    try:
                        cursor.execute("ALTER TABLE activities ADD COLUMN unit TEXT")
                        conn.commit()
                    except Exception:
                        pass
            except Exception:
                # activities table may not exist yet; _create_tables will handle that
                pass

            cursor.execute("PRAGMA table_info(users)")
            cols = [row[1] for row in cursor.fetchall()]

            needed = ['name', 'phone', 'phone_e164', 'password_hash', 'user_type', 'permanent', 'last_active', 'language', 'theme']
            missing = [c for c in needed if c not in cols]
            # If no missing columns and email is nullable, we're good
            if not missing:
                return

            # If the phone_e164 column is missing, add it directly (simpler and safer)
            if 'phone_e164' in missing:
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN phone_e164 TEXT")
                    conn.commit()
                except Exception:
                    pass

                # Try to populate phone_e164 for rows that already have an international-looking phone (+...)
                try:
                    import phone_utils
                    cursor.execute("SELECT id, phone FROM users WHERE phone IS NOT NULL AND phone LIKE '+%'")
                    for r in cursor.fetchall():
                        _id = r[0]
                        phone_val = r[1]
                        try:
                            norm = phone_utils.normalize_phone(phone_val)
                            cursor.execute("UPDATE users SET phone_e164 = ? WHERE id = ?", (norm['e164'], _id))
                        except Exception:
                            pass
                    conn.commit()
                except Exception:
                    pass

            if 'user_type' in missing:
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN user_type TEXT DEFAULT 'user'")
                    conn.commit()
                except Exception:
                    pass

                # no backfill required — default is 'user' for older rows

            if 'permanent' in missing:
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN permanent INTEGER DEFAULT 0")
                    conn.commit()
                except Exception:
                    pass

            # Add last_active column if missing
            if 'last_active' in missing:
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN last_active TIMESTAMP")
                    conn.commit()
                except Exception:
                    pass

            # Add language column if missing (defaults to 'en')
            if 'language' in missing:
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'en'")
                    conn.commit()
                except Exception:
                    pass

            # Add theme column if missing (defaults to 'light')
            if 'theme' in missing:
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'light'")
                    conn.commit()
                except Exception:
                    pass

            # If table has data, perform careful migration: create new table, copy data
            # ensure fresh temporary table
            cursor.execute("DROP TABLE IF EXISTS users_new")
            cursor.execute("""
                CREATE TABLE users_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT,
                    phone_e164 TEXT,
                    user_type TEXT DEFAULT 'user',
                    permanent INTEGER DEFAULT 0,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    password_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP
                )
            """)
            # Copy existing known columns
            existing_cols = [c for c in ['id', 'username', 'email', 'created_at', 'name', 'phone'] if c in cols]
            select_cols = ', '.join(existing_cols)
            cursor.execute(f"INSERT OR IGNORE INTO users_new ({select_cols}) SELECT {select_cols} FROM users")

            # Attempt to populate phone_e164 for rows where the phone looks like an international number (+...)
            try:
                import phone_utils
                cursor.execute("SELECT id, phone FROM users_new")
                rows = cursor.fetchall()
                for r in rows:
                    _id = r[0]
                    phone_val = r[1]
                    if phone_val and phone_val.strip().startswith('+'):
                        try:
                            norm = phone_utils.normalize_phone(phone_val)
                            cursor.execute("UPDATE users_new SET phone_e164 = ? WHERE id = ?", (norm['e164'], _id))
                        except Exception:
                            # skip normalizing invalid numbers
                            pass
            except Exception:
                # phone_utils not available or other error — skip normalization
                pass

            cursor.execute("DROP TABLE users")
            cursor.execute("ALTER TABLE users_new RENAME TO users")
            conn.commit()

            # Ensure activities table migrations: add quantity and unit columns if missing
            try:
                cursor.execute("PRAGMA table_info(activities)")
                a_cols = [r[1] for r in cursor.fetchall()]
                if 'quantity' not in a_cols:
                    try:
                        cursor.execute("ALTER TABLE activities ADD COLUMN quantity REAL")
                    except Exception:
                        pass
                if 'unit' not in a_cols:
                    try:
                        cursor.execute("ALTER TABLE activities ADD COLUMN unit TEXT")
                    except Exception:
                        pass
                conn.commit()
            except Exception:
                pass
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def update_user(self, user_id: int, username: str = None, email: str = None, name: str = None, phone: str = None, phone_e164: str = None, password_hash: str = None, user_type: str = None, permanent: int = None, last_active: str = None, language: str = None, theme: str = None):
        """Update only provided fields for a user."""
        fields = []
        values = []
        if username is not None:
            fields.append("username = ?")
            values.append(username)
        if email is not None:
            fields.append("email = ?")
            values.append(email)
        if name is not None:
            fields.append("name = ?")
            values.append(name)
        if phone is not None:
            fields.append("phone = ?")
            values.append(phone)
        if phone_e164 is not None:
            fields.append("phone_e164 = ?")
            values.append(phone_e164)
        if password_hash is not None:
            fields.append("password_hash = ?")
            values.append(password_hash)
        if user_type is not None:
            fields.append("user_type = ?")
            values.append(user_type)
        if permanent is not None:
            fields.append("permanent = ?")
            values.append(permanent)
        if last_active is not None:
            fields.append("last_active = ?")
            values.append(last_active)
        if language is not None:
            fields.append("language = ?")
            values.append(language)
        if theme is not None:
            fields.append("theme = ?")
            values.append(theme)

        if not fields:
            return 0

        values.append(user_id)
        sql = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(values))
            conn.commit()
            return cursor.rowcount

    def _create_tables(self):
        """Create tables if they don't exist."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT,
                    phone_e164 TEXT,
                    user_type TEXT DEFAULT 'user',
                    permanent INTEGER DEFAULT 0,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP,
                    language TEXT DEFAULT 'en',
                    theme TEXT DEFAULT 'light'
                )
            """)
            # Activities table: store persistent activity logs per user
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    subtype TEXT,
                    co2_kg REAL DEFAULT 0.0,
                    quantity REAL,
                    unit TEXT,
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            # Emission factors table: per category/subtype multipliers (co2_kg per unit)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emission_factors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    subtype TEXT,
                    unit TEXT,
                    co2_kg_per_unit REAL NOT NULL,
                    source TEXT
                )
            """)
            # seed default emission factors if empty
            cursor.execute("SELECT COUNT(*) FROM emission_factors")
            cnt = cursor.fetchone()[0]
            if cnt == 0:
                # Approximate default factors (public-domain estimates; verify for your region)
                defaults = [
                    ('Transport','car','km',0.21,'Approximate average; see local sources'),
                    ('Transport','bus','km',0.05,'Approximate average; see local sources'),
                    ('Transport','bike','km',0.0,'Zero direct emissions'),
                    ('Transport','walking','km',0.0,'Zero direct emissions'),
                    ('Electricity',None,'kWh',0.233,'Grid average estimate; adjust per country'),
                    ('Water',None,'liter',0.0003,'Embodied energy estimate (approx.)'),
                    ('Food','beef','meal',6.0,'Approximate beef meal emissions'),
                    ('Food','pork','meal',2.5,'Approximate pork meal emissions'),
                    ('Food','chicken','meal',1.5,'Approximate chicken meal emissions'),
                    ('Food','fish','meal',2.0,'Approximate fish meal emissions'),
                    ('Food','vegetarian','meal',1.0,'Approximate per meal emissions'),
                    ('Food','vegan','meal',0.5,'Approximate per meal emissions'),
                    ('Shopping','electronics','item',50.0,'Approximate lifecycle estimate per device'),
                    ('Shopping','clothes','item',6.0,'Approximate lifecycle estimate per garment')
                ]
                cursor.executemany('INSERT INTO emission_factors (category,subtype,unit,co2_kg_per_unit,source) VALUES (?,?,?,?,?)', defaults)
                conn.commit()

                # Ensure more detailed food subtypes exist in older DBs
                food_extra = [
                    ('Food','beef','meal',6.0,'Approximate beef meal emissions'),
                    ('Food','pork','meal',2.5,'Approximate pork meal emissions'),
                    ('Food','chicken','meal',1.5,'Approximate chicken meal emissions'),
                    ('Food','fish','meal',2.0,'Approximate fish meal emissions')
                ]
                for s in food_extra:
                    cursor.execute("SELECT COUNT(*) FROM emission_factors WHERE category = ? AND subtype = ?", (s[0], s[1]))
                    if cursor.fetchone()[0] == 0:
                        cursor.execute('INSERT INTO emission_factors (category,subtype,unit,co2_kg_per_unit,source) VALUES (?,?,?,?,?)', s)
                conn.commit()
            conn.commit()

            # Also ensure missing food factors are present for existing DBs
            try:
                extras = [
                    ('Food','beef','meal',6.0,'Approximate beef meal emissions'),
                    ('Food','pork','meal',2.5,'Approximate pork meal emissions'),
                    ('Food','chicken','meal',1.5,'Approximate chicken meal emissions'),
                    ('Food','fish','meal',2.0,'Approximate fish meal emissions')
                ]
                for s in extras:
                    cursor.execute("SELECT COUNT(*) FROM emission_factors WHERE category=? AND subtype=?", (s[0], s[1]))
                    if cursor.fetchone()[0] == 0:
                        cursor.execute('INSERT INTO emission_factors (category,subtype,unit,co2_kg_per_unit,source) VALUES (?,?,?,?,?)', s)
                conn.commit()
            except Exception:
                pass

            # GPS tracking tables: store tracks and their point sequences
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gps_tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    activity_type TEXT,
                    name TEXT,
                    started_at TIMESTAMP,
                    ended_at TIMESTAMP,
                    distance_km REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gps_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_id INTEGER NOT NULL,
                    seq INTEGER NOT NULL,
                    lat REAL NOT NULL,
                    lon REAL NOT NULL,
                    timestamp TIMESTAMP,
                    accuracy REAL,
                    speed REAL,
                    FOREIGN KEY(track_id) REFERENCES gps_tracks(id) ON DELETE CASCADE
                )
            """)
            # Indexes for faster lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_gps_points_track_id ON gps_points(track_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_gps_tracks_user_id ON gps_tracks(user_id)")

            # API tokens table for mobile clients (simple token-based auth)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_tokens (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    # ---------- CRUD FUNCTIONS ----------

    def add_user(self, username: str, email: str = None, name: str = None, phone: str = None, phone_e164: str = None, password_hash: str = None, user_type: str = 'user', permanent: int = 0):
        """Insert a user. Only username is required; other fields are optional."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, name, phone, phone_e164, password_hash, user_type, permanent) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (username, email, name, phone, phone_e164, password_hash, user_type, permanent)
            )
            conn.commit()
            return cursor.lastrowid

    # ---------- Activities ----------
    def add_activity(self, user_id: int, category: str, subtype: str = None, co2_kg: float = 0.0, note: str = None, quantity: float = None, unit: str = None):
        """Create an activity entry for a user."""
        with self.connect() as conn:
            cursor = conn.cursor()
            # Ensure insertion order matches function signature: co2_kg, note, quantity, unit
            cursor.execute(
                "INSERT INTO activities (user_id, category, subtype, co2_kg, note, quantity, unit, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (user_id, category, subtype, co2_kg, note, quantity, unit)
            )
            conn.commit()
            return cursor.lastrowid

    def get_emission_factor(self, category: str, subtype: str = None):
        with self.connect() as conn:
            cursor = conn.cursor()
            # try exact match first
            if subtype:
                cursor.execute("SELECT id, category, subtype, unit, co2_kg_per_unit, source FROM emission_factors WHERE category = ? AND subtype = ? LIMIT 1", (category, subtype))
                r = cursor.fetchone()
                if r:
                    return dict(r)
            # fallback to category-level factor
            cursor.execute("SELECT id, category, subtype, unit, co2_kg_per_unit, source FROM emission_factors WHERE category = ? AND (subtype IS NULL OR subtype = '') LIMIT 1", (category,))
            r = cursor.fetchone()
            if r:
                return dict(r)
            return None

    def list_emission_factors(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, category, subtype, unit, co2_kg_per_unit, source FROM emission_factors ORDER BY category, subtype")
            return cursor.fetchall()

    def get_activities_for_user(self, user_id: int, limit: int = 100):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, category, subtype, co2_kg, quantity, unit, note, created_at FROM activities WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
            rows = cursor.fetchall()
            # do not mutate DB here; return rows as-is and let application layer compute display co2
            return rows

    def get_activities_for_user_on_date(self, user_id: int, target_date: str):
        """Return activities for a user on a specific date (YYYY-MM-DD)."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, category, subtype, co2_kg, quantity, unit, note, created_at FROM activities WHERE user_id = ? AND date(created_at) = ? ORDER BY created_at ASC", (user_id, target_date))
            return cursor.fetchall()

    def get_all_activities(self, limit: int = 1000):
        """Return all activities across users (most recent first) with username included."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT activities.id, activities.user_id, users.username, activities.category, activities.subtype, activities.co2_kg, activities.quantity, activities.unit, activities.note, activities.created_at FROM activities LEFT JOIN users ON activities.user_id = users.id ORDER BY activities.created_at DESC LIMIT ?", (limit,))
            return cursor.fetchall()

    def apply_emission_factor_to_activities(self, category: str, subtype: str, co2_kg_per_unit: float):
        """Update existing activities (where co2_kg is NULL or 0 and quantity exists) to store co2_kg = quantity * co2_kg_per_unit.
        Returns number of rows updated."""
        with self.connect() as conn:
            cursor = conn.cursor()
            if subtype:
                cursor.execute("UPDATE activities SET co2_kg = ROUND(quantity * ?, 6) WHERE category = ? AND subtype = ? AND quantity IS NOT NULL AND (co2_kg IS NULL OR co2_kg = 0)", (co2_kg_per_unit, category, subtype))
            else:
                cursor.execute("UPDATE activities SET co2_kg = ROUND(quantity * ?, 6) WHERE category = ? AND (subtype IS NULL OR subtype = '') AND quantity IS NOT NULL AND (co2_kg IS NULL OR co2_kg = 0)", (co2_kg_per_unit, category))
            conn.commit()
            return cursor.rowcount

    def delete_emission_factor(self, ef_id: int):
        """Delete an emission factor by id."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM emission_factors WHERE id = ?", (ef_id,))
            conn.commit()
            return cursor.rowcount

    def add_emission_factor(self, category: str, subtype: str = None, unit: str = None, co2_kg_per_unit: float = 0.0, source: str = None):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO emission_factors (category, subtype, unit, co2_kg_per_unit, source) VALUES (?,?,?,?,?)', (category, subtype, unit, co2_kg_per_unit, source))
            conn.commit()
            return cursor.lastrowid

    def update_emission_factor(self, ef_id: int, co2_kg_per_unit: float = None, unit: str = None, source: str = None):
        fields = []
        values = []
        if co2_kg_per_unit is not None:
            fields.append('co2_kg_per_unit = ?')
            values.append(co2_kg_per_unit)
        if unit is not None:
            fields.append('unit = ?')
            values.append(unit)
        if source is not None:
            fields.append('source = ?')
            values.append(source)
        if not fields:
            return 0
        values.append(ef_id)
        sql = f"UPDATE emission_factors SET {', '.join(fields)} WHERE id = ?"
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(values))
            conn.commit()
            return cursor.rowcount

    def upsert_emission_factor(self, category: str, subtype: str = None, unit: str = None, co2_kg_per_unit: float = 0.0, source: str = None):
        # Try to find existing factor for category/subtype
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM emission_factors WHERE category = ? AND (subtype = ? OR (subtype IS NULL AND ? IS NULL)) LIMIT 1', (category, subtype, subtype))
            r = cursor.fetchone()
            if r:
                ef_id = r[0]
                cursor.execute('UPDATE emission_factors SET unit = ?, co2_kg_per_unit = ?, source = ? WHERE id = ?', (unit, co2_kg_per_unit, source, ef_id))
                conn.commit()
                return ef_id
            else:
                cursor.execute('INSERT INTO emission_factors (category, subtype, unit, co2_kg_per_unit, source) VALUES (?,?,?,?,?)', (category, subtype, unit, co2_kg_per_unit, source))
                conn.commit()
                return cursor.lastrowid

    def get_activity_sums_by_hour(self, user_id: int, target_date: str):
        """Return dict hour->sum(co2_kg) for a given date (YYYY-MM-DD).
        Compute co2 for activities that don't have a stored co2_kg by using emission_factors * quantity when available.
        """
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, strftime('%H', created_at) as hour, category, subtype, co2_kg, quantity, unit FROM activities WHERE user_id = ? AND date(created_at) = ? ORDER BY created_at ASC", (user_id, target_date))
            rows = cursor.fetchall()
            res = {}
            for r in rows:
                try:
                    hr = int(r[1])
                except Exception:
                    hr = 0
                co2 = float(r[4] or 0)
                qty = r[5]
                if (not co2 or co2 == 0) and qty is not None:
                    # try to compute using emission factor
                    try:
                        ef = self.get_emission_factor(r[2], r[3])
                        if ef and ef.get('co2_kg_per_unit') is not None:
                            co2 = float(qty) * float(ef.get('co2_kg_per_unit'))
                    except Exception:
                        pass
                res[hr] = res.get(hr, 0.0) + co2
            return res

    def get_activity_sums_by_day(self, user_id: int, start_date: str, end_date: str):
        """Return dict date->sum(co2_kg) for date range inclusive. Dates in YYYY-MM-DD.
        Compute co2 for activities without stored co2 using emission factors * quantity when available.
        """
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, date(created_at) as d, category, subtype, co2_kg, quantity, unit FROM activities WHERE user_id = ? AND date(created_at) BETWEEN ? AND ? ORDER BY created_at ASC", (user_id, start_date, end_date))
            rows = cursor.fetchall()
            res = {}
            for r in rows:
                d = r[1]
                co2 = float(r[4] or 0)
                qty = r[5]
                if (not co2 or co2 == 0) and qty is not None:
                    try:
                        ef = self.get_emission_factor(r[2], r[3])
                        if ef and ef.get('co2_kg_per_unit') is not None:
                            co2 = float(qty) * float(ef.get('co2_kg_per_unit'))
                    except Exception:
                        pass
                res[d] = res.get(d, 0.0) + co2
            return res

    def get_activity_counts_by_day(self, user_id: int, start_date: str, end_date: str):
        """Return dict date->count of activities in the inclusive date range."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT date(created_at) as d, COUNT(*) as cnt FROM activities WHERE user_id = ? AND date(created_at) BETWEEN ? AND ? GROUP BY d ORDER BY d ASC", (user_id, start_date, end_date))
            rows = cursor.fetchall()
            res = {}
            for r in rows:
                res[r[0]] = int(r[1] or 0)
            return res

    def get_activity(self, activity_id: int):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, category, subtype, co2_kg, quantity, unit, note, created_at FROM activities WHERE id = ? LIMIT 1", (activity_id,))
            r = cursor.fetchone()
            return r

    def delete_activity(self, activity_id: int):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
            conn.commit()
            return cursor.rowcount

    def get_user(self, user_id: int):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, created_at, name, phone, phone_e164, password_hash, user_type, permanent, last_active FROM users WHERE id = ?",
                (user_id,)
            )
            return cursor.fetchone()

    def get_user_by_username(self, username: str):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, created_at, name, phone, phone_e164, password_hash, user_type, permanent, last_active FROM users WHERE username = ?",
                (username,)
            )
            return cursor.fetchone()

    def get_user_by_login(self, key: str):
        """Find a user by username, email, phone, or phone_e164."""
        with self.connect() as conn:
            cursor = conn.cursor()
            # username
            cursor.execute("SELECT id, username, email, created_at, name, phone, phone_e164, password_hash, user_type, permanent, last_active FROM users WHERE username = ?", (key,))
            r = cursor.fetchone()
            if r:
                return r
            # email
            cursor.execute("SELECT id, username, email, created_at, name, phone, phone_e164, password_hash, user_type, permanent, last_active FROM users WHERE email = ?", (key,))
            r = cursor.fetchone()
            if r:
                return r
            # exact phone match
            cursor.execute("SELECT id, username, email, created_at, name, phone, phone_e164, password_hash, user_type, permanent, last_active FROM users WHERE phone = ?", (key,))
            r = cursor.fetchone()
            if r:
                return r
            # e164 match
            cursor.execute("SELECT id, username, email, created_at, name, phone, phone_e164, password_hash, user_type, permanent, last_active FROM users WHERE phone_e164 = ?", (key,))
            r = cursor.fetchone()
            if r:
                return r
            return None

    # ---------- API token helpers ----------
    def create_api_token(self, user_id: int, token: str = None, expires_at: str = None):
        """Create a simple API token bound to the given user id. Returns the token string."""
        if token is None:
            token = uuid.uuid4().hex
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO api_tokens (token, user_id, expires_at) VALUES (?,?,?)", (token, user_id, expires_at))
            conn.commit()
            return token

    def get_user_by_token(self, token: str):
        """Return user row for a valid token, or None."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM api_tokens WHERE token = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)", (token,))
            r = cursor.fetchone()
            if not r:
                return None
            try:
                return self.get_user(r[0])
            except Exception:
                return None

    def delete_api_token(self, token: str):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM api_tokens WHERE token = ?", (token,))
            conn.commit()
            return cursor.rowcount

    def get_all_users(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email, created_at, name, phone, phone_e164, password_hash, user_type, permanent, last_active FROM users")
            return cursor.fetchall()

    def delete_user(self, user_id: int):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount

    # ---------- GPS Tracking CRUD ----------
    def add_track(self, user_id: int, activity_type: str, name: str = None, started_at: str = None, ended_at: str = None, distance_km: float = None):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO gps_tracks (user_id, activity_type, name, started_at, ended_at, distance_km) VALUES (?,?,?,?,?,?)", (user_id, activity_type, name, started_at, ended_at, distance_km))
            conn.commit()
            return cursor.lastrowid

    def add_track_point(self, track_id: int, seq: int, lat: float, lon: float, timestamp: str = None, accuracy: float = None, speed: float = None):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO gps_points (track_id, seq, lat, lon, timestamp, accuracy, speed) VALUES (?,?,?,?,?,?,?)", (track_id, seq, lat, lon, timestamp, accuracy, speed))
            conn.commit()
            return cursor.lastrowid

    def get_tracks_for_user(self, user_id: int):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, activity_type, name, started_at, ended_at, distance_km, created_at FROM gps_tracks WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            return cursor.fetchall()

    def get_track_points(self, track_id: int):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT seq, lat, lon, timestamp, accuracy, speed FROM gps_points WHERE track_id = ? ORDER BY seq ASC", (track_id,))
            return cursor.fetchall()

    def delete_track(self, track_id: int):
        """Delete a track and its points."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM gps_points WHERE track_id = ?", (track_id,))
            cursor.execute("DELETE FROM gps_tracks WHERE id = ?", (track_id,))
            conn.commit()
            return cursor.rowcount

    def get_all_tracks(self, limit: int = 1000):
        """Return all tracks across users with username included."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT gps_tracks.id, gps_tracks.user_id, users.username, gps_tracks.activity_type, gps_tracks.name, gps_tracks.started_at, gps_tracks.ended_at, gps_tracks.distance_km, gps_tracks.created_at FROM gps_tracks LEFT JOIN users ON gps_tracks.user_id = users.id ORDER BY gps_tracks.created_at DESC LIMIT ?", (limit,))
            return cursor.fetchall()

    def delete_track_point(self, track_id: int, seq: int):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM gps_points WHERE track_id = ? AND seq = ?", (track_id, seq))
            conn.commit()
            return cursor.rowcount

    def update_track_point(self, track_id: int, seq: int, lat: float = None, lon: float = None, timestamp: str = None, accuracy: float = None, speed: float = None):
        fields = []
        values = []
        if lat is not None:
            fields.append('lat = ?')
            values.append(lat)
        if lon is not None:
            fields.append('lon = ?')
            values.append(lon)
        if timestamp is not None:
            fields.append('timestamp = ?')
            values.append(timestamp)
        if accuracy is not None:
            fields.append('accuracy = ?')
            values.append(accuracy)
        if speed is not None:
            fields.append('speed = ?')
            values.append(speed)
        if not fields:
            return 0
        values.extend([track_id, seq])
        sql = f"UPDATE gps_points SET {', '.join(fields)} WHERE track_id = ? AND seq = ?"
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(values))
            conn.commit()
            return cursor.rowcount

    def update_track(self, track_id: int, name: str = None, distance_km: float = None, started_at: str = None, ended_at: str = None, activity_type: str = None):
        fields = []
        values = []
        if name is not None:
            fields.append('name = ?')
            values.append(name)
        if distance_km is not None:
            fields.append('distance_km = ?')
            values.append(distance_km)
        if started_at is not None:
            fields.append('started_at = ?')
            values.append(started_at)
        if ended_at is not None:
            fields.append('ended_at = ?')
            values.append(ended_at)
        if activity_type is not None:
            fields.append('activity_type = ?')
            values.append(activity_type)
        if not fields:
            return 0
        values.append(track_id)
        sql = f"UPDATE gps_tracks SET {', '.join(fields)} WHERE id = ?"
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(values))
            conn.commit()
            return cursor.rowcount
