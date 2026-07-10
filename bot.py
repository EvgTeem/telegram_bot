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
        with open('log.txt', 'a', encoding='utf-8') as f:
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

# === РАБОТА С ПРЕДУПРЕЖДЕНИЯМИ ===
def load_warns():
    if os.path.exists(WARNS_FILE):
        with open(WARNS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_warns(warns):
    with open(WARNS_FILE, 'w', encoding='utf-8') as f:
        json.dump(warns, f, ensure_ascii=False, indent=4)

def get_warns(user_id):
    warns = load_warns()
    return warns.get(str(user_id), 0)

def add_warn(user_id):
    warns = load_warns()
    warns[str(user_id)] = warns.get(str(user_id), 0) + 1
    save_warns(warns)
    return warns[str(user_id)]

# === ФУНКЦИЯ РАССЫЛКИ ===
def send_broadcast(message_text):
    users = load_users()
    success = 0
    fail = 0
    for user_id, user_data in users.items():
        if is_banned(int(user_id)):
            continue
        try:
            bot.send_message(int(user_id), f"📢 РАССЫЛКА:\n\n{message_text}")
            success += 1
            time.sleep(0.5)
        except Exception as e:
            fail += 1
            print(f"❌ Не удалось отправить {user_id}: {e}")
    return success, fail

# === КЛАВИАТУРА ===
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

# === ИНЛАЙН-КЛАВИАТУРА (С КНОПКОЙ МИНИ-ПРИЛОЖЕНИЯ) ===
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

# === БАЗА ЗНАНИЙ (FAQ) ===
FAQ = {
    "бан": "Если тебя забанили, напиши в поддержку, я разберусь. Обычно баны даются за нарушение правил.",
    "доступ": "Чтобы получить доступ, нажми на кнопку 'Купить доступ' или напиши админу.",
    "бот не работает": "Попробуй перезапустить бота командой /start. Если не помогает — напиши в поддержку.",
    "как зарегистрироваться": "Ты уже зарегистрирован! Просто напиши /start и пользуйся ботом.",
    "регистрация": "Ты уже зарегистрирован! Просто напиши /start и пользуйся ботом.",
    "команды": "Все команды можно посмотреть через /help.",
    "помощь": "Напиши /help, чтобы увидеть список всех команд.",
    "купить": "Чтобы купить доступ, нажми на кнопку 'Купить доступ' или напиши /buy.",
    "оплата": "Оплата пока в разработке. Следи за обновлениями!",
}

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
        bot.send_message(message.chat.id, f"👋 Добро пожаловать, {first_name or 'гость'}!\n\nТы автоматически зарегистрирован.\nИспользуй кнопки ниже 👇", reply_markup=inline_keyboard())
    else:
        bot.send_message(message.chat.id, f"👋 С возвращением, {first_name or 'гость'}!\n\nВыбери действие:", reply_markup=inline_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if is_banned(call.from_user.id) and call.data != "support":
        bot.answer_callback_query(call.id, "⛔ Ты забанен! Пиши только в поддержку.", show_alert=True)
        return
    if call.data == "bio":
        class FakeMessage:
            def __init__(self, chat_id, from_user):
                self.chat = type('obj', (object,), {'id': chat_id})
                self.from_user = from_user
                self.text = "/bio"
        fake_msg = FakeMessage(call.message.chat.id, call.from_user)
        bio(fake_msg)
    elif call.data == "website":
        class FakeMessage:
            def __init__(self, chat_id, from_user):
                self.chat = type('obj', (object,), {'id': chat_id})
                self.from_user = from_user
                self.text = "/website"
        fake_msg = FakeMessage(call.message.chat.id, call.from_user)
        website(fake_msg)
    elif call.data == "instagram":
        class FakeMessage:
            def __init__(self, chat_id, from_user):
                self.chat = type('obj', (object,), {'id': chat_id})
                self.from_user = from_user
                self.text = "/instagram"
        fake_msg = FakeMessage(call.message.chat.id, call.from_user)
        instagram(fake_msg)
    elif call.data == "support":
        class FakeMessage:
            def __init__(self, chat_id, from_user):
                self.chat = type('obj', (object,), {'id': chat_id})
                self.from_user = from_user
                self.text = "/support"
        fake_msg = FakeMessage(call.message.chat.id, call.from_user)
        support_command(fake_msg)
    elif call.data == "profile":
        class FakeMessage:
            def __init__(self, chat_id, from_user):
                self.chat = type('obj', (object,), {'id': chat_id})
                self.from_user = from_user
                self.text = "👤 Мой профиль"
        fake_msg = FakeMessage(call.message.chat.id, call.from_user)
        profile(fake_msg)
    elif call.data == "buy":
        class FakeMessage:
            def __init__(self, chat_id, from_user):
                self.chat = type('obj', (object,), {'id': chat_id})
                self.from_user = from_user
                self.text = "/buy"
        fake_msg = FakeMessage(call.message.chat.id, call.from_user)
        buy_access(fake_msg)
    elif call.data == "help":
        class FakeMessage:
            def __init__(self, chat_id, from_user):
                self.chat = type('obj', (object,), {'id': chat_id})
                self.from_user = from_user
                self.text = "/help"
        fake_msg = FakeMessage(call.message.chat.id, call.from_user)
        help_command(fake_msg)
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['bio'])
def bio(message):
    if check_banned(message): return
    if check_muted(message): return
    log_user_action(message, "/bio")
    bot.send_message(message.chat.id, "Why him? I don't know — he's obviously worse.\n\nOne life. One shot. One name you won't forget.\n\nI don't owe explanations to anyone who ain't on my level — financially or otherwise. If your pockets are light, don't expect me to break it down for you.\n\nIf you know — you know where to find me.\n\n@whyyhe — personal.\n@w3hand — the movement.")

@bot.message_handler(commands=['website'])
def website(message):
    if check_banned(message): return
    if check_muted(message): return
    log_user_action(message, "/website")
    bot.send_message(message.chat.id, "🌐 My website: https://guns.lol/whyyhe")

@bot.message_handler(commands=['instagram'])
def instagram(message):
    if check_banned(message): return
    if check_muted(message): return
    log_user_action(message, "/instagram")
    bot.send_message(message.chat.id, "📸 My Instagram: https://www.instagram.com/oh.whyyhe")

@bot.message_handler(commands=['support'])
def support_command(message):
    log_user_action(message, "/support")
    user_id = message.from_user.id
    text = message.text.replace('/support', '').strip().lower()
    if text:
        for key, answer in FAQ.items():
            if key in text:
                bot.reply_to(message, f"🤖 **Автоответ:**\n\n{answer}\n\nЕсли это не решило проблему, напиши подробнее — я передам админу.")
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

@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    users = load_users()
    total_users = len(users)
    commands_count = {}
    total_commands = 0
    today_commands = 0
    week_commands = 0
    today_date = datetime.now().strftime('%Y-%m-%d')
    try:
        if os.path.exists('log.txt'):
            with open('log.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if '->' in line:
                        total_commands += 1
                        if today_date in line:
                            today_commands += 1
                        try:
                            date_part = line.split('[')[1].split(']')[0].split(' ')[0]
                            log_date = datetime.strptime(date_part, '%Y-%m-%d')
                            if (datetime.now() - log_date).days <= 7:
                                week_commands += 1
                        except:
                            pass
                        parts = line.split('->')
                        if len(parts) > 1:
                            cmd = parts[1].strip().split(' ')[0].replace('[', '').replace(']', '').strip()
                            if cmd and not cmd.startswith('💬') and not cmd.startswith('📱'):
                                commands_count[cmd] = commands_count.get(cmd, 0) + 1
    except:
        pass
    top_commands = sorted(commands_count.items(), key=lambda x: x[1], reverse=True)[:5]
    today_users = 0
    week_users = 0
    for uid, data in users.items():
        try:
            reg_date = datetime.strptime(data['date'], '%Y-%m-%d %H:%M:%S')
            if (datetime.now() - reg_date).days == 0:
                today_users += 1
            if (datetime.now() - reg_date).days <= 7:
                week_users += 1
        except:
            pass
    banned = load_banned()
    muted = load_muted()
    stats_text = (f"📊 СТАТИСТИКА БОТА\n{'='*30}\n\n👥 Всего пользователей: {total_users}\n🆕 За сегодня: {today_users}\n📈 За неделю: {week_users}\n\n📱 Команд всего: {total_commands}\n📅 За сегодня: {today_commands}\n📆 За неделю: {week_commands}\n\n🔥 Топ команд:\n")
    if top_commands:
        for i, (cmd, count) in enumerate(top_commands, 1):
            stats_text += f"  {i}. {cmd}: {count}\n"
    else:
        stats_text += "  Нет данных\n"
    stats_text += f"\n⛔ Забаненных: {len(banned)}\n🔇 Заглушенных: {len(muted)}"
    bot.send_message(message.chat.id, stats_text)

@bot.message_handler(commands=['users'])
def list_users(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    users = load_users()
    if not users:
        bot.send_message(message.chat.id, "📋 Пользователей нет.")
        return
    text = "📋 Все пользователи:\n\n"
    for uid, data in users.items():
        text += f"ID: {uid}\nИмя: {data['first_name']}\nЮзернейм: @{data['username']}\nДата: {data['date']}\n\n"
    if len(text) > 4096:
        for i in range(0, len(text), 4000):
            bot.send_message(message.chat.id, text[i:i+4000])
    else:
        bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['export'])
def export_users(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    users = load_users()
    if not users:
        bot.send_message(message.chat.id, "📋 База пользователей пуста.")
        return
    csv_data = "ID,Имя,Юзернейм,Дата регистрации\n"
    for uid, data in users.items():
        csv_data += f"{uid},{data['first_name']},@{data['username']},{data['date']}\n"
    csv_file = 'users_export.csv'
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write(csv_data)
    try:
        with open(csv_file, 'rb') as f:
            bot.send_document(message.chat.id, f, caption="📊 Вот список всех пользователей в формате CSV")
        os.remove(csv_file)
        bot.send_message(message.chat.id, "✅ Файл успешно отправлен и удалён с сервера!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка отправки файла: {e}")

@bot.message_handler(commands=['top'])
def top_users(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    try:
        if not os.path.exists('log.txt'):
            bot.send_message(message.chat.id, "📋 Логов пока нет.")
            return
        user_activity = {}
        with open('log.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if '->' in line:
                    parts = line.split('id=')
                    if len(parts) > 1:
                        user_id = parts[1].split(')')[0].strip()
                        if user_id.isdigit():
                            user_activity[user_id] = user_activity.get(user_id, 0) + 1
        if not user_activity:
            bot.send_message(message.chat.id, "📋 Нет данных об активности.")
            return
        top_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:5]
        users = load_users()
        top_text = "🏆 **Топ активных пользователей:**\n\n"
        for i, (user_id, count) in enumerate(top_users, 1):
            user_data = users.get(user_id, {})
            name = user_data.get('first_name', 'Неизвестно')
            username = user_data.get('username', 'нет')
            top_text += f"{i}. {name} (@{username}) — {count} команд\n"
        bot.send_message(message.chat.id, top_text)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['clean_logs'])
def clean_logs(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    try:
        if os.path.exists('log.txt'):
            with open('log.txt', 'w', encoding='utf-8') as f:
                f.write("")
            bot.send_message(message.chat.id, "✅ Логи успешно очищены!")
        else:
            bot.send_message(message.chat.id, "📁 Файл с логами не найден.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    text = message.text.replace('/ban', '').strip()
    if not text and not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Укажи ID или ответь на сообщение!")
        return
    target_id = message.reply_to_message.from_user.id if message.reply_to_message else int(text)
    if target_id == ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Нельзя забанить админа!")
        return
    muted = load_muted()
    if str(target_id) in muted:
        del muted[str(target_id)]
        save_muted(muted)
    banned = load_banned()
    banned[str(target_id)] = {'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'banned_by': ADMIN_ID}
    save_banned(banned)
    bot.send_message(message.chat.id, f"✅ Пользователь {target_id} забанен!")
    try:
        bot.send_message(target_id, f"⛔ Ты забанен!\n\nТы можешь писать только в поддержку: /support\nОбратись к @whyyhe для разблокировки.")
    except:
        pass

@bot.message_handler(commands=['unban'])
def unban_user(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    text = message.text.replace('/unban', '').strip()
    if not text and not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Укажи ID или ответь на сообщение!")
        return
    target_id = message.reply_to_message.from_user.id if message.reply_to_message else int(text)
    banned = load_banned()
    if str(target_id) in banned:
        del banned[str(target_id)]
        save_banned(banned)
        bot.send_message(message.chat.id, f"✅ Пользователь {target_id} разбанен!")
        try:
            bot.send_message(target_id, f"✅ Ты разбанен!\n\nТеперь ты снова можешь пользоваться ботом.\nНапиши /start.")
        except:
            pass
    else:
        bot.send_message(message.chat.id, f"❌ Пользователь не в бане!")

@bot.message_handler(commands=['banned'])
def list_banned(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    banned = load_banned()
    if not banned:
        bot.send_message(message.chat.id, "📋 Список забаненных пуст.")
        return
    text = "📋 Забаненные:\n\n"
    for uid, data in banned.items():
        text += f"ID: {uid}\nДата: {data['date']}\n\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['mute'])
def mute_user(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    text = message.text.replace('/mute', '').strip()
    if not text and not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Укажи ID или ответь на сообщение!")
        return
    target_id = message.reply_to_message.from_user.id if message.reply_to_message else int(text)
    if target_id == ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Нельзя заглушить админа!")
        return
    muted = load_muted()
    muted[str(target_id)] = {'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'muted_by': ADMIN_ID}
    save_muted(muted)
    bot.send_message(message.chat.id, f"🔇 {target_id} заглушен!")
    try:
        bot.send_message(target_id, f"🔇 Ты заглушен!")
    except:
        pass

@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    text = message.text.replace('/unmute', '').strip()
    if not text and not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Укажи ID или ответь на сообщение!")
        return
    target_id = message.reply_to_message.from_user.id if message.reply_to_message else int(text)
    muted = load_muted()
    if str(target_id) in muted:
        del muted[str(target_id)]
        save_muted(muted)
        bot.send_message(message.chat.id, f"🔊 {target_id} разглушен!")
        try:
            bot.send_message(target_id, f"🔊 Ты разглушен!")
        except:
            pass
    else:
        bot.send_message(message.chat.id, f"❌ Не в муте!")

@bot.message_handler(commands=['warn'])
def warn_user(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Ответь на сообщение!")
        return
    target_id = message.reply_to_message.from_user.id
    if target_id == ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Нельзя предупредить админа!")
        return
    warns = add_warn(target_id)
    bot.send_message(message.chat.id, f"⚠️ Предупреждение! Всего: {warns}")
    try:
        bot.send_message(target_id, f"⚠️ Ты получил предупреждение! Всего: {warns}")
    except:
        pass

@bot.message_handler(commands=['warns'])
def check_warns(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    text = message.text.replace('/warns', '').strip()
    if not text and not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Укажи ID или ответь на сообщение!")
        return
    target_id = message.reply_to_message.from_user.id if message.reply_to_message else int(text)
    warns = get_warns(target_id)
    bot.send_message(message.chat.id, f"⚠️ Предупреждений: {warns}")

@bot.message_handler(commands=['sendall'])
def sendall_command(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    text = message.text.replace('/sendall', '').strip()
    if not text:
        bot.send_message(message.chat.id, "❌ Напиши текст!")
        return
    bot.send_message(message.chat.id, f"⏳ Рассылка...")
    success, fail = send_broadcast(text)
    bot.send_message(message.chat.id, f"✅ Отправлено: {success}\n❌ Ошибок: {fail}")

# === КОМАНДА /GETLOG ===
@bot.message_handler(commands=['getlog'])
def send_logs(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    if os.path.exists('log.txt'):
        try:
            with open('log.txt', 'rb') as f:
                bot.send_document(message.chat.id, f, caption="📋 Вот полный лог всех сообщений.")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {e}")
    else:
        bot.send_message(message.chat.id, "📁 Лог-файл пока пуст.")

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

# === ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ ===
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if not message.text.startswith('/'):
        log_user_action(message, "💬 Сообщение")
    if message.text.startswith('/'):
        return
    if is_banned(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ Ты забанен!\n\nТы можешь писать только в поддержку: /support\nОбратись к @whyyhe для разблокировки.")
        return
    if check_muted(message): return
    user_id = message.from_user.id
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
        if is_registered(user_id):
            bot.send_message(message.chat.id, "❓ Используй кнопки внизу 👇\n\nИли напиши команду:\n/bio - Био\n/website - Сайт\n/instagram - Instagram\n/support - Поддержка\n/calc - Калькулятор\n/buy - Купить доступ")
        else:
            bot.send_message(message.chat.id, "❌ Ты не зарегистрирован! Напиши /start")

# === ЗАПУСК БОТА + ВЕБ-СЕРВЕР ДЛЯ RENDER ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!", 200

def run_bot():
    print("✅ Бот запущен с мини-приложением!")
    print(f"📁 Логи: {os.path.abspath('log.txt')}")
    print(f"📁 Пользователи: {os.path.abspath(USER_DATA_FILE)}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    bot.infinity_polling()

threading.Thread(target=run_bot, daemon=True).start()
app.run(host='0.0.0.0', port=10000)
