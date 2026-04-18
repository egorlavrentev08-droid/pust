# core.py - Ядро бота
# Версия: 2.0.0
# Творец: Легенда Пустоши
# Старый торговец: принял и одобрил

import logging
import random
import json
import os
import shutil
from datetime import datetime, timedelta

# Telegram
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)

# Планировщик
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# База данных
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# ==================== НАСТРОЙКИ ====================
TOKEN = '8492718356:AAF4pqw8050Td9dzxz_HKFsCX2aYjuyiVzM'
ADMIN_CODE = '1252836169043217'
SUPER_ADMIN_IDS = [6595788533]

MAX_LEVEL = 100
MAX_CLAN_BONUS = 10
MAX_MEDKITS = 10

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# База данных
Base = declarative_base()
engine = create_engine('sqlite:///radcoin_bot.db', pool_size=10, max_overflow=20)
Session = scoped_session(sessionmaker(bind=engine))

# Планировщик
scheduler = AsyncIOScheduler()

# Директория для бэкапов
BACKUP_DIR = '/app/data/backups'
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# ==================== НАСТРОЙКИ КАЗИНО (ПО УМОЛЧАНИЮ) ====================
CASINO_PUBLIC_CHANCE = 12      # 12% шанс выигрыша
CASINO_PUBLIC_CASH_MULT = 5    # x5 множитель при выигрыше
CASINO_MIN_BET = 100           # минимальная ставка
CASINO_MAX_BET = 100000        # максимальная ставка

# ==================== ФАБРИКИ (ТОЧКИ) ====================
FACTORIES = {
    'свалка': {
        'name': '🗑️ Свалка',
        'slots': 50,
        'price': 1500,
        'income': 1,
        'income_type': 'RF',
        'level': 1,
        'duration': 72
    },
    'мастерская': {
        'name': '🔧 Мастерская',
        'slots': 30,
        'price': 5000,
        'income': 5,
        'income_type': 'RF',
        'level': 5,
        'duration': 72
    },
    'станция': {
        'name': '⚡ Станция',
        'slots': 25,
        'price': 10000,
        'income': 12,
        'income_type': 'RF',
        'level': 7,
        'duration': 72
    },
    'дамба': {
        'name': '🌊 Дамба',
        'slots': 10,
        'price': 15000,
        'income': 25,
        'income_type': 'RF',
        'level': 10,
        'duration': 72
    },
    'химка': {
        'name': '🧪 Химка',
        'slots': 7,
        'price': 25000,
        'income': 40,
        'income_type': 'RF',
        'level': 15,
        'duration': 72
    },
    'комплекс': {
        'name': '🏭 Комплекс',
        'slots': 5,
        'price': 100000,
        'income': 100,
        'income_type': 'RF',
        'level': 25,
        'duration': 72
    },
    'реактор': {
        'name': '☢️ Реактор',
        'slots': 3,
        'price': 500000,
        'income': 1000,
        'income_type': 'RF',
        'level': 50,
        'duration': 72
    }
}

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (БАЗОВЫЕ) ====================
def get_exp_for_level(level):
    """Опыт для повышения уровня"""
    if level <= 1:
        return 0
    if level > MAX_LEVEL:
        level = MAX_LEVEL
    total = 0
    for i in range(2, level + 1):
        total += 100 + (i - 2) * 50
    return total

def calculate_reward(level):
    """Базовая награда RC"""
    level = min(level, MAX_LEVEL)
    base = random.randint(11, 150)
    bonus = 1 + (level - 1) * 0.05
    if bonus > 1 + (MAX_LEVEL - 1) * 0.05:
        bonus = 1 + (MAX_LEVEL - 1) * 0.05
    return int(base * bonus)

def calculate_experience():
    """Базовая награда опыта"""
    return random.randint(10, 50)

def get_random_interval(user=None):
    """Интервал между сборами"""
    base = random.randint(30, 120)
    if user and user.cooldown_reducer_until and user.cooldown_reducer_until > datetime.now():
        base = base // 2
    if user and user.pet == 'кайот':
        base = base // 2
    return max(base, 5)

# ==================== ОТПРАВКА В ЛИЧКУ ====================
async def send_to_private(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Отправляет сообщение в личку, если команда вызвана в группе"""
    try:
        if update.effective_chat.type != 'private':
            await update.message.reply_text("📩 Информация отправлена в личные сообщения.")
            await context.bot.send_message(chat_id=update.effective_user.id, text=text)
        else:
            await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"Error sending to private: {e}")

# ==================== АВТОБЭКАП ====================
def auto_backup():
    """Автоматическое создание бэкапа базы данных"""
    try:
        db_path = 'radcoin_bot.db'
        if os.path.exists(db_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"radcoin_bot.db.backup_{timestamp}.db"
            backup_path = os.path.join(BACKUP_DIR, backup_name)
            shutil.copy(db_path, backup_path)
            backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('radcoin_bot.db.backup')])
            if len(backups) > 24:
                for old_backup in backups[:-24]:
                    os.remove(os.path.join(BACKUP_DIR, old_backup))
            logger.info(f"✅ Автобэкап: {backup_name}")
    except Exception as e:
        logger.error(f"❌ Ошибка автобэкапа: {e}")

# ==================== БЭКАПЫ ====================

async def backups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список бэкапов"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Нет прав!")
        return
    try:
        backups_list = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('radcoin_bot.db.backup')])
        if not backups_list:
            await update.message.reply_text("📋 *Нет бэкапов*", parse_mode='Markdown')
            return
        text = "💾 *Список бэкапов*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, backup in enumerate(backups_list[-10:], 1):
            text += f"{i}. `{backup}`\n"
        text += "\n📌 /restore [имя] — восстановить\n📌 /backup_now — создать бэкап"
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in backups: {e}")
        await update.message.reply_text("❌ Ошибка")

async def restore_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Восстановить бэкап"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Нет прав!")
        return
    if not context.args:
        await update.message.reply_text("❌ /restore [имя_бэкапа]")
        return
    backup_name = context.args[0]
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    if not os.path.exists(backup_path):
        await update.message.reply_text(f"❌ Бэкап `{backup_name}` не найден!")
        return
    auto_backup()
    shutil.copy(backup_path, 'radcoin_bot.db')
    await update.message.reply_text(f"✅ *База восстановлена!* Перезапустите бота.")
    os._exit(0)

async def backup_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создать бэкап сейчас"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Нет прав!")
        return
    try:
        if os.path.exists('radcoin_bot.db'):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"radcoin_bot.db.backup_{timestamp}.db"
            backup_path = os.path.join(BACKUP_DIR, backup_name)
            shutil.copy('radcoin_bot.db', backup_path)
            await update.message.reply_text(f"✅ *Бэкап создан:* `{backup_name}`", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ База не найдена!")
    except Exception as e:
        logger.error(f"Error in backup_now: {e}")
        await update.message.reply_text("❌ Ошибка")
