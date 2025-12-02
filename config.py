import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# На Railway переменные окружения загружаются автоматически
# Просто используем os.getenv с fallback значением
TOKEN = os.getenv('BOT_TOKEN', '8257333823:AAEbtkDNKiMneY0tjF13K78jspxBj0SxUWw')

# Аналогично для админов
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '914844716,856631589,1979853467,1312790260')
ADMIN_IDS = [int(id_str.strip()) for id_str in ADMIN_IDS_STR.split(',') if id_str.strip().isdigit()]

DB_PATH = BASE_DIR / 'recipes.db'