"""Обработчики callback-запросов."""

from datetime import datetime
from utils.formatters import format_day_details, format_forecast_5days
from keyboards.inline import create_forecast_days_keyboard, create_back_to_forecast_keyboard
from services.user_storage import user_data, user_locations


def register_callback_handlers(bot):
    """Регистрирует обработчики callback-запросов."""
    
    @bot.callback_query_handler(func=lambda c: c.data.startswith('day_'))
    def day_details_callback(callback):
        """Обработчик нажатия на день в прогнозе."""
        user_id = callback.from_user.id
        
        try:
            # Извлекаем дату из callback_data
            day_str = callback.data.split('_', 1)[1]
            day_key = datetime.strptime(day_str, '%Y-%m-%d').date()
            
            if 'forecast_data' not in user_data[user_id]:
                bot.answer_callback_query(callback.id, "❌ Данные устарели. Запросите прогноз заново.")
                return
            
            day_details = user_data[user_id]['forecast_data']
            
            if day_key not in day_details:
                bot.answer_callback_query(callback.id, "❌ День не найден.")
                return
            
            day_data = day_details[day_key]
            text = format_day_details(day_data, day_key)
            
            # Кнопка "Назад"
            markup = create_back_to_forecast_keyboard()
            
            # Редактируем сообщение
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                reply_markup=markup
            )
            bot.answer_callback_query(callback.id)
        except Exception as e:
            bot.answer_callback_query(callback.id, f"❌ Ошибка: {str(e)}")
    
    @bot.callback_query_handler(func=lambda c: c.data == "back_to_forecast")
    def back_to_forecast_callback(callback):
        """Обработчик возврата к списку дней."""
        user_id = callback.from_user.id
        
        if 'forecast_data' not in user_data[user_id]:
            bot.answer_callback_query(callback.id, "❌ Данные устарели.")
            return
        
        day_details = user_data[user_id]['forecast_data']
        
        # Получаем название города из сохраненных данных
        city_name = "вашем городе"
        if user_id in user_locations:
            city_name = user_locations[user_id][2]
        
        # Формируем простой текст без деталей
        text = f"📅 Прогноз погоды на 5 дней в {city_name}\n\nВыберите день для подробного прогноза:"
        
        # Создаем inline-клавиатуру с кнопками
        markup = create_forecast_days_keyboard(day_details)
        
        bot.edit_message_text(
            text,
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=markup
        )
        bot.answer_callback_query(callback.id)

