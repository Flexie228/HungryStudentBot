import sqlite3
from config import DB_PATH

# Рецепты
def get_recipe(recipe_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,))
    recipe = cursor.fetchone()
    conn.close()
    return recipe

def get_recipes_by_category(category):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM recipes WHERE category = ? ORDER BY name', (category,))
    recipes = cursor.fetchall()
    conn.close()
    return recipes

def add_recipe(category, name, image_path, ingredients, instructions):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO recipes (category, name, image_path, ingredients, instructions) VALUES (?, ?, ?, ?, ?)',
        (category, name, image_path, ingredients, instructions)
    )
    recipe_id = cursor.lastrowid
    
    # Продукты для поиска
    for line in ingredients.split('\n'):
        if '•' in line:
            product = line.split('•')[1].split('-')[0].strip().lower()
            cursor.execute(
                'INSERT INTO recipe_products (recipe_id, product_name) VALUES (?, ?)',
                (recipe_id, product)
            )
    
    conn.commit()
    conn.close()
    return recipe_id

# Видео-ссылки
def add_video_to_recipe(recipe_id, video_url, title=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO recipe_videos (recipe_id, video_url, title) VALUES (?, ?, ?)',
        (recipe_id, video_url, title)
    )
    conn.commit()
    conn.close()

def get_recipe_videos(recipe_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT video_url, title FROM recipe_videos WHERE recipe_id = ?', (recipe_id,))
    videos = cursor.fetchall()
    conn.close()
    return videos

# Поиск
def search_recipes_by_product(product_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.* FROM recipes r
        JOIN recipe_products rp ON r.id = rp.recipe_id
        WHERE rp.product_name LIKE ?
    ''', (f'%{product_name}%',))
    recipes = cursor.fetchall()
    conn.close()
    return recipes

def update_recipe(recipe_id, ingredients=None, instructions=None):
    """Обновление рецепта"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if ingredients is not None:
        updates.append("ingredients = ?")
        params.append(ingredients)
    
    if instructions is not None:
        updates.append("instructions = ?")
        params.append(instructions)
    
    if updates:
        query = f"UPDATE recipes SET {', '.join(updates)} WHERE id = ?"
        params.append(recipe_id)
        cursor.execute(query, params)
    
    conn.commit()
    conn.close()

def update_recipe_image(recipe_id, image_path):
    """Обновление пути к изображению"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE recipes SET image_path = ? WHERE id = ?', (image_path, recipe_id))
    conn.commit()
    conn.close()

def delete_recipe_videos(recipe_id):
    """Удаление всех видео-ссылок рецепта"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM recipe_videos WHERE recipe_id = ?', (recipe_id,))
    conn.commit()
    conn.close()

def update_recipe_products(recipe_id, ingredients_text):
    """Обновление продуктов для поиска"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Удаляем старые продукты
    cursor.execute('DELETE FROM recipe_products WHERE recipe_id = ?', (recipe_id,))
    
    # Добавляем новые продукты
    for line in ingredients_text.split('\n'):
        if '•' in line:
            product = line.split('•')[1].split('-')[0].strip().lower()
            cursor.execute(
                'INSERT INTO recipe_products (recipe_id, product_name) VALUES (?, ?)',
                (recipe_id, product)
            )
    
    conn.commit()
    conn.close()

def delete_recipe_completely(recipe_id):
    """Полное удаление рецепта и всех связанных данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Удаляем связанные данные (продукты и видео)
        cursor.execute('DELETE FROM recipe_products WHERE recipe_id = ?', (recipe_id,))
        cursor.execute('DELETE FROM recipe_videos WHERE recipe_id = ?', (recipe_id,))
        
        # Удаляем сам рецепт
        cursor.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()