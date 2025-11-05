"""API для работы с OpenWeatherMap."""

import os
from dotenv import load_dotenv
import time
from typing import Optional
import requests
import json
import hashlib
from pathlib import Path


load_dotenv()

OW_API_KEY = os.getenv("OW_API_KEY")
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL = 600  # 10 минут в секундах

# Словарь для перевода описаний погоды на русский
WEATHER_DESCRIPTIONS = {
    'clear sky': 'ясно',
    'few clouds': 'небольшая облачность',
    'scattered clouds': 'переменная облачность',
    'broken clouds': 'облачно',
    'shower rain': 'ливень',
    'rain': 'дождь',
    'thunderstorm': 'гроза',
    'snow': 'снег',
    'mist': 'туман',
    'fog': 'туман',
    'haze': 'дымка',
    'dust': 'пыль',
    'sand': 'песчаная буря',
    'ash': 'пепел',
    'squall': 'шквал',
    'tornado': 'торнадо',
    'overcast clouds': 'пасмурно',
    'light rain': 'легкий дождь',
    'moderate rain': 'умеренный дождь',
    'heavy rain': 'сильный дождь',
    'light snow': 'легкий снег',
    'moderate snow': 'умеренный снег',
    'heavy snow': 'сильный снег',
    'freezing rain': 'ледяной дождь',
    'light intensity drizzle': 'легкая морось',
    'drizzle': 'морось',
    'heavy intensity drizzle': 'сильная морось',
    'light intensity shower rain': 'легкий ливень',
    'heavy intensity shower rain': 'сильный ливень',
    'ragged shower rain': 'прерывистый ливень',
    'light thunderstorm': 'легкая гроза',
    'thunderstorm with light rain': 'гроза с легким дождем',
    'thunderstorm with rain': 'гроза с дождем',
    'thunderstorm with heavy rain': 'гроза с сильным дождем',
    'light snow': 'легкий снег',
    'sleet': 'мокрый снег',
    'light shower sleet': 'легкий снег с дождем',
    'shower sleet': 'снег с дождем',
    'light rain and snow': 'легкий дождь и снег',
    'rain and snow': 'дождь и снег',
    'light shower snow': 'легкий снегопад',
    'shower snow': 'снегопад',
    'heavy shower snow': 'сильный снегопад'
}


def get_cache_key(lat: float, lon: float, endpoint: str) -> str:
    """Создает ключ кэша на основе координат и эндпоинта."""
    key_str = f"{lat:.4f},{lon:.4f},{endpoint}"
    return hashlib.md5(key_str.encode()).hexdigest()

def get_cache_path(lat: float, lon: float, endpoint: str) -> Path:
    """Возвращает путь к файлу кэша."""
    cache_key = get_cache_key(lat, lon, endpoint)
    return CACHE_DIR / f"{cache_key}.json"

def get_from_cache(lat: float, lon: float, endpoint: str) -> Optional[dict]:
    """Получает данные из кэша, если они не устарели."""
    cache_path = get_cache_path(lat, lon, endpoint)
    if not cache_path.exists():
        return None
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
        
        # Проверяем, не устарел ли кэш
        if time.time() - cached_data.get('timestamp', 0) < CACHE_TTL:
            return cached_data.get('data')
        else:
            # Удаляем устаревший кэш
            cache_path.unlink()
            return None
    except Exception:
        return None

def save_to_cache(lat: float, lon: float, endpoint: str, data: dict):
    """Сохраняет данные в кэш."""
    cache_path = get_cache_path(lat, lon, endpoint)
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': time.time(),
                'data': data
            }, f, ensure_ascii=False)
    except Exception:
        pass  # Игнорируем ошибки кэширования

def translate_weather_description(description: str) -> str:
    """Переводит описание погоды на русский язык."""
    desc_lower = description.lower()
    return WEATHER_DESCRIPTIONS.get(desc_lower, description)

def request_with_retries(url: str, max_retries: int = 3) -> Optional[requests.Response]:
    """HTTP GET с ретраями при 429/5xx и экспоненциальной паузой (1s, 2s, 4s).
    Возвращает None при ошибках вместо исключений."""
    delay_seconds = 1
    last_exc: Optional[BaseException] = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, timeout=15)
            # 4xx ошибки - клиентские ошибки, не ретраим
            if 400 <= resp.status_code < 500:
                return None
            # 429 и 5xx - серверные ошибки, ретраим
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                if attempt < max_retries:
                    time.sleep(delay_seconds)
                    delay_seconds *= 2
                    continue
                return None
            return resp
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            if attempt < max_retries:
                time.sleep(delay_seconds)
                delay_seconds *= 2
                continue
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries:
                time.sleep(delay_seconds)
                delay_seconds *= 2
                continue
    # После всех ретраев возвращаем None вместо исключения
    return None

def get_current_weather(lat: float, lon: float) -> Optional[dict]:
    """Возвращает текущую погоду по координатам через /data/2.5/weather.
    Возвращает None при ошибках вместо исключений."""
    if not OW_API_KEY:
        return None
    
    # Проверяем кэш
    cached = get_from_cache(lat, lon, 'weather')
    if cached:
        return cached
    
    url = (
        f"https://api.openweathermap.org/data/2.5/weather?"
        f"lat={lat}&lon={lon}&appid={OW_API_KEY}&units=metric&lang=ru"
    )
    response = request_with_retries(url)
    if response is None:
        return None
    
    if response.status_code == 200:
        try:
            data = response.json()
            # Проверяем, что ответ не пустой
            if not data or 'main' not in data:
                return None
            # Локализуем описание погоды, если API вернул английский
            if 'weather' in data and len(data['weather']) > 0:
                desc = data['weather'][0].get('description', '')
                if desc:
                    translated = translate_weather_description(desc)
                    data['weather'][0]['description'] = translated
            # Сохраняем в кэш
            save_to_cache(lat, lon, 'weather', data)
            return data
        except (json.JSONDecodeError, KeyError, ValueError):
            return None
    
    return None

def get_coordinates(city: str) -> Optional[tuple[float, float]]:
    """Возвращает (lat, lon) для города через OpenWeather Geocoding API.
    Возвращает None при ошибках или пустом ответе вместо исключений."""
    if not city or not city.strip():
        return None
    
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OW_API_KEY}"
    response = request_with_retries(url)
    if response is None:
        return None
    
    if response.status_code == 200:
        try:
            data = response.json()
            # Проверяем, что ответ не пустой
            if not data or len(data) == 0:
                return None
            if 'lat' not in data[0] or 'lon' not in data[0]:
                return None
            lat = data[0]["lat"]
            lon = data[0]["lon"]
            return lat, lon
        except (json.JSONDecodeError, KeyError, IndexError, ValueError):
            return None
    
    return None

def get_forecast_5d3h(lat: float, lon: float) -> Optional[dict]:
    """Возвращает прогноз погоды на 5 дней с шагом 3 часа.
    Возвращает None при ошибках вместо исключений."""
    # Проверяем кэш
    cached = get_from_cache(lat, lon, 'forecast')
    if cached:
        return cached
    
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OW_API_KEY}&units=metric&lang=ru"
    response = request_with_retries(url)
    if response is None:
        return None
    
    if response.status_code == 200:
        try:
            data = response.json()
            # Проверяем, что ответ не пустой
            if not data or 'list' not in data:
                return None
            # Локализуем описания погоды
            if 'list' in data:
                for item in data['list']:
                    if 'weather' in item and len(item['weather']) > 0:
                        desc = item['weather'][0].get('description', '')
                        if desc and desc.lower() in WEATHER_DESCRIPTIONS:
                            item['weather'][0]['description'] = translate_weather_description(desc)
            # Сохраняем в кэш
            save_to_cache(lat, lon, 'forecast', data)
            return data
        except (json.JSONDecodeError, KeyError, ValueError):
            return None
    
    return None

def get_air_pollution(lat: float, lon: float) -> Optional[dict]:
    """Возвращает загрязнение воздуха по координатам через /data/2.5/air_pollution.
    Возвращает None при ошибках вместо исключений."""
    # Проверяем кэш
    cached = get_from_cache(lat, lon, 'air_pollution')
    if cached:
        return cached
    
    url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OW_API_KEY}"
    response = request_with_retries(url)
    if response is None:
        return None
    
    if response.status_code == 200:
        try:
            data = response.json()
            # Проверяем, что ответ не пустой
            if not data or 'list' not in data or len(data['list']) == 0:
                return None
            components = data['list'][0].get('components')
            if not components:
                return None
            # Сохраняем в кэш
            save_to_cache(lat, lon, 'air_pollution', components)
            return components
        except (json.JSONDecodeError, KeyError, IndexError, ValueError):
            return None
    
    return None

# Константы для анализа качества воздуха
AIR_QUALITY_LEVELS = {
    1: {'name': 'Good', 'name_ru': 'Хорошо', 'ranges': {'so2': (0, 20), 'no2': (0, 40), 'pm10': (0, 20), 'pm2_5': (0, 10), 'o3': (0, 60), 'co': (0, 4400)}},
    2: {'name': 'Fair', 'name_ru': 'Удовлетворительно', 'ranges': {'so2': (20, 80), 'no2': (40, 70), 'pm10': (20, 50), 'pm2_5': (10, 25), 'o3': (60, 100), 'co': (4400, 9400)}},
    3: {'name': 'Moderate', 'name_ru': 'Умеренное', 'ranges': {'so2': (80, 250), 'no2': (70, 150), 'pm10': (50, 100), 'pm2_5': (25, 50), 'o3': (100, 140), 'co': (9400, 12400)}},
    4: {'name': 'Poor', 'name_ru': 'Плохое', 'ranges': {'so2': (250, 350), 'no2': (150, 200), 'pm10': (100, 200), 'pm2_5': (50, 75), 'o3': (140, 180), 'co': (12400, 15400)}},
    5: {'name': 'Very Poor', 'name_ru': 'Очень плохое', 'ranges': {'so2': (350, float('inf')), 'no2': (200, float('inf')), 'pm10': (200, float('inf')), 'pm2_5': (75, float('inf')), 'o3': (180, float('inf')), 'co': (15400, float('inf'))}}
}

POLLUTANT_NAMES = {'so2': 'SO₂', 'no2': 'NO₂', 'pm10': 'PM₁₀', 'pm2_5': 'PM₂.₅', 'o3': 'O₃', 'co': 'CO'}


def analyze_air_pollution(components: dict, extended: bool=False) -> dict:
    """Анализирует загрязнение воздуха и возвращает результат."""
    # Определение уровня для каждого загрязнителя
    pollutant_data = {}
    for key, value in components.items():
        if key in POLLUTANT_NAMES:
            for level in range(1, 6):
                lower, upper = AIR_QUALITY_LEVELS[level]['ranges'][key]
                if value >= lower and (upper == float('inf') or value < upper):
                    pollutant_data[key] = {'value': value, 'level': level}
                    break
    
    # Общий статус (максимальный уровень)
    overall_level = max((d['level'] for d in pollutant_data.values()), default=1)
    status = AIR_QUALITY_LEVELS[overall_level]
    
    result = {'overall_status': {'index': overall_level, 'name_ru': status['name_ru']}}
    
    if extended:
        below_norm, above_norm, all_components = [], [], []
        good_upper = {p: AIR_QUALITY_LEVELS[1]['ranges'][p][1] for p in pollutant_data.keys()}
        
        for pollutant, data in pollutant_data.items():
            value, level = data['value'], data['level']
            name = POLLUTANT_NAMES[pollutant]
            
            all_components.append({
                'pollutant': name,
                'value': round(value, 2),
                'unit': 'µg/m³',
                'level': level,
                'status': AIR_QUALITY_LEVELS[level]['name'],
                'status_ru': AIR_QUALITY_LEVELS[level]['name_ru']
            })
            
            if value < good_upper[pollutant]:
                below_norm.append({'pollutant': name, 'value': round(value, 2)})
            else:
                above_norm.append({'pollutant': name, 'value': round(value, 2), 'current_level': level})
        
        result['all_components'] = all_components
        result['below_norm'] = below_norm
        result['above_norm'] = above_norm
    
    return result

def format_air_pollution_report(result: dict) -> str:
    """Форматирует результат анализа загрязнения воздуха в читаемый вид."""
    status = result['overall_status']
    report = f"Общий статус воздуха: {status['name_ru']}\n"
    
    if 'all_components' in result:
        all_components = result['all_components']
        above_norm = result.get('above_norm', [])
        
        if not above_norm:
            report += "Все показатели в пределах нормы:\n"
        else:
            report += "Показатели выше нормы:\n"
            for item in above_norm:
                report += f"  {item['pollutant']}: {item['value']} мкг/м³\n"
            report += "Все показатели:\n"
        
        for component in all_components:
            report += f"{component['pollutant']}: {component['value']} мкг/м³ - {component['status_ru']}\n"
    
    return report


if __name__ == "__main__":
    res = get_coordinates('Москва')
    air_pollution = get_air_pollution(res[0], res[1])
    result = analyze_air_pollution(air_pollution, extended=True)
    print(format_air_pollution_report(result))