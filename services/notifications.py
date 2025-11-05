"""Сервис для работы с уведомлениями."""

import time
from datetime import datetime, timedelta
from collections import defaultdict
from telebot import TeleBot
from services.weather_api import get_current_weather, get_forecast_5d3h
from utils.formatters import format_current_weather
from services.user_storage import (
    user_locations, notifications_enabled, notification_intervals,
    last_weather, last_notification_check
)


def check_weather_notifications(bot: TeleBot):
    """Проверяет погоду и отправляет уведомления."""
    while True:
        # Проверяем каждую минуту, нужно ли отправить уведомление кому-то
        time.sleep(60)
        
        current_time = datetime.now()
        
        # Создаем копию словаря для безопасной итерации
        users_to_check = list(notifications_enabled.items())
        
        for user_id, enabled in users_to_check:
            # Проверяем, что уведомления все еще включены
            if not enabled or user_id not in notifications_enabled or not notifications_enabled[user_id]:
                continue
            
            if user_id not in user_locations:
                continue
            
            # Получаем интервал для пользователя
            interval_h = notification_intervals.get(user_id, 2)
            interval_seconds = interval_h * 3600
            
            # Проверяем, прошло ли достаточно времени с последней проверки
            if user_id in last_notification_check:
                last_check = last_notification_check[user_id]
                elapsed = (current_time - last_check).total_seconds()
                if elapsed < interval_seconds:
                    continue  # Еще не прошло достаточно времени
            
            # Обновляем время последней проверки
            last_notification_check[user_id] = current_time
            
            try:
                lat, lon, city_name = user_locations[user_id]
                weather = get_current_weather(lat, lon)
                if weather is None:
                    continue
                
                # Проверяем на дождь завтра
                forecast = get_forecast_5d3h(lat, lon)
                if forecast is None:
                    continue
                
                tomorrow = (datetime.now() + timedelta(days=1)).date()
                
                # Группируем прогноз по дням
                list_data = forecast.get('list', [])
                days_data = defaultdict(list)
                for item in list_data:
                    dt = datetime.fromtimestamp(item['dt'])
                    if dt.date() == tomorrow:
                        days_data[tomorrow].append(item)
                
                rain_tomorrow = False
                if tomorrow in days_data:
                    for item in days_data[tomorrow]:
                        weather_main = item['weather'][0]['main'].lower()
                        if 'rain' in weather_main or 'drizzle' in weather_main or 'storm' in weather_main:
                            rain_tomorrow = True
                            break
                
                # Проверяем изменение погоды
                weather_changed = False
                if user_id in last_weather:
                    old_weather = last_weather[user_id]
                    old_temp = old_weather['main']['temp']
                    new_temp = weather['main']['temp']
                    
                    if abs(old_temp - new_temp) > 5:  # Изменение более 5 градусов
                        weather_changed = True
                
                # Отправляем уведомления
                notification_text = f"🔔 Уведомление о погоде в {city_name}\n\n"
                send_notification = False
                
                if rain_tomorrow:
                    notification_text += "⚠️ Завтра ожидается дождь! Не забудьте зонт.\n\n"
                    send_notification = True
                
                if weather_changed:
                    old_temp = last_weather[user_id]['main']['temp']
                    new_temp = weather['main']['temp']
                    diff = new_temp - old_temp
                    if diff > 0:
                        notification_text += f"📈 Температура повысилась на {diff:.1f}°C\n"
                    else:
                        notification_text += f"📉 Температура понизилась на {abs(diff):.1f}°C\n"
                    send_notification = True
                
                # Если это первая проверка, отправляем базовую информацию
                if user_id not in last_weather:
                    send_notification = True
                    notification_text = f"🔔 Уведомления активированы для {city_name}\n\n"
                    notification_text += format_current_weather(weather, city_name)
                
                if send_notification:
                    try:
                        bot.send_message(user_id, notification_text)
                    except Exception:
                        pass  # Пользователь заблокировал бота или ошибка
                
                # Сохраняем текущую погоду
                last_weather[user_id] = weather
                
            except Exception:
                continue  # Пропускаем ошибки

