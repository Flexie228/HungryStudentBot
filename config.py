import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

# Используйте os.environ[] - он выбрасывает KeyError если переменной нет
# или os.environ.get() с значением по умолчанию
try:
    TOKEN = os.environ['BOT_TOKEN']  # Гарантированно возвращает str или KeyError
except KeyError:
    raise ValueError("BOT_TOKEN не установлен. Создайте файл .env")

# Для ADMIN_IDS используем get с дефолтным значением
ADMIN_IDS_STR = os.environ.get('ADMIN_IDS', '')
ADMIN_IDS = []
if ADMIN_IDS_STR:
    try:
        ADMIN_IDS = [int(id_str.strip()) for id_str in ADMIN_IDS_STR.split(',')]
    except ValueError:
        print("Ошибка: ADMIN_IDS должен содержать числа, разделенные запятыми")
        ADMIN_IDS = []

DB_PATH = BASE_DIR / 'recipes.db'