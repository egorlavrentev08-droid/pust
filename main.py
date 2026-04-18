import logging
from telegram.ext import Application, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Импортируем настройки и базу данных
from models import Base, engine, Session

# Импортируем обработчики команд из наших будущих блоков
import economy
import clans
import games
import inventory
import world
import classes
import admin

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # 1. Создаем таблицы в БД (если их нет)
    Base.metadata.create_all(engine)

    # 2. Инициализируем планировщик для автобэкапов или кулдаунов
    scheduler = AsyncIOScheduler()
    scheduler.start()

    # 3. Настройка приложения бота
    TOKEN = "8492718356:AAF4pqw8050Td9dzxz_HKFsCX2aYjuyiVzM"
    app = Application.builder().token(TOKEN).build()

    # --- РЕГИСТРАЦИЯ КОМАНД ---

    # Блок 2: Экономика
    app.add_handler(CommandHandler("exchange", economy.exchange))
    
    # Блок 3: Кланы
    app.add_handler(CommandHandler("clan", clans.clan_main))
    
    # Блок 4: Казино и игры
    app.add_handler(CommandHandler("casino", games.casino))
    
    # Блок 5: Инвентарь и снаряжение
    app.add_handler(CommandHandler("inv", inventory.show_inventory))
    app.add_handler(CommandHandler("equip", inventory.equip_item))
    app.add_handler(CommandHandler("use", inventory.use_item)) # Тут будут аптечки
    
    # Блок 6: Мир и Локации
    app.add_handler(CommandHandler("locate", world.locate))
    app.add_handler(CommandHandler("factory", world.factory))
    
    # Блок 7: Ролевая система (Классы)
    # ИЗМЕНЕНИЕ 9: Две версии команды
    app.add_handler(CommandHandler("class_upd", classes.class_update_free))
    app.add_handler(CommandHandler("class_pay", classes.class_update_paid))
    
    # Блок 8: Администрирование и Радио
    # ИСПРАВЛЕНИЕ 1 и 2
    app.add_handler(CommandHandler("give", admin.admin_give))
    app.add_handler(CommandHandler("radio", admin.radio_broadcast))
    app.add_handler(CommandHandler("admin", admin.admin_panel))

    # Запуск бота
    print("Бот запущен и готов к работе...")
    app.run_polling()

if __name__ == '__main__':
    main()
