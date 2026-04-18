import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Импортируем движок базы данных и модели
from models import Base, engine, Session, init_db

# Импортируем блоки с логикой (убедись, что файлы созданы)
import admin
import economy
import clans
import games
import inventory
import world
import classes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # 1. Инициализация базы данных
    init_db()

    # 2. Настройка планировщика задач (для бэкапов и кулдаунов)
    scheduler = AsyncIOScheduler()
    # Здесь можно добавить задачу на автобэкап, как в твоем старом коде
    # scheduler.add_job(auto_backup, 'interval', hours=24)
    scheduler.start()

    # 3. Инициализация бота
    TOKEN = "ТВОЙ_ТОКЕН_ЗДЕСЬ" # Вставь свой токен от @BotFather
    app = Application.builder().token(TOKEN).build()

    # ==================== РЕГИСТРАЦИЯ КОМАНД ====================

    # --- Блок: Профиль и Экономика ---
    app.add_handler(CommandHandler("balance", economy.balance))
    app.add_handler(CommandHandler("exchange", economy.exchange)) # Лимит 1кк RF внутри

    # --- Блок: Кланы (Исправлено начисление кристаллов) ---
    app.add_handler(CommandHandler("clan", clans.clan_main))

    # --- Блок: Игры и Казино (Лимиты 100 - 100,000 RC) ---
    app.add_handler(CommandHandler("casino", games.casino))

    # --- Блок: Инвентарь и Предметы (Без камуфляжа, щита, металлоискателя) ---
    app.add_handler(CommandHandler("inv", inventory.show_inventory))
    app.add_handler(CommandHandler("use", inventory.use_item)) # Аптечка 25% шанс внутри

    # --- Блок: Мир и Прогрессия (Без Болота и лока 36ч) ---
    app.add_handler(CommandHandler("locate", world.locate))
    app.add_handler(CommandHandler("factory", world.factory))

    # --- Блок: Ролевая система (Две версии команды) ---
    app.add_handler(CommandHandler("class_upd", classes.class_update_free)) # Раз в неделю
    app.add_handler(CommandHandler("class_pay", classes.class_update_paid)) # Платно (RF + RC)

    # --- Блок: Администрирование (Исправлено Радио и выдача) ---
    app.add_handler(CommandHandler("give", admin.admin_give))
    app.add_handler(CommandHandler("radio", admin.radio_broadcast))
    app.add_handler(CommandHandler("take", admin.admin_take))
    app.add_handler(CommandHandler("setlevel", admin.admin_setlevel))
    app.add_handler(CommandHandler("reset", admin.admin_reset))

    # --- Обработка обычных сообщений (если нужна логика опыта за общение) ---
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, world.handle_message))

    # ============================================================

    print("--- Бот запущен (с учетом новых исправлений) ---")
    app.run_polling()

if __name__ == '__main__':
    main()
