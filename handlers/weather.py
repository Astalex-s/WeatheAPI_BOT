"""Обработчики для работы с погодой."""

from services.weather_api import get_current_weather, get_coordinates, get_forecast_5d3h
from utils.formatters import format_current_weather, format_forecast_5days, format_extended_weather
from keyboards.reply import create_main_menu
from keyboards.inline import create_forecast_days_keyboard
from services.user_storage import user_data, user_locations, save_user_to_storage, last_weather


def register_weather_handlers(bot):
    """Регистрирует обработчики погоды."""
    
    @bot.message_handler(func=lambda m: m.text == "🌤️ Прогноз по городу")
    def weather_by_city_handler(message):
        """Обработчик запроса прогноза по городу."""
        user_id = message.from_user.id
        user_data[user_id]['state'] = 'waiting_city'
        bot.reply_to(message, "Введите название города:", reply_markup=create_main_menu())
    
    @bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get('state') == 'waiting_city')
    def process_city(message):
        """Обрабатывает введенное название города."""
        user_id = message.from_user.id
        city = message.text.strip()
        
        if not city:
            bot.reply_to(message, "❌ Пожалуйста, введите название города.", reply_markup=create_main_menu())
            return
        
        bot.reply_to(message, "🔍 Поиск погоды...", reply_markup=create_main_menu())
        coords = get_coordinates(city)
        if coords is None:
            bot.reply_to(message, "❌ Город не найден. Попробуйте еще раз.", reply_markup=create_main_menu())
            return
        
        lat, lon = coords
        weather = get_current_weather(lat, lon)
        if weather is None:
            bot.reply_to(message, "❌ Не удалось получить данные о погоде. Попробуйте позже.", reply_markup=create_main_menu())
            return
        
        response_text = format_current_weather(weather, city)
        bot.reply_to(message, response_text, reply_markup=create_main_menu())
        user_data[user_id]['state'] = 'main'
    
    @bot.message_handler(func=lambda m: m.text == "📅 Прогноз на 5 дней")
    def forecast_5days_handler(message):
        """Обработчик прогноза на 5 дней."""
        user_id = message.from_user.id
        
        # Проверяем, есть ли сохраненное местоположение
        if user_id in user_locations:
            # Используем сохраненное местоположение
            lat, lon, city_name = user_locations[user_id]
            bot.reply_to(message, "🔍 Загрузка прогноза...", reply_markup=create_main_menu())
            forecast = get_forecast_5d3h(lat, lon)
            if forecast is None:
                bot.reply_to(message, "❌ Не удалось получить прогноз погоды. Попробуйте позже.", reply_markup=create_main_menu())
                return
            
            text, day_details = format_forecast_5days(forecast)
            
            # Сохраняем данные для навигации
            user_data[user_id]['forecast_data'] = day_details
            
            # Создаем inline-клавиатуру с днями
            markup = create_forecast_days_keyboard(day_details)
            
            msg = bot.reply_to(message, text, reply_markup=markup)
            user_data[user_id]['forecast_message_id'] = msg.message_id
        else:
            # Просим ввести город или отправить местоположение
            user_data[user_id]['state'] = 'waiting_forecast_city'
            bot.reply_to(message, "Введите название города или отправьте местоположение:", reply_markup=create_main_menu())
    
    @bot.message_handler(content_types=['location'], func=lambda m: user_data.get(m.from_user.id, {}).get('state') == 'waiting_forecast_city')
    def process_forecast_location(message):
        """Обрабатывает геолокацию для прогноза на 5 дней."""
        user_id = message.from_user.id
        lat = message.location.latitude
        lon = message.location.longitude
        
        # Получаем название города по координатам
        weather = get_current_weather(lat, lon)
        if weather is None:
            bot.reply_to(message, "❌ Не удалось получить данные о погоде. Попробуйте позже.", reply_markup=create_main_menu())
            return
        
        city_name = weather.get('name', 'Неизвестно')
        
        bot.reply_to(message, "🔍 Загрузка прогноза...", reply_markup=create_main_menu())
        forecast = get_forecast_5d3h(lat, lon)
        if forecast is None:
            bot.reply_to(message, "❌ Не удалось получить прогноз погоды. Попробуйте позже.", reply_markup=create_main_menu())
            return
        
        text, day_details = format_forecast_5days(forecast)
        
        # Сохраняем данные для навигации
        user_data[user_id]['forecast_data'] = day_details
        
        # Создаем inline-клавиатуру с днями
        markup = create_forecast_days_keyboard(day_details)
        
        msg = bot.reply_to(message, text, reply_markup=markup)
        user_data[user_id]['forecast_message_id'] = msg.message_id
        user_data[user_id]['state'] = 'main'
    
    @bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get('state') == 'waiting_forecast_city' and m.content_type == 'text')
    def process_forecast_city(message):
        """Обрабатывает введенный город для прогноза на 5 дней."""
        user_id = message.from_user.id
        
        # Используем город
        city = message.text.strip()
        if not city:
            bot.reply_to(message, "❌ Пожалуйста, введите название города или отправьте местоположение.", reply_markup=create_main_menu())
            return
        
        coords = get_coordinates(city)
        if coords is None:
            bot.reply_to(message, "❌ Город не найден. Попробуйте еще раз.", reply_markup=create_main_menu())
            return
        
        lat, lon = coords
        city_name = city
        
        bot.reply_to(message, "🔍 Загрузка прогноза...", reply_markup=create_main_menu())
        forecast = get_forecast_5d3h(lat, lon)
        if forecast is None:
            bot.reply_to(message, "❌ Не удалось получить прогноз погоды. Попробуйте позже.", reply_markup=create_main_menu())
            return
        
        text, day_details = format_forecast_5days(forecast)
        
        # Сохраняем данные для навигации
        user_data[user_id]['forecast_data'] = day_details
        
        # Создаем inline-клавиатуру с днями
        markup = create_forecast_days_keyboard(day_details)
        
        msg = bot.reply_to(message, text, reply_markup=markup)
        user_data[user_id]['forecast_message_id'] = msg.message_id
        user_data[user_id]['state'] = 'main'
    
    @bot.message_handler(func=lambda m: m.text == "📊 Расширенные данные")
    def extended_data_handler(message):
        """Обработчик расширенных данных."""
        user_id = message.from_user.id
        user_data[user_id]['state'] = 'waiting_extended'
        bot.reply_to(message, "Введите название города или отправьте местоположение:", reply_markup=create_main_menu())
    
    @bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get('state') == 'waiting_extended' and m.content_type == 'text')
    def process_extended_text(message):
        """Обрабатывает запрос расширенных данных по тексту (город)."""
        user_id = message.from_user.id
        city = message.text.strip()
        
        if not city:
            bot.reply_to(message, "❌ Пожалуйста, введите название города или отправьте местоположение.", reply_markup=create_main_menu())
            return
        
        coords = get_coordinates(city)
        if coords is None:
            bot.reply_to(message, "❌ Город не найден. Попробуйте еще раз.", reply_markup=create_main_menu())
            return
        
        lat, lon = coords
        city_name = city
        
        bot.reply_to(message, "🔍 Загрузка расширенных данных...", reply_markup=create_main_menu())
        weather = get_current_weather(lat, lon)
        if weather is None:
            bot.reply_to(message, "❌ Не удалось получить данные о погоде. Попробуйте позже.", reply_markup=create_main_menu())
            return
        
        extended_text = format_extended_weather(weather, city_name, lat, lon)
        bot.reply_to(message, extended_text, reply_markup=create_main_menu())
        
        user_data[user_id]['state'] = 'main'
    
    @bot.message_handler(content_types=['location'], func=lambda m: user_data.get(m.from_user.id, {}).get('state') == 'waiting_extended')
    def process_extended_location(message):
        """Обрабатывает запрос расширенных данных по геолокации."""
        user_id = message.from_user.id
        lat = message.location.latitude
        lon = message.location.longitude
        
        bot.reply_to(message, "🔍 Загрузка расширенных данных...", reply_markup=create_main_menu())
        weather = get_current_weather(lat, lon)
        if weather is None:
            bot.reply_to(message, "❌ Не удалось получить данные о погоде. Попробуйте позже.", reply_markup=create_main_menu())
            return
        
        city_name = weather.get('name', 'Неизвестно')
        
        extended_text = format_extended_weather(weather, city_name, lat, lon)
        bot.reply_to(message, extended_text, reply_markup=create_main_menu())
        
        user_data[user_id]['state'] = 'main'

