import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import TOKEN
from database.db import init_db
from handlers.main_handler import start, button_handler
from handlers.admin import get_add_recipe_conversation, admin_check, get_change_recipe_conversation
from handlers.main_handler import handle_product_search
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

def main():
    # Инициализация БД
    init_db()
    
    # Создание приложения
    application = Application.builder().token(TOKEN).build()
    
    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_check))
    application.add_handler(get_add_recipe_conversation())
    application.add_handler(get_change_recipe_conversation())
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_search))
    
    # Запуск бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()