# main.py - Запуск и регистрация команд
# Версия: 3.0.0

import os
import sys
import glob
import shutil
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

# Импорты из config
from config import logger, TOKEN, CASINO_PUBLIC_CHANCE, CASINO_PUBLIC_CASH_MULT, SHOP_LIMITS, BACKUP_DIR, BACKUP_RETENTION_DAYS

# Импорты из core
from core import backups, restore_backup, backup_now, auto_backup, is_admin, send_to_private

# Импорты из database
from database import Session, User, Clan

# Импорты команд из user
from user import start, help_command, profile, stats, achievements, announce, phase_info, class_command, class_info

# Импорты команд из collect
from collect import collect, hunt, locate, pet_command

# Импорты команд из money
from money import shop, buy, sell, equip, casino, exchange, craft, inv, use_item

# Импорты команд из clan
from clan import clan_command, radion, radio, radio_register_group, aradio

# Импорты команд из chest
from chest import chest_command, factory, afactory

# Импорты команд из admin
from admin import (
    admin_giveme, admin_phase, admin_give, admin_take, admin_setlevel,
    admin_cd, admin_resethunt, admin_item, admin_pets, admin_manage, admins,
    admin_classes, call, lscall, admin_hide, top_command, acasino,
    advice_handler, gchest, admin_players, sale, check_user, admin_reset
)

# Создаём шедулер
scheduler = AsyncIOScheduler()


# ==================== СИСТЕМА АВТО-ВОССТАНОВЛЕНИЯ БАЗЫ ====================

def get_latest_backup():
    """Найти самый свежий бэкап"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        return None
    backups = glob.glob(os.path.join(BACKUP_DIR, "radcoin_bot.db.backup_*.db"))
    if not backups:
        return None
    return max(backups, key=os.path.getctime)


def restore_from_backup(backup_path):
    """Восстановить базу из бэкапа"""
    try:
        if not os.path.exists(backup_path):
            return False
        shutil.copy2(backup_path, 'radcoin_bot.db')
        logger.info(f"✅ База данных восстановлена из бэкапа: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка восстановления: {e}")
        return False


def check_and_restore_db():
    """Проверить базу при запуске и восстановить при необходимости"""
    # Создаём папку для бэкапов
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Если база существует и не пустая — всё ок
    if os.path.exists('radcoin_bot.db'):
        if os.path.getsize('radcoin_bot.db') > 0:
            logger.info("✅ База данных найдена, проверка пройдена")
            return True
        else:
            logger.warning("⚠️ База данных повреждена (0 байт)!")
    
    # База отсутствует или повреждена — пробуем восстановить
    logger.warning("⚠️ База данных отсутствует или повреждена! Пытаюсь восстановить из бэкапа...")
    
    latest = get_latest_backup()
    if latest and restore_from_backup(latest):
        logger.info("✅ База данных успешно восстановлена из последнего бэкапа")
        return True
    
    # Создаём новую базу
    logger.warning("⚠️ Бэкапов не найдено. Будет создана новая база данных.")
    return True  # Пусть создаётся новая


async def restore_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Восстановить последний бэкап (админ)"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Нет прав!")
        return
    
    latest = get_latest_backup()
    if not latest:
        await update.message.reply_text("❌ Нет доступных бэкапов!")
        return
    
    if restore_from_backup(latest):
        await update.message.reply_text(f"✅ База восстановлена из бэкапа!\n🔄 Бот будет перезапущен...")
        os._exit(0)  # Хостинг перезапустит бота
    else:
        await update.message.reply_text("❌ Ошибка восстановления!")


# ==================== РЕГИСТРАЦИЯ КОМАНД ====================

def register_handlers(app):
    """Регистрация всех обработчиков команд"""

    # Основные команды пользователя
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("achievements", achievements))
    app.add_handler(CommandHandler("announce", announce))
    app.add_handler(CommandHandler("phase_info", phase_info))

    # Ресурсы и охота
    app.add_handler(CommandHandler("collect", collect))
    app.add_handler(CommandHandler("hunt", hunt))
    app.add_handler(CommandHandler("locate", locate))
    app.add_handler(CommandHandler("pet", pet_command))

    # Экономика
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("equip", equip))
    app.add_handler(CommandHandler("casino", casino))
    app.add_handler(CommandHandler("exchange", exchange))
    app.add_handler(CommandHandler("craft", craft))
    app.add_handler(CommandHandler("inv", inv))
    app.add_handler(CommandHandler("use", use_item))

    # Классы
    app.add_handler(CommandHandler("class", class_command))
    app.add_handler(CommandHandler("class_info", class_info))

    # Кланы и радио
    app.add_handler(CommandHandler("clan", clan_command))
    app.add_handler(CommandHandler("radion", radion))
    app.add_handler(CommandHandler("radio", radio))
    app.add_handler(CommandHandler("aradio", aradio))

    # Сундуки и фабрики
    app.add_handler(CommandHandler("chest", chest_command))
    app.add_handler(CommandHandler("factory", factory))
    app.add_handler(CommandHandler("afactory", afactory))

    # Таблица лидеров
    app.add_handler(CommandHandler("top", top_command))
    app.add_handler(CommandHandler("hide", admin_hide))

    # Советы
    app.add_handler(CommandHandler("advice", advice_handler))

    # Бэкапы
    app.add_handler(CommandHandler("backups", backups))
    app.add_handler(CommandHandler("restore", restore_backup))
    app.add_handler(CommandHandler("backup_now", backup_now))
    app.add_handler(CommandHandler("restore_last", restore_last))

    # Распродажи
    app.add_handler(CommandHandler("sale", sale))

    # Админские команды
    app.add_handler(CommandHandler("givemeplsadmin", admin_giveme))
    app.add_handler(CommandHandler("phase", admin_phase))
    app.add_handler(CommandHandler("give", admin_give))
    app.add_handler(CommandHandler("take", admin_take))
    app.add_handler(CommandHandler("setlevel", admin_setlevel))
    app.add_handler(CommandHandler("cd", admin_cd))
    app.add_handler(CommandHandler("resethunt", admin_resethunt))
    app.add_handler(CommandHandler("item", admin_item))
    app.add_handler(CommandHandler("pets", admin_pets))
    app.add_handler(CommandHandler("players", admin_players))
    app.add_handler(CommandHandler("admins", admins))
    app.add_handler(CommandHandler("admin", admin_manage))
    app.add_handler(CommandHandler("classes", admin_classes))
    app.add_handler(CommandHandler("call", call))
    app.add_handler(CommandHandler("lscall", lscall))
    app.add_handler(CommandHandler("gchest", gchest))
    app.add_handler(CommandHandler("acasino", acasino))
    app.add_handler(CommandHandler("check", check_user))
    app.add_handler(CommandHandler("reset", admin_reset))
    
    # Обработчик для регистрации групп в радио
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, radio_register_group))


# ==================== ИНИЦИАЛИЗАЦИЯ ====================

def init_bot_data(app):
    """Инициализация данных бота"""
    app.bot_data['phase'] = 1
    app.bot_data['casino_public_chance'] = CASINO_PUBLIC_CHANCE
    app.bot_data['casino_public_cash_mult'] = CASINO_PUBLIC_CASH_MULT
    app.bot_data['radio_groups'] = set()
    app.bot_data['shop_limits'] = SHOP_LIMITS.copy()
    app.bot_data['last_shop_reset'] = datetime.now()
    app.bot_data['sale_discount'] = 0
    app.bot_data['sale_until'] = None

    logger.info("📦 Данные бота инициализированы")


# ==================== ЗАПУСК ====================

def main():
    """Запуск бота"""
    from telegram.ext import Application

    # ===== ПРОВЕРКА И ВОССТАНОВЛЕНИЕ БАЗЫ ДАННЫХ ПРИ ЗАПУСКЕ =====
    if not check_and_restore_db():
        logger.critical("❌ Не удалось восстановить базу данных! Бот не может запуститься.")
        return
    # ==============================================================

    app = Application.builder().token(TOKEN).build()

    init_bot_data(app)
    register_handlers(app)

    # Запускаем планировщик для автобэкапов (каждые 15 минут)
    scheduler.add_job(auto_backup, 'interval', minutes=15)
    scheduler.start()

    logger.info("🌟 RadCoin Bot 3.0 запущен! Пустошь ждёт своих героев!")
    logger.info(f"🎰 Настройки казино: шанс {CASINO_PUBLIC_CHANCE}%, множитель x{CASINO_PUBLIC_CASH_MULT}")
    logger.info(f"💾 Автобэкапы каждые 15 минут, хранение {BACKUP_RETENTION_DAYS} дней")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    app.run_polling()


if __name__ == '__main__':
    main()
