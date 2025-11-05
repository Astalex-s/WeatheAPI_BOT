"""Утилиты для работы с иконками погоды."""

def get_weather_icon(weather_code: str) -> str:
    """Возвращает иконку погоды по коду."""
    icons = {
        'clear': '☀️',
        'clouds': '☁️',
        'rain': '🌧️',
        'drizzle': '🌦️',
        'thunderstorm': '⛈️',
        'snow': '❄️',
        'mist': '🌫️',
        'fog': '🌫️'
    }
    weather_lower = weather_code.lower()
    for key, icon in icons.items():
        if key in weather_lower:
            return icon
    return '☀️'  # По умолчанию

