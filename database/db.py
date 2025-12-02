import sqlite3
from config import DB_PATH

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            image_path TEXT,
            ingredients TEXT,
            instructions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            video_url TEXT NOT NULL,
            title TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            product_name TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id)
        )
    ''')
    
    conn.commit()
    conn.close()