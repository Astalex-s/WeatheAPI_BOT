"""Inline клавиатуры."""

from telebot import types
from datetime import datetime
from utils.icons import get_weather_icon


def create_forecast_days_keyboard(day_details: dict) -> types.InlineKeyboardMarkup:
    """Создает inline-клавиатуру с днями прогноза."""
    markup = types.InlineKeyboardMarkup()
    sorted_days = sorted(day_details.keys())[:5]
    
    for day in sorted_days:
        day_info = day_details[day]
        day_name = day_info['name']
        date_str = day_info['date']
        avg_temp = day_info['avg_temp']
        weather_icon = day_info.get('weather_icon', '☀️')
        
        # Формат кнопки: "☀️ 25.09 - Четверг (10.6°С)"
        btn_text = f"{weather_icon} {date_str} - {day_name} ({avg_temp:.1f}°С)"
        callback_data = f"day_{day.strftime('%Y-%m-%d')}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=callback_data))
    
    return markup


def create_back_to_forecast_keyboard() -> types.InlineKeyboardMarkup:
    """Создает кнопку 'Назад' для возврата к прогнозу."""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀️ Назад к прогнозу", callback_data="back_to_forecast"))
    return markup


def create_notifications_menu_keyboard(interval: int) -> types.InlineKeyboardMarkup:
    """Создает меню управления уведомлениями."""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔕 Отключить уведомления", callback_data="notif_off"))
    markup.add(types.InlineKeyboardButton(f"⏰ Интервал: {interval}ч", callback_data="notif_interval"))
    return markup

