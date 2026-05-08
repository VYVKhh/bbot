# database.py
import sqlite3
from pathlib import Path

DB_PATH = Path("bot_data.db")
OWNER_ID = 123456789  # ضع معرف التليجرام الخاص بك هنا

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS banned_users (user_id INTEGER PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, coins INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS required_channels (channel_id TEXT PRIMARY KEY, channel_url TEXT, channel_name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS programmer_text (id INTEGER PRIMARY KEY DEFAULT 1, text TEXT)''')
    # إضافة أول أدمن (المالك)
    c.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (OWNER_ID,))
    conn.commit()
    conn.close()

def is_admin(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    result = c.fetchone() is not None
    conn.close()
    return result

def add_admin(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def remove_admin(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def ban_user(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,))
    result = c.fetchone() is not None
    conn.close()
    return result

def get_coins(user_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row is None:
        c.execute("INSERT INTO users (user_id, coins) VALUES (?, 0)", (user_id,))
        conn.commit()
        coins = 0
    else:
        coins = row[0]
    conn.close()
    return coins

def set_coins(user_id: int, amount: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, coins) VALUES (?, 0)", (user_id,))
    c.execute("UPDATE users SET coins = ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def add_coins(user_id: int, amount: int):
    current = get_coins(user_id)
    set_coins(user_id, current + amount)

def remove_coins(user_id: int, amount: int):
    current = get_coins(user_id)
    new = current - amount
    if new < 0:
        new = 0
    set_coins(user_id, new)

def deduct_coins(user_id: int, amount: int) -> bool:
    if amount <= 0:
        return True
    coins = get_coins(user_id)
    if coins < amount:
        return False
    set_coins(user_id, coins - amount)
    return True

def get_all_users() -> list:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_all_admins() -> list:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_programmer_text() -> str:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT text FROM programmer_text WHERE id = 1")
    row = c.fetchone()
    if row is None:
        default = "📝 **Programmer Zone**\n\nYou can customize this message later.\nJust edit it using /set_programmer <text>"
        c.execute("INSERT INTO programmer_text (id, text) VALUES (1, ?)", (default,))
        conn.commit()
        text = default
    else:
        text = row[0]
    conn.close()
    return text

def set_programmer_text(new_text: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO programmer_text (id, text) VALUES (1, ?)", (new_text,))
    conn.commit()
    conn.close()

def add_required_channel(channel_id: str, channel_url: str, channel_name: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO required_channels (channel_id, channel_url, channel_name) VALUES (?, ?, ?)",
              (channel_id, channel_url, channel_name))
    conn.commit()
    conn.close()

def remove_required_channel(channel_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM required_channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()

def get_required_channels() -> list:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_id, channel_url, channel_name FROM required_channels")
    rows = c.fetchall()
    conn.close()
    return rows

init_db()