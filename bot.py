import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import json
import os
import time
from flask import Flask
import threading

TOKEN = os.getenv('TOKEN')
ADMIN_ID = 1107351961

bot = telebot.TeleBot(TOKEN)

# === ФАЙЛЫ ===
USER_DATA_FILE = 'users.json'
BANNED_FILE = 'banned.json'
MUTED_FILE = 'muted.json'
WARNS_FILE = 'warns.json'
LOG_FILE = 'log.txt'

# === ЛОГИРОВАНИЕ ===
def log_user_action(message, action="message"):
    try:
        user = message.from_user
        username = user.username or "без юзернейма"
        user_id = user.id
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        full_name = f"{first_name} {last_name}".strip()
        text = message.text or "не текст"
        log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {full_name} (@{username}, id={user_id}) -> {action}: {text}"
        print(log_entry)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    except Exception as e:
        print(f"❌ Ошибка логирования: {e}")

# === РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ===
def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_user(user_id, username, first_name):
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            'username': username or 'без юзернейма',
            'first_name': first_name or 'Без имени',
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
        return True
    return False

def is_registered(user_id):
    users = load_users()
    return str(user_id) in users

# === РАБОТА С БАНАМИ ===
def load_banned():
    if os.path.exists(BANNED_FILE):
        with open(BANNED_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_banned(banned):
    with open(BANNED_FILE, 'w', encoding='utf-8') as f:
        json.dump(banned, f, ensure_ascii=False, indent=4)

def is_banned(user_id):
    banned = load_banned()
    return str(user_id) in banned

# === РАБОТА С ЗАГЛУШЕННЫМИ ===
def load_muted():
    if os.path.exists(MUTED_FILE):
        with open(MUTED_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_muted(muted):
    with open(MUTED_FILE, 'w', encoding='utf-8') as f:
        json.dump(muted, f, ensure_ascii=False, indent=4)

def is_muted(user_id):
    muted = load_muted()
    return str(user_id) in muted

# === КЛАВИАТУРЫ ===
def main_keyboard():
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = KeyboardButton("📝 Био")
    btn2 = KeyboardButton("🌐 Сайт")
    btn3 = KeyboardButton("📋 Команды")
    btn4 = KeyboardButton("👤 Мой профиль")
    keyboard.add(btn1, btn2, btn3, btn4)
    return keyboard

def inline_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("📝 Био", callback_data="bio")
    btn2 = InlineKeyboardButton("🌐 Сайт", callback_data="website")
    btn3 = InlineKeyboardButton("📋 Команды", callback_data="help")
    btn4 = InlineKeyboardButton("👤 Мой профиль", callback_data="profile")
    keyboard.add(btn1, btn2, btn3, btn4)
    return keyboard

# === КОМАНДЫ ===
@bot.message_handler(commands=['start'])
def start(message):
    log_user_action(message, "/start")
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    is_new = save_user(user_id, username, first_name)
    if is_new:
        users = load_users()
        total_users = len(users)
        notify_text = (f"🆕 НОВЫЙ ПОЛЬЗОВАТЕЛЬ!\n\n👤 Имя: {first_name or 'Без имени'}\n🆔 ID: {user_id}\n📛 Юзернейм: @{username or 'нет'}\n📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n👥 Всего пользователей: {total_users}")
        try:
            bot.send_message(ADMIN_ID, notify_text)
        except:
            pass
        bot.send_message(message.chat.id, f"👋 Добро пожаловать, {first_name or 'гость'}!\n\nТы автоматически зарегистрирован.\nИспользуй кнопки ниже 👇", reply_markup=main_keyboard())
    else:
        bot.send_message(message.chat.id, f"👋 С возвращением, {first_name or 'гость'}!\n\nВыбери действие:", reply_markup=main_keyboard())

@bot.message_handler(commands=['bio'])
def bio(message):
    bot.send_message(message.chat.id, "Твой био текст...")

@bot.message_handler(commands=['website'])
def website(message):
    bot.send_message(message.chat.id, "https://evgteem.github.io/my-site/")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "📋 Команды:\n/start - Главное меню\n/bio - Био\n/website - Сайт")

def profile(message):
    user_id = message.from_user.id
    users = load_users()
    user_data = users.get(str(user_id))
    if user_data:
        now = datetime.now()
        bot.send_message(message.chat.id, f"👤 Твой профиль:\n\n🕐 Текущее время: {now.strftime('%H:%M:%S')}\n📅 Текущая дата: {now.strftime('%Y-%m-%d')}\n\n👤 Имя: {user_data['first_name']}\n📛 Юзернейм: @{user_data['username']}\n📅 Дата регистрации: {user_data['date']}")

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
    elif call.data == "profile":
        bot.answer_callback_query(call.id, "👤 Профиль")
        profile(call.message)
    else:
        bot.answer_callback_query(call.id, "Неизвестная команда")

# === ОБРАБОТЧИК REPLY-КНОПОК ===
@bot.message_handler(func=lambda message: True)
def handle_reply_buttons(message):
    if message.text.startswith('/'):
        return
    if not is_registered(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Сначала зарегистрируйся через /start")
        return
    if message.text == "📝 Био":
        bio(message)
    elif message.text == "🌐 Сайт":
        website(message)
    elif message.text == "📋 Команды":
        help_command(message)
    elif message.text == "👤 Мой профиль":
        profile(message)
    else:
        bot.send_message(message.chat.id, "❓ Используй кнопки внизу 👇\nИли напиши команду /help")

# === ЗАПУСК ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!", 200

def run_bot():
    print("✅ Проверочный бот запущен!")
    bot.infinity_polling()

threading.Thread(target=run_bot, daemon=True).start()
app.run(host='0.0.0.0', port=10000)
