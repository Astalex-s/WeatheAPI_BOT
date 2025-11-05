"""Обработчики inline-режима.

Этот файл является модулем и не предназначен для прямого запуска.
Для запуска бота используйте: python main.py
или: python bot.py
"""

import hashlib
from telebot import types
from services.weather_api import get_current_weather, get_coordinates, get_forecast_5d3h
from utils.formatters import format_current_weather, format_forecast_5days
from keyboards.inline import create_forecast_days_keyboard
from services.user_storage import user_data


def register_inline_handlers(bot):
    """Регистрирует обработчики inline-режима."""
    
    @bot.inline_handler(func=lambda query: len(query.query) > 0)
    def query_text(inline_query):
        """Обработчик inline-запросов для поиска городов."""
        query = inline_query.query.strip()
        
        if not query or len(query) < 2:
            return
        
        # Получаем координаты города
        coords = get_coordinates(query)
        if coords is None:
            return  # Город не найден, просто игнорируем
        
        lat, lon = coords
        weather = get_current_weather(lat, lon)
        if weather is None:
            return  # Не удалось получить погоду, игнорируем
        
        temp = weather['main']['temp']
        feels_like = weather['main']['feels_like']
        description = weather['weather'][0]['description'].capitalize()
        city_name = weather.get('name', query)
        
        # Формируем текст результата
        result_text = f"🌤️ Погода в {city_name}\n\n"
        result_text += f"🌡️ Температура: {temp}°C (ощущается как {feels_like}°C)\n"
        result_text += f"☁️ {description}\n\n"
        result_text += f"Нажмите для получения полного прогноза на 5 дней"
        
        # Создаем inline-результат
        result_id = hashlib.md5(f"{lat}_{lon}_{city_name}".encode()).hexdigest()
        
        result = types.InlineQueryResultArticle(
            id=result_id,
            title=f"{city_name}: {temp}°C - {description}",
            description=f"Ощущается как {feels_like}°C",
            input_message_content=types.InputTextMessageContent(
                message_text=result_text
            ),
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    text="📅 Прогноз на 5 дней",
                    callback_data=f"inline_forecast_{lat}_{lon}"
                )
            )
        )
        
        bot.answer_inline_query(inline_query.id, [result], cache_time=300)
    
    @bot.callback_query_handler(func=lambda c: c.data.startswith('inline_forecast_'))
    def inline_forecast_callback(callback):
        """Обработчик inline-кнопки для прогноза на 5 дней."""
        user_id = callback.from_user.id
        
        # Извлекаем координаты из callback_data
        try:
            parts = callback.data.split('_')
            lat = float(parts[2])
            lon = float(parts[3])
        except (ValueError, IndexError):
            bot.answer_callback_query(callback.id, "❌ Ошибка: неверные данные")
            return
        
        forecast = get_forecast_5d3h(lat, lon)
        if forecast is None:
            bot.answer_callback_query(callback.id, "❌ Не удалось получить прогноз")
            return
        
        text, day_details = format_forecast_5days(forecast)
        
        # Сохраняем данные для навигации
        user_data[user_id]['forecast_data'] = day_details
        
        # Создаем inline-клавиатуру с днями
        markup = create_forecast_days_keyboard(day_details)
        
        bot.edit_message_text(
            text,
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=markup
        )
        bot.answer_callback_query(callback.id)

