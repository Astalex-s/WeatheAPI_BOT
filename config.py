"""Конфигурация бота."""

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OW_API_KEY = os.getenv("OW_API_KEY")

if not BOT_TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена")

if not OW_API_KEY:
    raise ValueError("Переменная окружения OW_API_KEY не установлена")

