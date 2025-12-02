import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent

TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    print("DEBUG: All env vars:", dict(os.environ))
    sys.exit("BOT_TOKEN not set")

ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = []
if ADMIN_IDS_STR:
    ADMIN_IDS = [int(id_str.strip()) for id_str in ADMIN_IDS_STR.split(',')]

DB_PATH = BASE_DIR / 'recipes.db'