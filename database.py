import sqlite3

DB_NAME = "notion_data.db"

def init_users_table():
    """ユーザー管理用のテーブルを作成（初回のみ実行）"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def init_db():
    """データベースを作成（初回のみ実行）"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notion_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT,
            database_id TEXT,
            encoded_data TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_entry(api_key, database_id, encoded_data):
    """入力データをデータベースに保存"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO notion_entries (api_key, database_id, encoded_data) VALUES (?, ?, ?)",
              (api_key, database_id, encoded_data))
    conn.commit()
    conn.close()

def get_entries():
    """保存されたデータを取得"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, api_key, database_id, encoded_data, timestamp FROM notion_entries ORDER BY timestamp DESC")
    entries = c.fetchall()
    conn.close()
    return entries

# 初回のみデータベースを作成
init_db()


# 初回にテーブルを作成
init_users_table()