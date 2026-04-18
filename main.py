# main.py - Запуск и регистрация команд
# Версия: 2.0.0

from telegram.ext import CommandHandler, MessageHandler, filters
from core import logger, scheduler, auto_backup, CASINO_PUBLIC_CHANCE, CASINO_PUBLIC_CASH_MULT
from database import Session

# Импорт всех команд из блоков
from user import (
    start, help_command, profile, stats, achievements, announce, phase_info
)
from collect import (
    collect, hunt, locate, pet_command
)
from money import (
    shop, buy, sell, equip, casino, exchange, craft
)
from clan import (
    clan_command, radion, radio, radio_register_group, aradio
)
from chest import (
    chest_command, factory
)
from admin import (
    admin_giveme, admin_phase, admin_give, admin_take, admin_setlevel,
    admin_cd, admin_resethunt, admin_item, admin_pets, admin_manage, admins,
    admin_classes, call, lscall, admin_hide, top_command, acasino,
    advice_handler, gchest
)

# ==================== ФАБРИКИ (АДМИН-КОМАНДЫ) ====================
# Импортируем админ-команды фабрик из chest.py
from chest import afactory

# ==================== КОМАНДЫ КЛАССОВ ====================
# Отдельные команды для классов (из user.py нужно добавить)
# В user.py уже есть class_command и class_info, добавим их в импорт
from user import class_command as class_cmd
from user import class_info

# Переименовываем чтобы не было конфликта
class_command = class_cmd

# ==================== БЭКАПЫ ====================
from core import backups, restore_backup, backup_now

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
    
    # Обработчик для регистрации групп в радио
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, radio_register_group))

# ==================== ИНИЦИАЛИЗАЦИЯ БОТА ====================

def init_bot_data(app):
    """Инициализация данных бота"""
    # Фаза Пустоши (по умолчанию 1 - мирная)
    app.bot_data['phase'] = 1
    
    # Настройки казино
    app.bot_data['casino_public_chance'] = CASINO_PUBLIC_CHANCE
    app.bot_data['casino_public_cash_mult'] = CASINO_PUBLIC_CASH_MULT
    
    # Список групп для радио
    app.bot_data['radio_groups'] = set()
    
    logger.info("📦 Данные бота инициализированы")

# ==================== ЗАПУСК ====================

def main():
    """Запуск бота"""
    from telegram.ext import Application
    
    # Используем токен из core
    from core import TOKEN
    
    # Создаём приложение
    app = Application.builder().token(TOKEN).build()
    
    # Инициализируем данные
    init_bot_data(app)
    
    # Регистрируем обработчики
    register_handlers(app)
    
    # Запускаем планировщик для автобэкапов (каждый час)
    scheduler.add_job(auto_backup, 'interval', hours=1)
    scheduler.start()
    
    logger.info("🌟 RadCoin Bot 2.0 запущен! Пустошь ждёт своих героев!")
    logger.info(f"🎰 Настройки казино: шанс {CASINO_PUBLIC_CHANCE}%, множитель x{CASINO_PUBLIC_CASH_MULT}")
    logger.info(f"🏭 Фабрики: {len(FACTORIES)} точек")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Запускаем поллинг
    app.run_polling()

# ==================== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ====================
# Функция admin_players (не была импортирована, добавим)

async def admin_players(update, context):
    """Список всех игроков (админ)"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Нет прав!")
        return
    session = Session()
    try:
        users = session.query(User).order_by(User.level.desc()).all()
        if not users:
            await update.message.reply_text("📋 *Нет игроков*", parse_mode='Markdown')
            return
        text = "👥 *Список игроков*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, u in enumerate(users, 1):
            clan_name = "—"
            if u.clan_id:
                clan = session.query(Clan).filter_by(id=u.clan_id).first()
                if clan:
                    clan_name = clan.name
            text += f"{i}. *{u.username or f'ID:{u.user_id}'}* — ур.{u.level}, RC:{u.radcoins:.0f}, 🏰{clan_name}\n"
            if len(text) > 3500:
                await update.message.reply_text(text, parse_mode='Markdown')
                text = ""
        if text:
            await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in admin_players: {e}")
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

# Добавляем недостающие импорты для admin_players
from database import User, Clan
from utils import is_admin
from core import FACTORIES

# Переопределяем admin_players в регистрации
# Нужно добавить в register_handlers:
# app.add_handler(CommandHandler("players", admin_players))

# Обновляем регистрацию
def register_handlers_full(app):
    """Полная регистрация всех обработчиков"""
    register_handlers(app)
    app.add_handler(CommandHandler("players", admin_players))

# Исправляем main
def main_full():
    """Полный запуск бота"""
    from telegram.ext import Application
    from core import TOKEN
    
    app = Application.builder().token(TOKEN).build()
    init_bot_data(app)
    register_handlers_full(app)
    
    scheduler.add_job(auto_backup, 'interval', hours=1)
    scheduler.start()
    
    logger.info("🌟 RadCoin Bot 2.0 запущен! Пустошь ждёт своих героев!")
    app.run_polling()

if __name__ == '__main__':
    main_full()
