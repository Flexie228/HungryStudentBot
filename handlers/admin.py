from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from database.recipes_db import add_recipe
from utils.auth import check_admin, is_admin
from utils.helpers import transliterate_to_english
import sqlite3
from config import DB_PATH
import os
from pathlib import Path
from config import BASE_DIR
from database.recipes_db import (
    add_recipe, 
    add_video_to_recipe, 
    get_recipes_by_category,
    get_recipe, 
    get_recipe_videos,
    update_recipe,
    update_recipe_image,
    delete_recipe_videos,
    update_recipe_products,
    delete_recipe_completely
)

(
    CATEGORY, NAME, PHOTO, INGREDIENTS, INSTRUCTIONS, VIDEOS,
    CHANGE_RECIPE_SELECT, CHANGE_FIELD, CHANGE_PHOTO, CHANGE_INGREDIENTS, CHANGE_INSTRUCTIONS, CHANGE_VIDEOS
) = range(12)

async def start_add_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления рецепта - ТОЛЬКО ДЛЯ АДМИНОВ"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("🍳 Завтрак", callback_data='breakfast')],
        [InlineKeyboardButton("🍲 Обед", callback_data='lunch')],
        [InlineKeyboardButton("🍝 Ужин", callback_data='dinner')],
        [InlineKeyboardButton("❌ Отмена", callback_data='cancel')]
    ]
    
    await update.message.reply_text(
        "👑 Режим администратора\nВыберите категорию для нового рецепта:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CATEGORY

async def category_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора категории"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()
    
    if query.data == 'cancel':
        await query.edit_message_text("❌ Добавление рецепта отменено")
        return ConversationHandler.END
    
    context.user_data['new_recipe'] = {'category': query.data}
    await query.edit_message_text("📝 Введите название рецепта:")
    
    return NAME

async def name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение названия рецепта"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    context.user_data['new_recipe']['name'] = update.message.text
    await update.message.reply_text("🖼 Отправьте фото рецепта:")
    
    return PHOTO

async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение фото рецепта и автоматическое сохранение"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    # Сохраняем информацию о фото
    photo = update.message.photo[-1]
    context.user_data['new_recipe']['photo'] = photo
    
    await update.message.reply_text(
        "📋 Введите состав рецепта (каждый ингредиент с новой строки, формат: • Продукт - количество):\n\n"
        "Пример:\n"
        "• Яйца - 2 шт.\n"
        "• Молоко - 100 мл\n"
        "• Соль - по вкусу"
    )
    
    return INGREDIENTS

async def ingredients_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение состава"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    context.user_data['new_recipe']['ingredients'] = update.message.text
    await update.message.reply_text("👨‍🍳 Введите инструкцию по приготовлению:")
    
    return INSTRUCTIONS

async def instructions_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение инструкций"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    context.user_data['new_recipe']['instructions'] = update.message.text
    await update.message.reply_text(
        "🎥 Введите ссылки на видео-гайды (каждую с новой строки):\n\n"
        "Пример:\n"
        "https://youtube.com/watch?v=123 - Основной рецепт\n"
        "https://youtube.com/watch?v=456 - Альтернативный способ\n\n"
        "Или отправьте '-' если видео нет"
    )
    
    return VIDEOS

async def videos_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение видео-ссылок"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    videos_text = update.message.text
    recipe_data = context.user_data['new_recipe']
    
    try:
        # Генерируем имя файла на английском
        english_filename = transliterate_to_english(recipe_data['name'])
        category = recipe_data['category']
        
        # Формируем путь
        image_filename = f"{english_filename}.jpg"
        image_path = f"images/{category}/{image_filename}"
        full_image_path = Path(image_path)
        
        # Создаем папку если её нет
        full_image_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Скачиваем и сохраняем фото
        photo_file = await recipe_data['photo'].get_file()
        await photo_file.download_to_drive(full_image_path)
        
        # Добавляем рецепт в БД (без видео)
        recipe_id = add_recipe(
            category=category,
            name=recipe_data['name'],
            image_path=image_path,
            ingredients=recipe_data['ingredients'],
            instructions=recipe_data['instructions']
        )
        
        # Добавляем видео-ссылки если они есть
        video_count = 0
        if videos_text.strip() != '-':
            for line in videos_text.split('\n'):
                line = line.strip()
                if line and ('http://' in line or 'https://' in line):
                    # Парсим заголовок если есть
                    if ' - ' in line:
                        url, title = line.split(' - ', 1)
                        add_video_to_recipe(recipe_id, url.strip(), title.strip())
                    else:
                        add_video_to_recipe(recipe_id, line.strip())
                    video_count += 1
        
        await update.message.reply_text(
            f"✅ Рецепт '{recipe_data['name']}' успешно добавлен!\n"
            f"ID рецепта: {recipe_id}\n"
            f"📁 Фото сохранено: {image_path}\n"
            f"🎥 Добавлено видео: {video_count}"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при добавлении рецепта: {e}")
    
    # Очищаем данные
    context.user_data.pop('new_recipe', None)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена добавления рецепта"""
    context.user_data.pop('new_recipe', None)
    await update.message.reply_text("❌ Добавление рецепта отменено")
    return ConversationHandler.END

# Создаем ConversationHandler для добавления рецептов
def get_add_recipe_conversation():
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^/addrecipe$'), start_add_recipe)],
        states={
            CATEGORY: [CallbackQueryHandler(category_chosen, pattern='^(breakfast|lunch|dinner|cancel)$')],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_received)],
            PHOTO: [MessageHandler(filters.PHOTO, photo_received)],
            INGREDIENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ingredients_received)],
            INSTRUCTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, instructions_received)],
            VIDEOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, videos_received)],
        },
        fallbacks=[MessageHandler(filters.Regex('^/cancel$'), cancel)]
    )

async def admin_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка прав администратора"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Без username"
    
    if is_admin(user_id):
        await update.message.reply_text(
            f"✅ Вы администратор!\n"
            f"ID: {user_id}\n"
            f"Username: @{username}\n\n"
            f"Доступные команды:\n"
            f"/addrecipe - добавить рецепт"
        )
    else:
        await update.message.reply_text(
            f"❌ Вы не администратор\n"
            f"ID: {user_id}\n"
            f"Username: @{username}\n\n"
            f"Обратитесь к разработчикам для получения прав"
        )


async def start_change_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало изменения рецепта - ТОЛЬКО ДЛЯ АДМИНОВ"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("🍳 Завтрак", callback_data='change_breakfast')],
        [InlineKeyboardButton("🍲 Обед", callback_data='change_lunch')],
        [InlineKeyboardButton("🍝 Ужин", callback_data='change_dinner')],
        [InlineKeyboardButton("❌ Отмена", callback_data='change_cancel')]
    ]
    
    await update.message.reply_text(
        "👑 Режим администратора\nВыберите категорию рецепта для изменения:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CHANGE_RECIPE_SELECT

async def change_category_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора категории для изменения"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()
    
    if query.data == 'change_cancel':
        await query.edit_message_text("❌ Изменение рецепта отменено")
        return ConversationHandler.END
    
    category = query.data.replace('change_', '')
    recipes = get_recipes_by_category(category)
    
    if not recipes:
        await query.edit_message_text(
            f"😔 В категории '{category}' нет рецептов для изменения",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='change_back')]])
        )
        return CHANGE_RECIPE_SELECT
    
    # Создаем клавиатуру с рецептами
    keyboard = []
    for recipe_id, recipe_name in recipes:
        keyboard.append([InlineKeyboardButton(recipe_name, callback_data=f'change_recipe_{recipe_id}')])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='change_back')])
    
    await query.edit_message_text(
        "Выберите рецепт для изменения:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CHANGE_RECIPE_SELECT

async def change_recipe_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора рецепта для изменения"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()
    
    if query.data == 'change_back':
        keyboard = [
            [InlineKeyboardButton("🍳 Завтрак", callback_data='change_breakfast')],
            [InlineKeyboardButton("🍲 Обед", callback_data='change_lunch')],
            [InlineKeyboardButton("🍝 Ужин", callback_data='change_dinner')],
            [InlineKeyboardButton("❌ Отмена", callback_data='change_cancel')]
        ]
        await query.edit_message_text(
            "Выберите категорию рецепта для изменения:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CHANGE_RECIPE_SELECT
    
    recipe_id = int(query.data.replace('change_recipe_', ''))
    recipe = get_recipe(recipe_id)
    context.user_data['changing_recipe'] = {
        'id': recipe_id,
        'current_recipe': recipe
    }
    
    # Текущие данные рецепта и кнопки для изменения
    recipe_text = (
        f"📝 Рецепт: {recipe[2]}\n\n"
        f"Текущие данные:\n"
        f"🖼 Фото: {recipe[3]}\n"
        f"📋 Ингредиенты: {len(recipe[4].split(chr(10)))} строк\n"
        f"👨‍🍳 Инструкции: {len(recipe[5].split(chr(10)))} строк\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("🖼 Изменить фото", callback_data='change_photo')],
        [InlineKeyboardButton("📋 Изменить состав", callback_data='change_ingredients')],
        [InlineKeyboardButton("👨‍🍳 Изменить инструкцию", callback_data='change_instructions')],
        [InlineKeyboardButton("🎥 Изменить видео", callback_data='change_videos')],
        [InlineKeyboardButton("🗑️ Удалить рецепт", callback_data='change_delete')],
        [InlineKeyboardButton("🔙 Назад к выбору", callback_data='change_back')],
        [InlineKeyboardButton("✅ Завершить", callback_data='change_finish')]
    ]
    
    await query.edit_message_text(
        recipe_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CHANGE_FIELD

async def change_field_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора поля для изменения"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()

    if query.data == 'change_back_to_menu':
        return await change_recipe_selected(update, context)
    
    if query.data == 'change_back':
        # Возвращаемся к выбору категории
        keyboard = [
            [InlineKeyboardButton("🍳 Завтрак", callback_data='change_breakfast')],
            [InlineKeyboardButton("🍲 Обед", callback_data='change_lunch')],
            [InlineKeyboardButton("🍝 Ужин", callback_data='change_dinner')],
            [InlineKeyboardButton("❌ Отмена", callback_data='change_cancel')]
        ]
        await query.edit_message_text(
            "Выберите категорию рецепта для изменения:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CHANGE_RECIPE_SELECT
    
    if query.data == 'change_finish':
        recipe_data = context.user_data.get('changing_recipe', {})
        recipe_id = recipe_data.get('id')
        if recipe_id:
            await query.edit_message_text(f"✅ Изменение рецепта ID {recipe_id} завершено")
        else:
            await query.edit_message_text("✅ Изменение рецепта завершено")
        context.user_data.pop('changing_recipe', None)
        return ConversationHandler.END
    
    if query.data == 'change_delete':
        recipe_data = context.user_data['changing_recipe']
        recipe_id = recipe_data['id']
        recipe_name = recipe_data['current_recipe'][2]
        
        # Подтверждения удаления
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f'confirm_delete_{recipe_id}'),
                InlineKeyboardButton("❌ Нет, отмена", callback_data='cancel_delete')
            ]
        ]
        
        await query.edit_message_text(
            f"⚠️ Вы уверены, что хотите удалить рецепт?\n\n"
            f"📝 '{recipe_name}'\n"
            f"🔢 ID: {recipe_id}\n\n"
            f"Это действие нельзя отменить!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CHANGE_FIELD
    
    field = query.data.replace('change_', '')
    recipe_data = context.user_data['changing_recipe']
    recipe = recipe_data['current_recipe']
    
    if field == 'photo':
        # Показываем текущее фото
        try:
            image_path = BASE_DIR / recipe[3]
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo,
                    caption="📸 Текущее фото рецепта\n\nОтправьте новое фото:"
                )
        except:
            await query.edit_message_text("📸 Не удалось загрузить текущее фото\n\nОтправьте новое фото:")
        else:
            await query.delete_message()
        
        return CHANGE_PHOTO
    
    elif field == 'ingredients':
        await query.edit_message_text(
            f"📋 Текущий состав:\n{recipe[4]}\n\nВведите новый состав:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='change_back_to_menu')]])
        )
        return CHANGE_INGREDIENTS
    
    elif field == 'instructions':
        await query.edit_message_text(
            f"👨‍🍳 Текущая инструкция:\n{recipe[5]}\n\nВведите новую инструкцию:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='change_back_to_menu')]])
        )
        return CHANGE_INSTRUCTIONS
    
    elif field == 'videos':
        videos = get_recipe_videos(recipe_data['id'])
        videos_text = "🎥 Текущие видео-ссылки:\n\n"
        if videos:
            for i, (url, title) in enumerate(videos, 1):
                videos_text += f"{i}. {title or url}\n"
        else:
            videos_text += "Видео-ссылок нет\n"
        
        videos_text += "\nВведите новые видео-ссылки (каждую с новой строки):\n\nПример:\nhttps://youtube.com/watch?v=123 - Основной рецепт\nhttps://youtube.com/watch?v=456 - Альтернативный способ\n\nИли отправьте '-' чтобы удалить все видео"
        
        await query.edit_message_text(
            videos_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='change_back_to_menu')]])
        )
        return CHANGE_VIDEOS

async def change_photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение нового фото"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    recipe_data = context.user_data['changing_recipe']
    recipe_id = recipe_data['id']
    recipe = recipe_data['current_recipe']
    
    try:
        # Получаем новое фото
        photo = update.message.photo[-1]
        
        # Генерируем путь (используем старое имя файла)
        old_image_path = Path(recipe[3])
        new_image_path = BASE_DIR / old_image_path
        
        # Скачиваем и сохраняем новое фото
        photo_file = await photo.get_file()
        await photo_file.download_to_drive(new_image_path)
        
        await update.message.reply_text("✅ Фото успешно обновлено!")
        
        # Возвращаемся к меню изменения
        return await return_to_change_menu(update, context, recipe_data)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при обновлении фото: {e}")
        return await return_to_change_menu(update, context, recipe_data)

async def change_ingredients_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение нового состава"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    recipe_data = context.user_data['changing_recipe']
    recipe_id = recipe_data['id']
    new_ingredients = update.message.text
    
    try:
        # Обновляем состав в БД
        update_recipe(recipe_id, ingredients=new_ingredients)
        
        # Обновляем продукты для поиска
        update_recipe_products(recipe_id, new_ingredients)
        
        await update.message.reply_text("✅ Состав успешно обновлен!")
        
        # Обновляем данные в контексте
        recipe_data['current_recipe'] = get_recipe(recipe_id)
        context.user_data['changing_recipe'] = recipe_data
        
        return await return_to_change_menu(update, context, recipe_data)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при обновлении состава: {e}")
        return await return_to_change_menu(update, context, recipe_data)

async def change_instructions_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение новой инструкции"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    recipe_data = context.user_data['changing_recipe']
    recipe_id = recipe_data['id']
    new_instructions = update.message.text
    
    try:
        # Обновляем инструкции в БД
        update_recipe(recipe_id, instructions=new_instructions)
        
        await update.message.reply_text("✅ Инструкции успешно обновлены!")
        
        # Обновляем данные в контексте
        recipe_data['current_recipe'] = get_recipe(recipe_id)
        context.user_data['changing_recipe'] = recipe_data
        
        return await return_to_change_menu(update, context, recipe_data)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при обновлении инструкций: {e}")
        return await return_to_change_menu(update, context, recipe_data)

async def change_videos_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение новых видео-ссылок"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    recipe_data = context.user_data['changing_recipe']
    recipe_id = recipe_data['id']
    videos_text = update.message.text
    
    try:
        # Удаляем старые видео
        delete_recipe_videos(recipe_id)
        
        # Добавляем новые видео если они есть
        video_count = 0
        if videos_text.strip() != '-':
            for line in videos_text.split('\n'):
                line = line.strip()
                if line and ('http://' in line or 'https://' in line):
                    # Парсим заголовок если есть
                    if ' - ' in line:
                        url, title = line.split(' - ', 1)
                        add_video_to_recipe(recipe_id, url.strip(), title.strip())
                    else:
                        add_video_to_recipe(recipe_id, line.strip())
                    video_count += 1
        
        await update.message.reply_text(f"✅ Видео-ссылки успешно обновлены! Добавлено: {video_count}")
        
        return await return_to_change_menu(update, context, recipe_data)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при обновлении видео: {e}")
        return await return_to_change_menu(update, context, recipe_data)

async def change_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки Назад из полей изменения"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    
    if query:
        await query.answer()
        return await change_recipe_selected(update, context)
    else:
        recipe_data = context.user_data['changing_recipe']
        return await return_to_change_menu(update, context, recipe_data)

async def return_to_change_menu(query_or_update, context: ContextTypes.DEFAULT_TYPE, recipe_data):
    """Возврат в меню изменения рецепта (работает с Update или CallbackQuery)"""
    recipe = recipe_data['current_recipe']
    
    recipe_text = (
        f"📝 Рецепт: {recipe[2]}\n\n"
        f"Текущие данные:\n"
        f"🖼 Фото: {recipe[3]}\n"
        f"📋 Ингредиенты: {len(recipe[4].split(chr(10)))} строк\n"
        f"👨‍🍳 Инструкции: {len(recipe[5].split(chr(10)))} строк\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("🖼 Изменить фото", callback_data='change_photo')],
        [InlineKeyboardButton("📋 Изменить состав", callback_data='change_ingredients')],
        [InlineKeyboardButton("👨‍🍳 Изменить инструкцию", callback_data='change_instructions')],
        [InlineKeyboardButton("🎥 Изменить видео", callback_data='change_videos')],
        [InlineKeyboardButton("🔙 Назад к выбору", callback_data='change_back')],
        [InlineKeyboardButton("✅ Завершить", callback_data='change_finish')]
    ]
    
    # Проверяем что передали - Update или CallbackQuery
    if hasattr(query_or_update, 'edit_message_text'):
        # Это CallbackQuery
        await query_or_update.edit_message_text(
            recipe_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # Это Update с message
        await query_or_update.message.reply_text(
            recipe_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    return CHANGE_FIELD

async def change_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена изменения рецепта"""
    context.user_data.pop('changing_recipe', None)
    await update.message.reply_text("❌ Изменение рецепта отменено")
    return ConversationHandler.END

# Создаем ConversationHandler для изменения рецептов
def get_change_recipe_conversation():
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^/changerecipe$'), start_change_recipe)],
        states={
            CHANGE_RECIPE_SELECT: [
                CallbackQueryHandler(change_category_chosen, pattern='^change_(breakfast|lunch|dinner|cancel)$'),
                CallbackQueryHandler(change_recipe_selected, pattern='^change_recipe_'),
                CallbackQueryHandler(change_back_to_menu_handler, pattern='^change_back$')
            ],
            CHANGE_FIELD: [
                CallbackQueryHandler(change_field_selected, pattern='^change_(photo|ingredients|instructions|videos|delete|back|finish|back_to_menu)$'),  # ← ВКЛЮЧИ back_to_menu сюда
                CallbackQueryHandler(confirm_delete_recipe, pattern='^confirm_delete_'),
                CallbackQueryHandler(cancel_delete_recipe, pattern='^cancel_delete$'),
            ],
            CHANGE_PHOTO: [
                MessageHandler(filters.PHOTO, change_photo_received),
                CallbackQueryHandler(change_back_to_menu_handler, pattern='^change_back_to_menu$'),
            ],
            CHANGE_INGREDIENTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, change_ingredients_received),
                CallbackQueryHandler(change_back_to_menu_handler, pattern='^change_back_to_menu$'),
            ],
            CHANGE_INSTRUCTIONS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, change_instructions_received),
                CallbackQueryHandler(change_back_to_menu_handler, pattern='^change_back_to_menu$'),
            ],
            CHANGE_VIDEOS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, change_videos_received),
                CallbackQueryHandler(change_back_to_menu_handler, pattern='^change_back_to_menu$'),
            ],
        },
        fallbacks=[MessageHandler(filters.Regex('^/cancel$'), change_cancel)]
    )

async def confirm_delete_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение удаления рецепта"""
    if not await check_admin(update, context):
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()
    
    recipe_id = int(query.data.replace('confirm_delete_', ''))
    recipe_data = context.user_data.get('changing_recipe', {})
    
    try:
        # Удаляем рецепт из БД
        delete_recipe_completely(recipe_id)
        
        await query.edit_message_text(
            f"✅ Рецепт ID {recipe_id} успешно удален!\n\n"
            f"Все данные рецепта были полностью удалены из базы данных."
        )
        
        # Очищаем данные
        context.user_data.pop('changing_recipe', None)
        return ConversationHandler.END
        
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка при удалении рецепта: {e}")
        return await return_to_change_menu(update, context, recipe_data)

async def cancel_delete_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена удаления рецепта"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("❌ Удаление рецепта отменено")
    return await return_to_change_menu(update, context, context.user_data['changing_recipe'])

async def change_back_to_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки Назад из полей изменения"""
    query = update.callback_query
    await query.answer()
    
    recipe_data = context.user_data.get('changing_recipe', {})
    if not recipe_data:
        # Используй query для редактирования сообщения
        await query.edit_message_text("❌ Ошибка: данные рецепта не найдены")
        return ConversationHandler.END
    
    # Создаем новый Update из query
    return await return_to_change_menu(query, context, recipe_data)