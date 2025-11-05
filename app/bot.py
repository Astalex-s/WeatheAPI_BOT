"""Инициализация бота и регистрация всех обработчиков."""

import telebot
import threading
from config import BOT_TOKEN
from services.user_storage import load_all_users_from_storage
from services.notifications import check_weather_notifications
from handlers.commands import register_command_handlers
from handlers.weather import register_weather_handlers
from handlers.location import register_location_handlers
from handlers.callbacks import register_callback_handlers
from handlers.comparisons import register_comparison_handlers
from handlers.notifications import register_notification_handlers
from handlers.inline import register_inline_handlers


# Создаем экземпляр бота
bot = telebot.TeleBot(BOT_TOKEN)


def register_all_handlers():
    """Регистрирует все обработчики бота."""
    register_command_handlers(bot)
    register_weather_handlers(bot)
    register_location_handlers(bot)
    register_callback_handlers(bot)
    register_comparison_handlers(bot)
    register_notification_handlers(bot)
    register_inline_handlers(bot)


def start_notification_thread():
    """Запускает поток для проверки уведомлений."""
    notification_thread = threading.Thread(target=check_weather_notifications, args=(bot,), daemon=True)
    notification_thread.start()


def main():
    """Основная функция запуска бота."""
    # Загружаем данные всех пользователей при старте
    load_all_users_from_storage()
    
    # Регистрируем все обработчики
    register_all_handlers()
    
    # Запускаем поток уведомлений
    start_notification_thread()
    
    # Запускаем бота
    print("Бот запущен!")
    bot.infinity_polling()


if __name__ == "__main__":
    main()

