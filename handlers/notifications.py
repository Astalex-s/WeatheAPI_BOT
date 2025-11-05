"""Обработчики для работы с уведомлениями."""

from services.weather_api import get_current_weather
from keyboards.reply import create_main_menu
from keyboards.inline import create_notifications_menu_keyboard
from services.user_storage import (
    user_data, user_locations, notifications_enabled, notification_intervals,
    save_user_to_storage, last_weather, last_notification_check
)


def register_notification_handlers(bot):
    """Регистрирует обработчики уведомлений."""
    
    @bot.message_handler(func=lambda m: m.text == "🔔 Погодные уведомления")
    def notifications_handler(message):
        """Обработчик управления уведомлениями."""
        user_id = message.from_user.id
        
        if user_id not in notifications_enabled:
            notifications_enabled[user_id] = False
        if user_id not in notification_intervals:
            notification_intervals[user_id] = 2
        
        if notifications_enabled[user_id]:
            # Показываем меню управления уведомлениями
            interval = notification_intervals.get(user_id, 2)
            markup = create_notifications_menu_keyboard(interval)
            bot.reply_to(message, f"🔔 Уведомления включены (интервал: {interval}ч)\n\nВыберите действие:", reply_markup=markup)
        else:
            if user_id not in user_locations:
                bot.reply_to(message, "❌ Сначала отправьте ваше местоположение для работы уведомлений", reply_markup=create_main_menu())
                return
            
            notifications_enabled[user_id] = True
            if user_id not in notification_intervals:
                notification_intervals[user_id] = 2
            
            # Сохраняем текущую погоду для отслеживания изменений
            lat, lon, city_name = user_locations[user_id]
            weather = get_current_weather(lat, lon)
            if weather:
                last_weather[user_id] = weather
            
            save_user_to_storage(user_id)  # Сохраняем изменения
            interval = notification_intervals[user_id]
            bot.reply_to(message, f"🔔 Уведомления включены. Бот будет проверять погоду каждые {interval} часов.", reply_markup=create_main_menu())
    
    @bot.callback_query_handler(func=lambda c: c.data == "notif_off")
    def notifications_off_callback(callback):
        """Обработчик отключения уведомлений."""
        user_id = callback.from_user.id
        notifications_enabled[user_id] = False
        # Очищаем данные о погоде и времени проверки при отключении
        if user_id in last_weather:
            del last_weather[user_id]
        if user_id in last_notification_check:
            del last_notification_check[user_id]
        save_user_to_storage(user_id)
        bot.answer_callback_query(callback.id, "🔕 Уведомления отключены")
        bot.edit_message_text(
            "🔕 Уведомления отключены",
            callback.message.chat.id,
            callback.message.message_id
        )
    
    @bot.callback_query_handler(func=lambda c: c.data == "notif_interval")
    def notifications_interval_callback(callback):
        """Обработчик настройки интервала уведомлений."""
        user_id = callback.from_user.id
        user_data[user_id]['state'] = 'waiting_notif_interval'
        bot.answer_callback_query(callback.id)
        bot.edit_message_text(
            "⏰ Введите интервал уведомлений в часах (от 1 до 24):",
            callback.message.chat.id,
            callback.message.message_id
        )
    
    @bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get('state') == 'waiting_notif_interval')
    def process_notification_interval(message):
        """Обрабатывает введенный интервал уведомлений."""
        user_id = message.from_user.id
        try:
            interval = int(message.text.strip())
            if interval < 1 or interval > 24:
                bot.reply_to(message, "❌ Интервал должен быть от 1 до 24 часов.", reply_markup=create_main_menu())
                return
            
            notification_intervals[user_id] = interval
            save_user_to_storage(user_id)
            bot.reply_to(message, f"✅ Интервал уведомлений установлен: {interval} часов.", reply_markup=create_main_menu())
            user_data[user_id]['state'] = 'main'
        except ValueError:
            bot.reply_to(message, "❌ Пожалуйста, введите число от 1 до 24.", reply_markup=create_main_menu())

