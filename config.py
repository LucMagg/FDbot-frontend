import os
from dotenv import load_dotenv

load_dotenv()

BOT_KEY = os.getenv('BOT_KEY')
PREFIX = '/'
DISCORD_API = os.getenv('DISCORD_API_URL')

DB_PATH = f"http://{os.getenv('BACK_HOST')}:{os.getenv('BACK_PORT')}/"