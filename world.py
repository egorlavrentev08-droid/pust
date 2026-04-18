import random
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from models import Session, User

logger = logging.getLogger(__name__)

# Список доступных локаций (ИЗМЕНЕНИЕ 3: Убрано Болото)
LOCATIONS = {
    "normal": {"name": "🌲 Кордон", "mult": 1.0, "min_level": 1},
    "military": {"name": "🎖 Военные склады", "mult": 1.5, "min_level": 10},
    "city": {"name": "🏙 Мертвый город", "mult": 2.0, "min_level": 20},
    "wasteland": {"name": "☢️ Пустошь", "mult": 2.5, "min_level": 30},
    "lab": {"name": "🔬 Лаборатория X-18", "mult": 3.0, "min_level": 40},
    "forest": {"name": "🌳 Рыжий лес", "mult": 3.5, "min_level": 50}
}

async def locate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Смена локации пользователя"""
    user_id = update.effective_user.id
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()

    if not context.args:
        text = "🌍 *Доступные локации:*\n\n"
        for loc_id, info in LOCATIONS.items():
            text += f"{info['name']} (ID: `{loc_id}`) — мин. lvl: {info['min_level']}\n"
        await update.message.reply_text(text, parse_mode='Markdown')
        return

    new_loc = context.args[0].lower()
    if new_loc not in LOCATIONS:
        await update.message.reply_text("❌ Такой локации не существует (или Болото было удалено).")
        return

    if user.level < LOCATIONS[new_loc]['min_level']:
        await update.message.reply_text(f"❌ Ваш уровень слишком мал для этой зоны (нужен {LOCATIONS[new_loc]['min_level']}).")
        return

    user.location = new_loc
    session.commit()
    await update.message.reply_text(f"🚀 Вы переместились в локацию: *{LOCATIONS[new_loc]['name']}*", parse_mode='Markdown')
    session.close()

async def factory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Работа на заводе (ИЗМЕНЕНИЕ 6: Убран блокиратор на 36 часов).
    Теперь проверяется только обычный кулдаун на работу.
    """
    user_id = update.effective_user.id
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()

    now = datetime.now()
    
    # Здесь оставляем только стандартный кулдаун (например, 1 час), 
    # полностью удалив проверку factory_bans или 36-часовые метки.
    if user.last_collection and (now - user.last_collection) < timedelta(hours=1):
        wait_time = timedelta(hours=1) - (now - user.last_collection)
        minutes = int(wait_time.total_seconds() // 60)
        await update.message.reply_text(f"⏳ Смена еще не закончена. Приходите через {minutes} мин.")
        return

    # Логика получения прибыли
    reward = random.randint(50, 200) * LOCATIONS.get(user.location, {"mult": 1})['mult']
    user.radcoins += reward
    user.last_collection = now
    
    session.commit()
    await update.message.reply_text(
        f"🏭 Вы отработали смену на заводе.\n💰 Получено: {reward:.2f} RC",
        parse_mode='Markdown'
    )
    session.close()
