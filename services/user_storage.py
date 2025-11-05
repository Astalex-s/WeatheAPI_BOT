"""Сервис для работы с данными пользователей."""

from collections import defaultdict
from services.storage import load_user, save_user, load_all_users


# Глобальные хранилища данных пользователей
user_data = defaultdict(dict)
user_locations = {}  # {user_id: (lat, lon, city_name)}
notifications_enabled = {}  # {user_id: True/False}
notification_intervals = {}  # {user_id: interval_hours}
last_weather = {}  # {user_id: weather_data} для отслеживания изменений
last_notification_check = {}  # {user_id: datetime}


def load_user_from_storage(user_id: int):
    """Загружает данные пользователя из хранилища и обновляет память."""
    stored_data = load_user(user_id)
    
    if stored_data:
        # Восстанавливаем местоположение
        if 'lat' in stored_data and 'lon' in stored_data and 'city' in stored_data:
            user_locations[user_id] = (
                stored_data['lat'],
                stored_data['lon'],
                stored_data['city']
            )
        
        # Восстанавливаем настройки уведомлений
        if 'notifications' in stored_data:
            notifications_enabled[user_id] = stored_data['notifications'].get('enabled', False)
            notification_intervals[user_id] = stored_data['notifications'].get('interval_h', 2)


def save_user_to_storage(user_id: int):
    """Сохраняет данные пользователя в хранилище."""
    data = {}
    
    # Сохраняем местоположение
    if user_id in user_locations:
        lat, lon, city_name = user_locations[user_id]
        data['lat'] = lat
        data['lon'] = lon
        data['city'] = city_name
    
    # Сохраняем настройки уведомлений
    notifications = {
        'enabled': notifications_enabled.get(user_id, False),
        'interval_h': notification_intervals.get(user_id, 2)
    }
    data['notifications'] = notifications
    
    save_user(user_id, data)


def load_all_users_from_storage():
    """Загружает данные всех пользователей из хранилища при старте."""
    all_users = load_all_users()
    
    for user_id_str, user_data_dict in all_users.items():
        try:
            user_id = int(user_id_str)
            load_user_from_storage(user_id)
        except (ValueError, KeyError):
            continue

