"""Функции форматирования сообщений."""

from datetime import datetime
from collections import defaultdict
from services.weather_api import get_air_pollution, analyze_air_pollution, format_air_pollution_report
from utils.icons import get_weather_icon


def format_current_weather(weather_data: dict, city_name: str = None) -> str:
    """Форматирует текущую погоду для отображения."""
    temp = weather_data['main']['temp']
    feels_like = weather_data['main']['feels_like']
    humidity = weather_data['main']['humidity']
    pressure = weather_data['main']['pressure']
    wind_speed = weather_data.get('wind', {}).get('speed', 0)
    wind_deg = weather_data.get('wind', {}).get('deg', 0)
    description = weather_data['weather'][0]['description'].capitalize()
    city = city_name or weather_data.get('name', 'Неизвестно')
    
    wind_direction = ""
    if wind_deg:
        directions = ["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"]
        wind_direction = directions[int((wind_deg + 22.5) / 45) % 8]
    
    text = f"🌤️ Погода в {city}\n\n"
    text += f"🌡️ Температура: {temp}°C (ощущается как {feels_like}°C)\n"
    text += f"☁️ {description}\n"
    text += f"💧 Влажность: {humidity}%\n"
    text += f"🌬️ Ветер: {wind_speed} м/с {wind_direction}\n"
    text += f"📊 Давление: {pressure} гПа\n"
    
    return text


def format_extended_weather(weather_data: dict, city_name: str = None, lat: float = None, lon: float = None) -> str:
    """Форматирует расширенные данные о погоде."""
    text = format_current_weather(weather_data, city_name)
    
    # Дополнительные данные из текущей погоды
    cloudiness = weather_data.get('clouds', {}).get('all', 0)
    visibility = weather_data.get('visibility', 0) / 1000 if weather_data.get('visibility') else None
    
    # Восход и закат
    sunrise = datetime.fromtimestamp(weather_data['sys']['sunrise'])
    sunset = datetime.fromtimestamp(weather_data['sys']['sunset'])
    
    text += f"\n📈 Расширенные данные:\n"
    text += f"☁️ Облачность: {cloudiness}%\n"
    if visibility:
        text += f"👁️ Видимость: {visibility} км\n"
    text += f"🌅 Восход солнца: {sunrise.strftime('%H:%M')}\n"
    text += f"🌇 Закат солнца: {sunset.strftime('%H:%M')}\n"
    
    # Загрязнение воздуха
    if lat and lon:
        air_pollution = get_air_pollution(lat, lon)
        if air_pollution is not None:
            try:
                air_analysis = analyze_air_pollution(air_pollution, extended=True)
                text += f"\n{format_air_pollution_report(air_analysis)}"
            except Exception:
                text += f"\n⚠️ Данные о загрязнении воздуха недоступны\n"
        else:
            text += f"\n⚠️ Данные о загрязнении воздуха недоступны\n"
    
    return text


def format_forecast_5days(forecast_data: dict) -> tuple[str, dict]:
    """Форматирует прогноз на 5 дней и возвращает текст и данные по дням."""
    list_data = forecast_data['list']
    city_name = forecast_data['city']['name']
    
    # Группируем по дням
    days_data = defaultdict(list)
    for item in list_data:
        dt = datetime.fromtimestamp(item['dt'])
        day_key = dt.date()
        days_data[day_key].append(item)
    
    # Сортируем дни
    sorted_days = sorted(days_data.keys())[:5]
    
    # Простое сообщение без детального текста
    text = f"📅 Прогноз погоды на 5 дней в {city_name}\n\nВыберите день для подробного прогноза:"
    
    day_details = {}
    day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    
    for day in sorted_days:
        day_items = days_data[day]
        day_name = day_names[day.weekday()]
        date_str = day.strftime('%d.%m')
        
        # Берем средние значения за день
        temps = [item['main']['temp'] for item in day_items]
        feels_like_temps = [item['main']['feels_like'] for item in day_items]
        min_temp = min(temps)
        max_temp = max(temps)
        avg_temp = sum(temps) / len(temps)
        avg_feels_like = sum(feels_like_temps) / len(feels_like_temps)
        
        # Основное описание (берем дневное значение) для иконки
        main_weather = day_items[len(day_items)//2]['weather'][0]['main']
        weather_icon = get_weather_icon(main_weather)
        
        day_details[day] = {
            'name': day_name,
            'date': date_str,
            'items': day_items,
            'min_temp': min_temp,
            'max_temp': max_temp,
            'avg_temp': avg_temp,
            'avg_feels_like': avg_feels_like,
            'weather_icon': weather_icon
        }
    
    return text, day_details


def format_day_details(day_data: dict, day_key: datetime.date) -> str:
    """Форматирует детальную информацию о дне."""
    day_name = day_data['name']
    date_str = day_data['date']
    items = day_data['items']
    
    text = f"📆 {day_name}, {date_str}\n\n"
    
    for item in items:
        dt = datetime.fromtimestamp(item['dt'])
        time_str = dt.strftime('%H:%M')
        temp = item['main']['temp']
        feels_like = item['main']['feels_like']
        humidity = item['main']['humidity']
        pressure = item['main']['pressure']
        wind_speed = item.get('wind', {}).get('speed', 0)
        description = item['weather'][0]['description'].capitalize()
        
        text += f"🕐 {time_str}\n"
        text += f"   🌡️ {temp}°C (ощущается как {feels_like}°C)\n"
        text += f"   ☁️ {description}\n"
        text += f"   💧 Влажность: {humidity}%\n"
        text += f"   🌬️ Ветер: {wind_speed} м/с\n"
        text += f"   📊 Давление: {pressure} гПа\n\n"
    
    return text


def format_cities_comparison(city1: str, weather1: dict, city2: str, weather2: dict) -> str:
    """Форматирует сравнение двух городов в текстовом виде построчно."""
    temp1 = weather1['main']['temp']
    temp2 = weather2['main']['temp']
    feels1 = weather1['main']['feels_like']
    feels2 = weather2['main']['feels_like']
    humidity1 = weather1['main']['humidity']
    humidity2 = weather2['main']['humidity']
    wind1 = weather1.get('wind', {}).get('speed', 0)
    wind2 = weather2.get('wind', {}).get('speed', 0)
    pressure1 = weather1['main']['pressure']
    pressure2 = weather2['main']['pressure']
    desc1 = weather1['weather'][0]['description'].capitalize()
    desc2 = weather2['weather'][0]['description'].capitalize()
    
    text = f"📊 Сравнение городов\n\n"
    text += f"🏙️ {city1} vs {city2}\n\n"
    
    text += f"🌡️ Температура:\n"
    text += f"   {city1}: {temp1}°C\n"
    text += f"   {city2}: {temp2}°C\n\n"
    
    text += f"🌡️ Ощущается как:\n"
    text += f"   {city1}: {feels1}°C\n"
    text += f"   {city2}: {feels2}°C\n\n"
    
    text += f"☁️ Погода:\n"
    text += f"   {city1}: {desc1}\n"
    text += f"   {city2}: {desc2}\n\n"
    
    text += f"💧 Влажность:\n"
    text += f"   {city1}: {humidity1}%\n"
    text += f"   {city2}: {humidity2}%\n\n"
    
    text += f"🌬️ Ветер:\n"
    text += f"   {city1}: {wind1:.1f} м/с\n"
    text += f"   {city2}: {wind2:.1f} м/с\n\n"
    
    text += f"📊 Давление:\n"
    text += f"   {city1}: {pressure1} гПа\n"
    text += f"   {city2}: {pressure2} гПа\n"
    
    # Разница
    diff = temp1 - temp2
    if abs(diff) > 0.1:
        text += f"\n💡 Разница температур: {abs(diff):.1f}°C\n"
        if diff > 0:
            text += f"   В {city1} теплее на {diff:.1f}°C\n"
        else:
            text += f"   В {city2} теплее на {abs(diff):.1f}°C\n"
    
    return text

