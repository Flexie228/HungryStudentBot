from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from pathlib import Path
from database.recipes_db import get_recipes_by_category, get_recipe, get_recipe_videos
from keyboards.menus import main_menu_keyboard, recipes_menu_keyboard, recipe_list_keyboard, recipe_card_keyboard
from database.recipes_db import search_recipes_by_product
from keyboards.menus import search_back_keyboard
from telegram.ext import MessageHandler, filters

BASE_DIR = Path(__file__).parent.parent

RECIPES = {
    'breakfast': {
        'title': '🍳 Завтраки и Перекусы',
        'recipes': {
            'omelette': {
                'name': 'Омлет с овощами',
                'image': 'images/snack/omlette.jpg',
                'ingredients': '• Яйца - 3 шт.\n• Молоко - 50 мл\n• Помидор - 1 шт.\n• Перец болгарский - 0.5 шт.\n• Соль, перец по вкусу',
                'instructions': '1. Взбейте яйца с молоком\n2. Нарежьте овощи кубиками\n3. Обжарьте овощи 3 минуты\n4. Залейте яичной смесью\n5. Готовьте под крышкой 7-10 минут',
                'guide_url': 'https://youtube.com'
            },
            'smoothie': {
                'name': 'Фруктовый смузи',
                'image': 'images/snack/smothie_banana_berries.jpg',
                'ingredients': '• Банан - 1 шт.\n• Ягоды замороженные - 100 г\n• Йогурт - 150 мл\n• Мед - 1 ст.л.',
                'instructions': '1. Все ингредиенты поместите в блендер\n2. Взбивайте до однородной массы\n3. Подавайте сразу же',
                'guide_url': 'https://youtube.com'
            }
        }
    },
    'lunch': {
        'title': '🍲 Обеды',
        'recipes': {
            'borscht': {
                'name': 'Борщ классический',
                'image': 'images/lunch/borsch.jpg',
                'ingredients': '• Свекла - 2 шт.\n• Капуста - 200 г\n• Картофель - 3 шт.\n• Мясо - 300 г\n• Морковь - 1 шт.\n• Лук - 1 шт.',
                'instructions': '1. Сварите мясной бульон\n2. Нарежьте овощи\n3. Обжарьте лук, морковь и свеклу\n4. Добавьте все в бульон\n5. Варите до готовности',
                'guide_url': 'https://youtube.com'
            },
            'salad': {
                'name': 'Греческий салат',
                'image': 'images/lunch/salad_greek.jpg',
                'ingredients': '• Помидоры - 2 шт.\n• Огурец - 1 шт.\n• Перец - 1 шт.\n• Сыр фета - 100 г\n• Оливки - 50 г\n• Оливковое масло',
                'instructions': '1. Нарежьте овощи крупно\n2. Добавьте сыр и оливки\n3. Заправьте маслом\n4. Аккуратно перемешайте',
                'guide_url': 'https://youtube.com'
            }
        }
    },
    'dinner': {
        'title': '🍝 Ужины',
        'recipes': {
            'pasta': {
                'name': 'Паста Карбонара',
                'image': 'images/dinner/pasta.jpg',
                'ingredients': '• Спагетти - 200 г\n• Бекон - 150 г\n• Яйца - 2 шт.\n• Сыр пармезан - 50 г\n• Сливки - 100 мл',
                'instructions': '1. Отварите пасту\n2. Обжарьте бекон\n3. Смешайте яйца со сливками и сыром\n4. Соедините все ингредиенты',
                'guide_url': 'https://youtube.com'
            },
            'chicken': {
                'name': 'Курица с овощами',
                'image': 'images/dinner/chicken_vegetables.jpg',
                'ingredients': '• Куриное филе - 400 г\n• Брокколи - 200 г\n• Морковь - 2 шт.\n• Соус соевый - 2 ст.л.',
                'instructions': '1. Нарежьте курицу и овощи\n2. Обжарьте курицу\n3. Добавьте овощи\n4. Тушите под крышкой 15 минут',
                'guide_url': 'https://youtube.com'
            }
        }
    }
}

# Твои оригинальные функции (немного адаптированы под БД)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👨‍🍳 Добро пожаловать!\n"
        "Наш бот — это личный помощник на кухне, который создан специально для студентов.\n"
        "С его помощью ты сможешь:\n"
        "✔️Быстро выбрать блюдо — выбери категорию или укажи какой продукт хочешь использовать\n"
        "✔️Сэкономить деньги — все рецепты основаны на доступных и недорогих ингредиентах\n"
        "✔️Готовить легко и просто — чётные инструкции и полезные советы помогут даже новичкам\n\n"
        "Выберите раздел:"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())
    else:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=main_menu_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'recipes':
        await query.edit_message_text(
            "🍽 Выберите категорию рецептов:",
            reply_markup=recipes_menu_keyboard()
        )
    
    elif data == 'feedback':
        await query.edit_message_text(
            "Мы стремимся к совершенству и ценим ваше мнение.\nПоделитесь своими мыслями и предложениями.🤝\n"
            "@darivue\n"
            "@dariiiiishaa\n"
            "@PKMaksimovna\n",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='back_main')]])
        )
    
    elif data == 'search':
        await query.edit_message_text(
            "🔍 Введите название продукта для поиска:\n\n"
            "Примеры: яйца, молоко, курица, помидоры, картофель",
            reply_markup=search_back_keyboard()
        )
        # Сохраняем состояние поиска
        context.user_data['waiting_for_product'] = True
    
    elif data in ['breakfast', 'lunch', 'dinner']:
        category_title = RECIPES[data]['title']
        recipes = get_recipes_by_category(data)
        await query.edit_message_text(
            f"{category_title}\n\nВыберите рецепт:",
            reply_markup=recipe_list_keyboard(recipes)
        )
    
    elif data.startswith('recipe_'):
        # Теперь используем ID из БД
        recipe_id = int(data.split('_')[1])
        recipe = get_recipe(recipe_id)
        videos = get_recipe_videos(recipe_id)  # Получаем все видео-ссылки
        
        recipe_text = (
            f"🍴 {recipe[2]}\n\n"  # name
            f"📋 **Состав:**\n{recipe[4]}\n\n"  # ingredients
            f"👨‍🍳 **Рецепт:**\n{recipe[5]}"  # instructions
        )
        
        await query.delete_message()
        
        try:
            image_path = BASE_DIR / recipe[3]  # image_path
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo,
                    caption=recipe_text,
                    reply_markup=recipe_card_keyboard(recipe_id, recipe[1], videos),  # category, videos
                    parse_mode='Markdown'
                )
        except Exception as e:
            print(f"Ошибка загрузки изображения: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=recipe_text,
                reply_markup=recipe_card_keyboard(recipe_id, recipe[1], videos),
                parse_mode='Markdown'
            )
    
    elif data.startswith('back_'):
        if data == 'back_main':
            await query.delete_message()
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="👨‍🍳 Добро пожаловать! Я - бот, помогу вам с рецептами!\n\nВыберите раздел:",
                reply_markup=main_menu_keyboard()
            )
        elif data == 'back_recipes':
            await query.delete_message()
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="🍽 Выберите категорию рецептов:",
                reply_markup=recipes_menu_keyboard()
            )
        elif data in ['back_breakfast', 'back_lunch', 'back_dinner']:
            category = data.replace('back_', '')
            category_title = RECIPES[category]['title']
            recipes = get_recipes_by_category(category)
            await query.delete_message()
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"{category_title}\n\nВыберите рецепт:",
                reply_markup=recipe_list_keyboard(recipes)
            )

async def handle_product_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка введенного продукта для поиска"""
    if context.user_data.get('waiting_for_product'):
        product_name = update.message.text.lower().strip()
        
        # Ищем рецепты
        recipes = search_recipes_by_product(product_name)
        
        if recipes:
            # Формируем список рецептов
            recipes_text = f"🍴 Найдено рецептов с '{product_name}':\n\n"
            for recipe in recipes:
                recipes_text += f"• {recipe[2]}\n"  # recipe[2] - название
            
            recipes_text += f"\nВыберите рецепт чтобы посмотреть подробности:"
            
            # Создаем клавиатуру с найденными рецептами
            keyboard = []
            for recipe in recipes:
                recipe_id, _, name, _, _, _, _ = recipe
                keyboard.append([InlineKeyboardButton(name, callback_data=f'recipe_{recipe_id}')])
            keyboard.append([InlineKeyboardButton("🔙 Назад к поиску", callback_data='search')])
            
            await update.message.reply_text(
                recipes_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                f"😔 Рецептов с продуктом '{product_name}' не найдено.\n\n"
                f"Попробуйте другой продукт:",
                reply_markup=search_back_keyboard()
            )
        
        # Сбрасываем состояние поиска
        context.user_data['waiting_for_product'] = False