import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask
import threading
import os

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

# === КЛАВИАТУРЫ ===
def main_keyboard():
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = KeyboardButton("📝 Био")
    btn2 = KeyboardButton("🌐 Сайт")
    btn3 = KeyboardButton("📋 Команды")
    keyboard.add(btn1, btn2, btn3)
    return keyboard

def inline_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("📝 Био", callback_data="bio")
    btn2 = InlineKeyboardButton("🌐 Сайт", callback_data="website")
    btn3 = InlineKeyboardButton("📋 Команды", callback_data="help")
    keyboard.add(btn1, btn2, btn3)
    return keyboard

# === КОМАНДЫ ===
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Выбери действие:", reply_markup=main_keyboard())
    bot.send_message(message.chat.id, "Или нажми на кнопку под этим сообщением:", reply_markup=inline_keyboard())

@bot.message_handler(commands=['bio'])
def bio(message):
    bot.send_message(message.chat.id, "Твой био текст...")

@bot.message_handler(commands=['website'])
def website(message):
    bot.send_message(message.chat.id, "https://evgteem.github.io/my-site/")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "📋 Команды:\n/start - Главное меню\n/bio - Био\n/website - Сайт")

# === ОБРАБОТЧИК ИНЛАЙН-КНОПОК ===
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "bio":
        bot.answer_callback_query(call.id, "📝 Био")
        bio(call.message)
    elif call.data == "website":
        bot.answer_callback_query(call.id, "🌐 Сайт")
        website(call.message)
    elif call.data == "help":
        bot.answer_callback_query(call.id, "📋 Команды")
        help_command(call.message)
    else:
        bot.answer_callback_query(call.id, "Неизвестная команда")

# === ОБРАБОТЧИК REPLY-КНОПОК ===
@bot.message_handler(func=lambda message: True)
def handle_reply_buttons(message):
    if message.text.startswith('/'):
        return
    if message.text == "📝 Био":
        bio(message)
    elif message.text == "🌐 Сайт":
        website(message)
    elif message.text == "📋 Команды":
        help_command(message)
    else:
        bot.send_message(message.chat.id, "❓ Используй кнопки внизу 👇")

# === ЗАПУСК ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!", 200

def run_bot():
    print("✅ Бот запущен!")
    bot.infinity_polling()

threading.Thread(target=run_bot, daemon=True).start()
app.run(host='0.0.0.0', port=10000)
