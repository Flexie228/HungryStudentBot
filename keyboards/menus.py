from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📖 Рецепты", callback_data='recipes')],
        [InlineKeyboardButton("📞 Обратная связь", callback_data='feedback')]
    ]
    return InlineKeyboardMarkup(keyboard)

def recipes_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🍳 Завтрак / Перекус", callback_data='breakfast')],
        [InlineKeyboardButton("🍲 Обед", callback_data='lunch')],
        [InlineKeyboardButton("🍝 Ужин", callback_data='dinner')],
        [InlineKeyboardButton("🔍 Поиск по продукту", callback_data='search')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def recipe_list_keyboard(recipes):
    """recipes - список кортежей (id, name)"""
    keyboard = []
    for recipe_id, recipe_name in recipes:
        keyboard.append([InlineKeyboardButton(recipe_name, callback_data=f'recipe_{recipe_id}')])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back_recipes')])
    return InlineKeyboardMarkup(keyboard)

def recipe_card_keyboard(recipe_id, category, videos):
    """videos - список кортежей (url, title)"""
    keyboard = []
    
    # Кнопки для каждого видео
    for i, (url, title) in enumerate(videos, 1):
        button_text = f"🎥 Видео {i}"
        if title:
            button_text = f"🎥 {title}"
        keyboard.append([InlineKeyboardButton(button_text, url=url)])
    
    keyboard.append([InlineKeyboardButton("🔙 К списку рецептов", callback_data=f'back_{category}')])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data='back_main')])
    
    return InlineKeyboardMarkup(keyboard)

def search_back_keyboard():
    """Клавиатура только с кнопкой Назад для поиска"""
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data='back_recipes')]
    ]
    return InlineKeyboardMarkup(keyboard)