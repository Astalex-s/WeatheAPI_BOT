"""Обработчики для сравнения городов."""

from services.weather_api import get_current_weather, get_coordinates
from utils.formatters import format_cities_comparison
from keyboards.reply import create_main_menu
from services.user_storage import user_data


def register_comparison_handlers(bot):
    """Регистрирует обработчики сравнения городов."""
    
    @bot.message_handler(func=lambda m: m.text == "⚖️ Сравнение городов")
    def compare_cities_handler(message):
        """Обработчик сравнения городов."""
        user_id = message.from_user.id
        user_data[user_id]['state'] = 'waiting_city1'
        bot.reply_to(message, "Введите название первого города:", reply_markup=create_main_menu())
    
    @bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get('state') == 'waiting_city1')
    def process_city1(message):
        """Обрабатывает первый город для сравнения."""
        user_id = message.from_user.id
        city1 = message.text.strip()
        
        if not city1:
            bot.reply_to(message, "❌ Пожалуйста, введите название города.", reply_markup=create_main_menu())
            return
        
        coords1 = get_coordinates(city1)
        if coords1 is None:
            bot.reply_to(message, "❌ Город не найден. Попробуйте еще раз.", reply_markup=create_main_menu())
            return
        
        lat1, lon1 = coords1
        weather1 = get_current_weather(lat1, lon1)
        if weather1 is None:
            bot.reply_to(message, "❌ Не удалось получить данные о погоде для первого города. Попробуйте позже.", reply_markup=create_main_menu())
            return
        
        user_data[user_id]['compare_city1'] = (city1, weather1)
        user_data[user_id]['state'] = 'waiting_city2'
        bot.reply_to(message, f"✅ Первый город: {city1}\nВведите название второго города:", reply_markup=create_main_menu())
    
    @bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get('state') == 'waiting_city2')
    def process_city2(message):
        """Обрабатывает второй город для сравнения."""
        user_id = message.from_user.id
        city2 = message.text.strip()
        
        if not city2:
            bot.reply_to(message, "❌ Пожалуйста, введите название города.", reply_markup=create_main_menu())
            return
        
        coords2 = get_coordinates(city2)
        if coords2 is None:
            bot.reply_to(message, "❌ Город не найден. Попробуйте еще раз.", reply_markup=create_main_menu())
            return
        
        lat2, lon2 = coords2
        weather2 = get_current_weather(lat2, lon2)
        if weather2 is None:
            bot.reply_to(message, "❌ Не удалось получить данные о погоде для второго города. Попробуйте позже.", reply_markup=create_main_menu())
            return
        
        if 'compare_city1' not in user_data[user_id]:
            bot.reply_to(message, "❌ Ошибка: данные о первом городе не найдены. Начните заново.", reply_markup=create_main_menu())
            user_data[user_id]['state'] = 'main'
            return
        
        city1, weather1 = user_data[user_id]['compare_city1']
        
        comparison_text = format_cities_comparison(city1, weather1, city2, weather2)
        bot.reply_to(message, comparison_text, reply_markup=create_main_menu())
        
        # Очищаем состояние
        user_data[user_id]['state'] = 'main'
        if 'compare_city1' in user_data[user_id]:
            del user_data[user_id]['compare_city1']

