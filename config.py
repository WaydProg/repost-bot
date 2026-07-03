import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL', '')  # Должен быть форумом!
SOURCE_CHANNELS = [chan.strip() for chan in os.getenv('SOURCE_CHANNELS', '').split(',') if chan.strip()]
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

# Настройки для форумов
TOPIC_CACHE_TIMEOUT = 3600  # 1 час кэширования тем
MAX_TOPICS_CREATE_PER_DAY = 50  # Лимит создания тем

# Проверка обязательных настроек
assert BOT_TOKEN, "BOT_TOKEN не установлен"
assert API_ID, "API_ID не установлен"
assert API_HASH, "API_HASH не установлен"
assert TARGET_CHANNEL, "TARGET_CHANNEL не установлен"
assert SOURCE_CHANNELS, "SOURCE_CHANNELS не установлены"