"""Reply клавиатуры."""

from telebot import types


def create_main_menu():
    """Создает главное меню с кнопками."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn1 = types.KeyboardButton("🌤️ Прогноз по городу")
    btn2 = types.KeyboardButton("📅 Прогноз на 5 дней")
    btn3 = types.KeyboardButton("📍 Отправить местоположение", request_location=True)
    btn4 = types.KeyboardButton("🔔 Погодные уведомления")
    btn5 = types.KeyboardButton("⚖️ Сравнение городов")
    btn6 = types.KeyboardButton("📊 Расширенные данные")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    return markup

