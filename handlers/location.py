"""Обработчики для работы с геолокацией."""

from services.weather_api import get_current_weather
from utils.formatters import format_current_weather
from keyboards.reply import create_main_menu
from services.user_storage import (
    user_data, user_locations, save_user_to_storage, last_weather
)


def register_location_handlers(bot):
    """Регистрирует обработчики геолокации."""
    
    @bot.message_handler(content_types=['location'], func=lambda m: user_data.get(m.from_user.id, {}).get('state') not in ['waiting_extended', 'waiting_forecast_city'])
    def location_handler(message):
        """Обработчик получения местоположения."""
        user_id = message.from_user.id
        
        if not message.location:
            bot.reply_to(message, "❌ Пожалуйста, отправьте ваше местоположение через кнопку '📍 Отправить местоположение'.", reply_markup=create_main_menu())
            return
        
        lat = message.location.latitude
        lon = message.location.longitude
        
        # Получаем название города по координатам
        weather = get_current_weather(lat, lon)
        if weather is None:
            bot.reply_to(message, "❌ Не удалось получить данные о погоде. Попробуйте позже.", reply_markup=create_main_menu())
            return
        
        city_name = weather.get('name', 'Неизвестно')
        
        # Сохраняем местоположение
        user_locations[user_id] = (lat, lon, city_name)
        
        # Сохраняем текущую погоду для уведомлений
        last_weather[user_id] = weather
        
        # Сохраняем в хранилище
        save_user_to_storage(user_id)
        
        # Показываем погоду
        response_text = format_current_weather(weather, city_name)
        response_text += f"\n✅ Местоположение сохранено: {city_name}"
        bot.reply_to(message, response_text, reply_markup=create_main_menu())
    

