import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
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
    btn5 = KeyboardButton("📸 Instagram")
    btn6 = KeyboardButton("🆘 Поддержка")
    btn7 = KeyboardButton("⚡️ Купить доступ")
    keyboard.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    return keyboard

def inline_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("📝 Био", callback_data="bio")
    btn2 = InlineKeyboardButton("🌐 Сайт", callback_data="website")
    btn3 = InlineKeyboardButton("📸 Instagram", callback_data="instagram")
    btn4 = InlineKeyboardButton("🆘 Поддержка", callback_data="support")
    btn5 = InlineKeyboardButton("👤 Мой профиль", callback_data="profile")
    btn6 = InlineKeyboardButton("⚡️ Купить доступ", callback_data="buy")
    btn7 = InlineKeyboardButton("📋 Команды", callback_data="help")
    btn8 = InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url="https://evgteem.github.io/my-site/"))
    keyboard.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8)
    return keyboard

# === ПРОВЕРКА НА БАН И МУТ ===
def check_banned(message):
    if is_banned(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ Ты забанен!\n\nТы можешь писать только в поддержку: /support\nОбратись к @whyyhe для разблокировки.")
        return True
    return False

def check_muted(message):
    if is_muted(message.from_user.id):
        bot.send_message(message.chat.id, "🔇 Ты заглушен! Не можешь писать.")
        return True
    return False

# === КОМАНДЫ ===
@bot.message_handler(commands=['start'])
def start(message):
    if check_banned(message): return
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
    if check_banned(message): return
    if check_muted(message): return
    log_user_action(message, "/bio")
    bot.send_message(
        message.chat.id,
        "Why him? I don't know — he's obviously worse.\n\n"
        "One life. One shot. One name you won't forget.\n\n"
        "@whyyhe ain't just a person anymore. It's an organization. It's a movement. It's a whole damn ecosystem.\n\n"
        "If you know — you know where to find me.\n\n"
        "@whyyhe — the brand.\n"
        "@w3hand — the movement."
    )

@bot.message_handler(commands=['website'])
def website(message):
    if check_banned(message): return
    if check_muted(message): return
    log_user_action(message, "/website")
    bot.send_message(message.chat.id, "🌐 Мой сайт: https://evgteem.github.io/my-site/")

@bot.message_handler(commands=['instagram'])
def instagram(message):
    if check_banned(message): return
    if check_muted(message): return
    log_user_action(message, "/instagram")
    bot.send_message(message.chat.id, "📸 My Instagram: https://www.instagram.com/oh.whyyhe")

@bot.message_handler(commands=['help'])
def help_command(message):
    if check_banned(message): return
    if check_muted(message): return
    log_user_action(message, "/help")
    user_commands = ("📋 **Команды для всех:**\n/start - Главное меню\n/bio - Моё био\n/website - Мой сайт\n/instagram - Мой Instagram\n/support ТЕКСТ - Сообщение в поддержку\n/calc - Калькулятор\n/buy - Купить доступ")
    if message.from_user.id == ADMIN_ID:
        admin_commands = ("\n\n👑 **Админ-команды:**\n/stats - Статистика бота\n/users - Список всех пользователей\n/export - Скачать базу пользователей (CSV)\n/top - Топ активных пользователей\n/clean_logs - Очистить логи\n/sendall - Рассылка\n/ban - Забанить\n/unban - Разбанить\n/banned - Список забаненных\n/mute - Заглушить\n/unmute - Разглушить\n/warn - Предупредить\n/warns - Предупреждения\n/reply ID ТЕКСТ - Ответить пользователю\n/getlog - Скачать полный лог сообщений")
        bot.send_message(message.chat.id, user_commands + admin_commands)
    else:
        bot.send_message(message.chat.id, user_commands)

def profile(message):
    user_id = message.from_user.id
    if check_banned(message): return
    if check_muted(message): return
    users = load_users()
    user_data = users.get(str(user_id))
    if user_data:
        now = datetime.now()
        bot.send_message(message.chat.id, f"👤 Твой профиль:\n\n🕐 Текущее время: {now.strftime('%H:%M:%S')}\n📅 Текущая дата: {now.strftime('%Y-%m-%d')}\n\n👤 Имя: {user_data['first_name']}\n📛 Юзернейм: @{user_data['username']}\n📅 Дата регистрации: {user_data['date']}")
    else:
        bot.send_message(message.chat.id, "❌ Ты не зарегистрирован! Напиши /start")

@bot.message_handler(commands=['calc'])
def calc(message):
    if check_banned(message): return
    if check_muted(message): return
    log_user_action(message, "/calc")
    text = message.text.replace('/calc', '').strip()
    if not text:
        bot.send_message(message.chat.id, "📱 /calc 2+2")
        return
    try:
        result = eval(text)
        bot.send_message(message.chat.id, f"🧮 {text} = {result}")
    except:
        bot.send_message(message.chat.id, "❌ Ошибка!")

@bot.message_handler(commands=['buy'])
def buy_access(message):
    if check_banned(message): return
    if check_muted(message): return
    log_user_action(message, "/buy")
    bot.send_message(message.chat.id, "⚡️ Платежи пока в разработке!\n\nСкоро здесь будет возможность купить доступ к премиум-командам.\nСледи за обновлениями!")

@bot.message_handler(commands=['support'])
def support_command(message):
    log_user_action(message, "/support")
    user_id = message.from_user.id
    text = message.text.replace('/support', '').strip().lower()
    if text:
        bot.reply_to(message, f"🤖 **Автоответ:**\n\n{text}\n\nЕсли это не решило проблему, напиши подробнее — я передам админу.")
        return
    user = message.from_user
    username = user.username or "без юзернейма"
    first_name = user.first_name or "Без имени"
    banned_status = "⛔ ЗАБАНЕН" if is_banned(user_id) else "✅ Не в бане"
    admin_text = (f"📩 НОВОЕ СООБЩЕНИЕ В ПОДДЕРЖКУ!\n\n👤 От: {first_name}\n🆔 ID: {user_id}\n📛 Юзернейм: @{username}\n📊 Статус: {banned_status}\n\n📝 Текст:\n{text}\n\n💡 Чтобы ответить, напиши:\n/reply {user_id} ТВОЙ_ОТВЕТ")
    try:
        bot.send_message(ADMIN_ID, admin_text)
        bot.send_message(message.chat.id, "✅ Твоё сообщение отправлено администратору!\n\nМы ответим тебе в ближайшее время.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Ошибка отправки сообщения. Попробуй позже.")

@bot.message_handler(commands=['reply'])
def reply_command(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.send_message(message.chat.id, "❌ Используй: /reply ID ТЕКСТ\n\nПример: /reply 123456789 Привет, я тебя разбанил!")
        return
    try:
        target_id = int(parts[1])
        reply_text = parts[2]
    except:
        bot.send_message(message.chat.id, "❌ Неверный ID!")
        return
    if not is_registered(target_id):
        bot.send_message(message.chat.id, f"❌ Пользователь с ID {target_id} не найден.")
        return
    try:
        bot.send_message(target_id, f"📩 ОТВЕТ ОТ АДМИНИСТРАТОРА:\n\n{reply_text}")
        bot.send_message(message.chat.id, f"✅ Ответ отправлен пользователю {target_id}!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Не удалось отправить ответ: {e}")

# === ОСНОВНОЙ ОБРАБОТЧИК (ДЛЯ REPLY-КНОПОК И ЛЮБОГО ДРУГОГО ТЕКСТА) ===
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Логируем всё, что не команда
    if not message.text.startswith('/'):
        log_user_action(message, "💬 Сообщение")

    # Пропускаем команды — они уже обработаны выше
    if message.text.startswith('/'):
        return

    # Проверяем бан и мут
    if is_banned(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ Ты забанен!\n\nТы можешь писать только в поддержку: /support\nОбратись к @whyyhe для разблокировки.")
        return

    if check_muted(message):
        return

    user_id = message.from_user.id

    # Проверяем регистрацию
    if not is_registered(user_id):
        bot.send_message(message.chat.id, "❌ Сначала зарегистрируйся через /start")
        return

    # === ОБРАБОТКА КНОПОК ===
    if message.text == "📝 Био":
        bio(message)
    elif message.text == "🌐 Сайт":
        website(message)
    elif message.text == "📋 Команды":
        help_command(message)
    elif message.text == "👤 Мой профиль":
        profile(message)
    elif message.text == "📸 Instagram":
        instagram(message)
    elif message.text == "🆘 Поддержка":
        bot.send_message(message.chat.id, "✏️ Напиши /support ТВОЁ_СООБЩЕНИЕ\n\nПример: /support Меня забанили, помогите разобраться!")
    elif message.text == "⚡️ Купить доступ":
        buy_access(message)
    else:
        bot.send_message(message.chat.id, "❓ Используй кнопки внизу 👇\n\nИли напиши команду /help")

# === ЗАПУСК БОТА ===
if __name__ == "__main__":
    print("✅ Бот запущен с инлайн-кнопками и Reply-кнопками!")
    bot.infinity_polling()
