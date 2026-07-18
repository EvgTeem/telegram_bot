import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, LabeledPrice
from datetime import datetime, timedelta
import json
import os
import time
from flask import Flask
import threading
import random

TOKEN = os.getenv('TOKEN')
ADMIN_ID = 1107351961

bot = telebot.TeleBot(TOKEN)

# === ФАЙЛЫ ===
USER_DATA_FILE = 'users.json'
LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'log.txt')
BANNED_FILE = 'banned.json'
MUTED_FILE = 'muted.json'
WARNS_FILE = 'warns.json'
COINS_FILE = 'coins.json'
VIP_FILE = 'vip_users.json'
REFS_FILE = 'refs.json'
LOTTERY_FILE = 'lottery.json'

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# ============================================
# 1. БАЗОВЫЕ ФУНКЦИИ (ЛОГИ, ПОЛЬЗОВАТЕЛИ, БАН)
# ============================================
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

# ============================================
# 2. КОИНЫ (БАЛАНС)
# ============================================
def load_coins():
    if os.path.exists(COINS_FILE):
        with open(COINS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_coins(coins):
    with open(COINS_FILE, 'w', encoding='utf-8') as f:
        json.dump(coins, f, ensure_ascii=False, indent=4)

def get_coins(user_id):
    coins = load_coins()
    return coins.get(str(user_id), 0)

def add_coins(user_id, amount):
    coins = load_coins()
    coins[str(user_id)] = coins.get(str(user_id), 0) + amount
    save_coins(coins)

def remove_coins(user_id, amount):
    coins = load_coins()
    current = coins.get(str(user_id), 0)
    if current >= amount:
        coins[str(user_id)] = current - amount
        save_coins(coins)
        return True
    return False

# ============================================
# 3. VIP-СТАТУС
# ============================================
def load_vip():
    if os.path.exists(VIP_FILE):
        with open(VIP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_vip(vip_data):
    with open(VIP_FILE, 'w', encoding='utf-8') as f:
        json.dump(vip_data, f, ensure_ascii=False, indent=4)

def is_vip(user_id):
    vip_data = load_vip()
    if str(user_id) not in vip_data:
        return False
    expiry = vip_data[str(user_id)].get('expiry')
    if expiry and datetime.now().isoformat() > expiry:
        return False
    return True

def give_vip(user_id, days=30):
    vip_data = load_vip()
    expiry = (datetime.now() + timedelta(days=days)).isoformat()
    vip_data[str(user_id)] = {
        'expiry': expiry,
        'start': datetime.now().isoformat()
    }
    save_vip(vip_data)

def revoke_vip(user_id):
    vip_data = load_vip()
    if str(user_id) in vip_data:
        del vip_data[str(user_id)]
        save_vip(vip_data)
        return True
    return False

# ============================================
# 4. КЛАВИАТУРЫ
# ============================================
def main_keyboard():
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = KeyboardButton("📝 Био")
    btn2 = KeyboardButton("📋 Команды")
    btn3 = KeyboardButton("👤 Мой профиль")
    btn4 = KeyboardButton("🆘 Поддержка")
    btn5 = KeyboardButton("⭐ VIP")
    btn6 = KeyboardButton("🚀 Открыть приложение")
    keyboard.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return keyboard

def inline_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("📝 Био", callback_data="bio")
    btn2 = InlineKeyboardButton("🆘 Поддержка", callback_data="support")
    btn3 = InlineKeyboardButton("👤 Мой профиль", callback_data="profile")
    btn4 = InlineKeyboardButton("⭐ VIP", callback_data="vip")
    btn5 = InlineKeyboardButton("📋 Команды", callback_data="help")
    btn6 = InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url="https://evgteem.github.io/my-site/"))
    keyboard.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return keyboard

# ============================================
# 5. ПРОВЕРКИ
# ============================================
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

def check_vip(message):
    if not is_vip(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Эта команда доступна только VIP-пользователям!")
        return False
    return True

# ============================================
# 6. ОСНОВНЫЕ КОМАНДЫ
# ============================================
@bot.message_handler(commands=['start'])
def start(message):
    if check_banned(message): return
    log_user_action(message, "/start")
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    is_new = save_user(user_id, username, first_name)
    
    # Реферальная система
    if message.text.startswith('/start ref_'):
        ref_id = message.text.split('_')[1]
        if is_new and ref_id != str(user_id):
            refs = load_refs()
            refs[str(user_id)] = ref_id
            save_refs(refs)
            add_coins(int(ref_id), 5)
            try:
                bot.send_message(int(ref_id), f"🎉 Новый пользователь по твоей реферальной ссылке! +5 монет")
            except:
                pass
    
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

@bot.message_handler(commands=['help'])
def help_command(message):
    if check_banned(message): return
    if check_muted(message): return
    log_user_action(message, "/help")
    user_commands = "📋 **Команды для всех:**\n/start - Главное меню\n/bio - Моё био\n/support ТЕКСТ - Сообщение в поддержку\n/calc - Калькулятор"
    if is_vip(message.from_user.id):
        user_commands += "\n\n👑 **VIP-команды:**\n/vip_info - Информация о VIP\n/vip_joke - Шутка для VIP\n/vip_time - Время для VIP\n/vip_chat - Приватный чат с админом\n/slot - Казино\n/lottery - Лотерея\n/quiz - Викторина\n/ref - Реферальная программа"
    if message.from_user.id == ADMIN_ID:
        admin_commands = ("\n\n👑 **Админ-команды:**\n/stats - Статистика\n/users - Список пользователей\n/export - Экспорт CSV\n/top - Топ активных\n/clean_logs - Очистить логи\n/sendall - Рассылка\n/ban - Забанить\n/unban - Разбанить\n/banned - Список забаненных\n/mute - Заглушить\n/unmute - Разглушить\n/warn - Предупредить\n/warns - Предупреждения\n/reply ID ТЕКСТ - Ответить пользователю\n/getlog - Скачать логи\n/vip_manage ID days - Выдать VIP\n/vip_remove ID - Забрать VIP\n/coins_add ID amount - Добавить монеты\n/coins_remove ID amount - Забрать монеты")
        bot.send_message(message.chat.id, user_commands + admin_commands)
    else:
        bot.send_message(message.chat.id, user_commands)

# ============================================
# 7. ПОДДЕРЖКА (ИСПРАВЛЕННАЯ)
# ============================================
@bot.message_handler(commands=['support'])
def support_command(message):
    log_user_action(message, "/support")
    user_id = message.from_user.id
    text = message.text.replace('/support', '').strip()
    
    if not text:
        bot.send_message(message.chat.id, "✏️ Напиши сообщение в поддержку:\n/support ТВОЁ_СООБЩЕНИЕ")
        return
    
    user = message.from_user
    username = user.username or "без юзернейма"
    first_name = user.first_name or "Без имени"
    banned_status = "⛔ ЗАБАНЕН" if is_banned(user_id) else "✅ Не в бане"
    vip_status = "👑 VIP" if is_vip(user_id) else "👤 Пользователь"
    
    admin_text = (
        f"📩 **НОВОЕ СООБЩЕНИЕ В ПОДДЕРЖКУ!**\n\n"
        f"👤 От: {first_name}\n"
        f"🆔 ID: {user_id}\n"
        f"📛 Юзернейм: @{username}\n"
        f"📊 Статус: {banned_status}\n"
        f"👑 VIP: {vip_status}\n\n"
        f"📝 Текст:\n{text}\n\n"
        f"💡 Чтобы ответить, напиши:\n/reply {user_id} ТВОЙ_ОТВЕТ"
    )
    try:
        bot.send_message(ADMIN_ID, admin_text)
        bot.send_message(message.chat.id, "✅ Твоё сообщение отправлено администратору!\n\nМы ответим тебе в ближайшее время.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Ошибка отправки сообщения. Попробуй позже.")

# ============================================
# 8. VIP-КОМАНДЫ (ТОЛЬКО ДЛЯ VIP)
# ============================================
@bot.message_handler(commands=['vip_info'])
def vip_info(message):
    if not check_vip(message): return
    user_id = message.from_user.id
    vip_data = load_vip()
    expiry = vip_data.get(str(user_id), {}).get('expiry', 'Неизвестно')
    coins = get_coins(user_id)
    bot.send_message(
        message.chat.id,
        f"👑 **Твой VIP-статус**\n\n"
        f"📅 Действует до: {expiry}\n"
        f"🪙 Монет: {coins}"
    )

@bot.message_handler(commands=['vip_joke'])
def vip_joke(message):
    if not check_vip(message): return
    jokes = [
        "Почему программисты путают Хэллоуин и Рождество? Oct 31 = Dec 25.",
        "Сколько программистов нужно, чтобы заменить лампочку? Ни одного — это аппаратная проблема.",
        "Что сказал 0 числу 8? «Классный пояс!»",
        "Почему боты не ходят в душ? Они и так чистые.",
        "Что сказал один сервер другому? «Ты меня нагружаешь!»"
    ]
    bot.send_message(message.chat.id, random.choice(jokes))

@bot.message_handler(commands=['vip_time'])
def vip_time(message):
    if not check_vip(message): return
    now = datetime.now()
    bot.send_message(message.chat.id, f"🕐 **VIP-время:**\n{now.strftime('%Y-%m-%d %H:%M:%S')}")

@bot.message_handler(commands=['vip_chat'])
def vip_chat(message):
    if not check_vip(message): return
    text = message.text.replace('/vip_chat', '').strip()
    if not text:
        bot.send_message(message.chat.id, "✏️ Напиши сообщение админу:\n/vip_chat ТЕКСТ")
        return
    user = message.from_user
    admin_text = (
        f"📩 **VIP-ЧАТ**\n\n"
        f"👤 От: {user.first_name} (@{user.username or 'без юзернейма'})\n"
        f"🆔 ID: {user.id}\n\n"
        f"📝 Текст:\n{text}\n\n"
        f"💡 Чтобы ответить, напиши:\n/reply {user.id} ТВОЙ_ОТВЕТ"
    )
    bot.send_message(ADMIN_ID, admin_text)
    bot.send_message(message.chat.id, "✅ Сообщение отправлено админу!")

# ============================================
# 9. КАЗИНО (СЛОТ)
# ============================================
@bot.message_handler(commands=['slot'])
def slot(message):
    if not check_vip(message): return
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.chat.id, "🎰 Используй: /slot СТАВКА\nПример: /slot 10")
        return
    try:
        bet = int(parts[1])
    except:
        bot.send_message(message.chat.id, "❌ Ставка должна быть числом!")
        return
    if bet < 1:
        bot.send_message(message.chat.id, "❌ Минимальная ставка: 1 монета.")
        return
    if not remove_coins(message.from_user.id, bet):
        bot.send_message(message.chat.id, f"❌ У тебя нет {bet} монет. Твой баланс: {get_coins(message.from_user.id)}")
        return
    emojis = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣"]
    reel1, reel2, reel3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)
    result = f"{reel1} | {reel2} | {reel3}"
    if reel1 == reel2 == reel3:
        win = bet * (10 if reel1 == "💎" else 5 if reel1 == "7️⃣" else 3)
        add_coins(message.from_user.id, win)
        bot.send_message(message.chat.id, f"🎰 **ДЖЕКПОТ!**\n{result}\n\nТы выиграл {win} монет! 🎉")
    elif reel1 == reel2 or reel1 == reel3 or reel2 == reel3:
        win = bet * 1
        add_coins(message.from_user.id, win)
        bot.send_message(message.chat.id, f"🎰 Почти!\n{result}\n\nТы выиграл {win} монет.")
    else:
        bot.send_message(message.chat.id, f"🎰 Проигрыш!\n{result}\n\nТы проиграл {bet} монет.")

# ============================================
# 10. ЛОТЕРЕЯ
# ============================================
def load_lottery():
    if os.path.exists(LOTTERY_FILE):
        with open(LOTTERY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'tickets': {}, 'total': 0}

def save_lottery(data):
    with open(LOTTERY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@bot.message_handler(commands=['lottery'])
def lottery(message):
    if not check_vip(message): return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "🎫 /lottery buy - купить билет (10 монет)\n/lottery draw - провести розыгрыш (только админ)")
        return
    action = parts[1].lower()
    if action == 'buy':
        if not remove_coins(message.from_user.id, 10):
            bot.send_message(message.chat.id, "❌ У тебя нет 10 монет для покупки билета.")
            return
        data = load_lottery()
        user_id = str(message.from_user.id)
        data['tickets'][user_id] = data['tickets'].get(user_id, 0) + 1
        data['total'] += 1
        save_lottery(data)
        bot.send_message(message.chat.id, f"✅ Билет куплен! Всего билетов: {data['total']}")
    elif action == 'draw':
        if message.from_user.id != ADMIN_ID:
            bot.send_message(message.chat.id, "❌ Только админ может проводить розыгрыш!")
            return
        data = load_lottery()
        if data['total'] == 0:
            bot.send_message(message.chat.id, "❌ Нет билетов для розыгрыша.")
            return
        winner_id = random.choice(list(data['tickets'].keys()))
        prize = data['total'] * 5
        add_coins(int(winner_id), prize)
        bot.send_message(message.chat.id, f"🎉 **Победитель лотереи!**\n👤 ID: {winner_id}\n💰 Приз: {prize} монет")
        save_lottery({'tickets': {}, 'total': 0})
        try:
            bot.send_message(int(winner_id), f"🎉 Ты выиграл в лотерее {prize} монет!")
        except:
            pass

# ============================================
# 11. ВИКТОРИНА (КВИЗ)
# ============================================
QUIZ = [
    {"question": "Сколько планет в Солнечной системе?", "answers": ["8", "9", "7", "10"], "correct": 0},
    {"question": "Какой язык используется для ботов?", "answers": ["Python", "Java", "C++", "JavaScript"], "correct": 0},
    {"question": "Сколько дней в году?", "answers": ["365", "366", "364", "360"], "correct": 0},
]

@bot.message_handler(commands=['quiz'])
def vip_quiz(message):
    if not check_vip(message): return
    question = random.choice(QUIZ)
    keyboard = InlineKeyboardMarkup(row_width=2)
    for i, answer in enumerate(question['answers']):
        keyboard.add(InlineKeyboardButton(answer, callback_data=f"quiz_{i}"))
    bot.send_message(message.chat.id, f"🧠 **Вопрос для VIP:**\n{question['question']}", reply_markup=keyboard)

# ============================================
# 12. РЕФЕРАЛЬНАЯ ПРОГРАММА
# ============================================
REFS_FILE = 'refs.json'

def load_refs():
    if os.path.exists(REFS_FILE):
        with open(REFS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_refs(refs):
    with open(REFS_FILE, 'w', encoding='utf-8') as f:
        json.dump(refs, f, ensure_ascii=False, indent=4)

@bot.message_handler(commands=['ref'])
def ref_command(message):
    if not check_vip(message): return
    refs = load_refs()
    ref_link = f"https://t.me/{bot.get_me().username}?start=ref_{message.from_user.id}"
    count = len([r for r in refs.values() if r == str(message.from_user.id)])
    bot.send_message(message.chat.id, f"🔗 **Твоя реферальная ссылка:**\n{ref_link}\n\n👥 Приглашено: {count}\n🎁 За каждого нового пользователя ты получишь 5 монет!")

# ============================================
# 13. ПОКУПКА VIP ЗА 150 STARS
# ============================================
@bot.message_handler(commands=['buy_vip'])
def buy_vip(message):
    if check_banned(message): return
    if check_muted(message): return
    log_user_action(message, "/buy_vip")
    bot.send_invoice(
        chat_id=message.chat.id,
        title="⭐ VIP-доступ на 30 дней",
        description="Полный доступ ко всем VIP-командам, казино, лотерее и приватному чату с админом.",
        invoice_payload=f"vip_{message.from_user.id}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="VIP-доступ", amount=150)],
        photo_url="https://cdn-icons-png.flaticon.com/512/891/891386.png",
        photo_width=256,
        photo_height=256
    )

@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout_query(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message):
    payment_info = message.successful_payment
    user_id = message.from_user.id
    if payment_info.invoice_payload.startswith("vip_"):
        give_vip(user_id, 30)
        bot.send_message(message.chat.id, "✅ Оплата прошла успешно! VIP-доступ активирован на 30 дней.")
        try:
            bot.send_message(ADMIN_ID, f"💰 Пользователь {user_id} купил VIP за 150 Stars!")
        except:
            pass

# ============================================
# 14. АДМИН-УПРАВЛЕНИЕ VIP И КОИНАМИ
# ============================================
@bot.message_handler(commands=['vip_manage'])
def vip_manage(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Только для админа!")
        return
    parts = message.text.split()
    if len(parts) < 3:
        bot.send_message(message.chat.id, "❌ Используй: /vip_manage ID дни\nПример: /vip_manage 123456789 30")
        return
    try:
        target_id = int(parts[1])
        days = int(parts[2])
        give_vip(target_id, days)
        bot.send_message(message.chat.id, f"✅ Пользователь {target_id} получил VIP на {days} дней!")
        try:
            bot.send_message(target_id, f"👑 Ты получил VIP-доступ на {days} дней!")
        except:
            pass
    except:
        bot.send_message(message.chat.id, "❌ Неверный ID или количество дней.")

@bot.message_handler(commands=['vip_remove'])
def vip_remove(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Только для админа!")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ Используй: /vip_remove ID\nПример: /vip_remove 123456789")
        return
    try:
        target_id = int(parts[1])
        if revoke_vip(target_id):
            bot.send_message(message.chat.id, f"✅ VIP забран у пользователя {target_id}!")
            try:
                bot.send_message(target_id, f"❌ Администратор забрал у тебя VIP-доступ.")
            except:
                pass
        else:
            bot.send_message(message.chat.id, f"❌ У пользователя {target_id} нет VIP.")
    except:
        bot.send_message(message.chat.id, "❌ Неверный ID.")

@bot.message_handler(commands=['coins_add'])
def coins_add(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Только для админа!")
        return
    parts = message.text.split()
    if len(parts) < 3:
        bot.send_message(message.chat.id, "❌ Используй: /coins_add ID количество\nПример: /coins_add 123456789 100")
        return
    try:
        target_id = int(parts[1])
        amount = int(parts[2])
        add_coins(target_id, amount)
        bot.send_message(message.chat.id, f"✅ Пользователю {target_id} добавлено {amount} монет!")
        try:
            bot.send_message(target_id, f"🪙 Тебе начислено {amount} монет!")
        except:
            pass
    except:
        bot.send_message(message.chat.id, "❌ Неверный ID или количество.")

@bot.message_handler(commands=['coins_remove'])
def coins_remove(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Только для админа!")
        return
    parts = message.text.split()
    if len(parts) < 3:
        bot.send_message(message.chat.id, "❌ Используй: /coins_remove ID количество\nПример: /coins_remove 123456789 50")
        return
    try:
        target_id = int(parts[1])
        amount = int(parts[2])
        if remove_coins(target_id, amount):
            bot.send_message(message.chat.id, f"✅ У пользователя {target_id} снято {amount} монет!")
            try:
                bot.send_message(target_id, f"🪙 У тебя снято {amount} монет!")
            except:
                pass
        else:
            bot.send_message(message.chat.id, f"❌ У пользователя {target_id} недостаточно монет.")
    except:
        bot.send_message(message.chat.id, "❌ Неверный ID или количество.")

# ============================================
# 15. ОБРАБОТЧИК КНОПОК
# ============================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "bio":
        bot.answer_callback_query(call.id, "📝 Био")
        bio(call.message)
    elif call.data == "support":
        bot.answer_callback_query(call.id, "🆘 Поддержка")
        support_command(call.message)
    elif call.data == "profile":
        bot.answer_callback_query(call.id, "👤 Профиль")
        profile(call.message)
    elif call.data == "vip":
        bot.answer_callback_query(call.id, "⭐ VIP")
        buy_vip(call.message)
    elif call.data == "help":
        bot.answer_callback_query(call.id, "📋 Команды")
        help_command(call.message)
    elif call.data == "webapp":
        bot.answer_callback_query(call.id, "🚀 Открываю приложение...")
    elif call.data.startswith("quiz_"):
        bot.answer_callback_query(call.id, "✅ Ответ принят")
        bot.send_message(call.message.chat.id, "🧠 Ответ записан! Спасибо за участие.")
    else:
        bot.answer_callback_query(call.id, "Неизвестная команда")

# ============================================
# 16. ОБРАБОТЧИК REPLY-КНОПОК
# ============================================
@bot.message_handler(func=lambda message: True)
def handle_reply_buttons(message):
    if message.text.startswith('/'):
        return
    if not is_registered(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Сначала зарегистрируйся через /start")
        return
    if is_banned(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ Ты забанен! Обратись к @whyyhe.")
        return
    if is_muted(message.from_user.id):
        bot.send_message(message.chat.id, "🔇 Ты заглушен!")
        return
    if message.text == "📝 Био":
        bio(message)
    elif message.text == "📋 Команды":
        help_command(message)
    elif message.text == "👤 Мой профиль":
        profile(message)
    elif message.text == "🆘 Поддержка":
        support_command(message)
    elif message.text == "⭐ VIP":
        buy_vip(message)
    elif message.text == "🚀 Открыть приложение":
        from telebot.types import WebAppInfo
        keyboard = InlineKeyboardMarkup()
        btn = InlineKeyboardButton("🚀 Открыть приложение", web_app=WebAppInfo(url="https://evgteem.github.io/my-site/"))
        keyboard.add(btn)
        bot.send_message(message.chat.id, "Нажми на кнопку, чтобы открыть приложение:", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "❓ Используй кнопки внизу 👇")

# ============================================
# 17. ПРОФИЛЬ
# ============================================
def profile(message):
    user_id = message.from_user.id
    if check_banned(message): return
    if check_muted(message): return
    users = load_users()
    user_data = users.get(str(user_id))
    if user_data:
        now = datetime.now()
        vip_status = "👑 VIP" if is_vip(user_id) else "👤 Пользователь"
        coins = get_coins(user_id)
        bot.send_message(
            message.chat.id,
            f"👤 **Твой профиль:**\n\n"
            f"🕐 Текущее время: {now.strftime('%H:%M:%S')}\n"
            f"📅 Текущая дата: {now.strftime('%Y-%m-%d')}\n\n"
            f"👤 Имя: {user_data['first_name']}\n"
            f"📛 Юзернейм: @{user_data['username']}\n"
            f"📅 Дата регистрации: {user_data['date']}\n"
            f"⭐ Статус: {vip_status}\n"
            f"🪙 Монет: {coins}"
        )
    else:
        bot.send_message(message.chat.id, "❌ Ты не зарегистрирован! Напиши /start")

# ============================================
# 18. АДМИН-КОМАНДЫ (СТАТИСТИКА, ПОЛЬЗОВАТЕЛИ И Т.Д.)
# ============================================
# Здесь вставь свои существующие админ-команды (stats, users, export, top, clean_logs, sendall, ban, unban, banned, mute, unmute, warn, warns, reply, getlog)
# Они остаются без изменений, просто добавь их сюда.

# ============================================
# 19. ЗАПУСК БОТА
# ============================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!", 200

def run_bot():
    print("✅ Бот с VIP, монетами и поддержкой запущен!")
    bot.infinity_polling()

threading.Thread(target=run_bot, daemon=True).start()
app.run(host='0.0.0.0', port=10000)
