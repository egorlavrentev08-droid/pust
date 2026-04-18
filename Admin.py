import logging
from telegram import Update
from telegram.ext import ContextTypes
from models import Session, User, Clan

logger = logging.getLogger(__name__)
SUPER_ADMIN_IDS = [6595788533]

async def admin_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выдача ресурсов (ИСПРАВЛЕНИЕ 1)"""
    if update.effective_user.id not in SUPER_ADMIN_IDS: return

    if len(context.args) < 3:
        await update.message.reply_text("Использование: `/give [username] [тип] [кол-во]`")
        return

    target_username = context.args[0].replace("@", "")
    item_type = context.args[1].lower()
    try:
        amount = int(context.args[2])
    except: return

    session = Session()
    target_user = session.query(User).filter_by(username=target_username).first()

    if not target_user:
        await update.message.reply_text("❌ Пользователь не найден.")
        return

    # ЛОГИКА КРИСТАЛЛОВ: Если в клане — на счет клана
    if item_type == "crystals":
        if target_user.clan_id:
            clan = session.query(Clan).filter_by(id=target_user.clan_id).first()
            clan.treasury_crystals += amount
            msg = f"💎 {amount} кристаллов зачислены в казну клана *{clan.name}*"
        else:
            target_user.radcrystals += amount
            msg = f"💎 {amount} кристаллов выданы игроку лично (нет клана)."
    
    elif item_type == "coins":
        target_user.radcoins += amount
        msg = f"🪙 Выдано {amount} RC."
    
    session.commit()
    await update.message.reply_text(msg, parse_mode='Markdown')
    session.close()

async def radio_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Радио во все группы (ИСПРАВЛЕНИЕ 2)"""
    if update.effective_user.id not in SUPER_ADMIN_IDS: return
    
    if not context.args: return
    message_text = " ".join(context.args)
    broadcast_msg = f"📻 *ЭФИР РАДИО*\n\n{message_text}"

    session = Session()
    # Собираем все уникальные chat_id, где бот видел пользователей
    # Для лучшей работы рекомендуется создать отдельную таблицу GroupChats
    users = session.query(User).all()
    chat_ids = set([u.user_id for u in users]) 

    count = 0
    for cid in chat_ids:
        try:
            await context.bot.send_message(chat_id=cid, text=broadcast_msg, parse_mode='Markdown')
            count += 1
        except:
            continue
            
    await update.message.reply_text(f"✅ Сообщение отправлено в {count} каналов/чатов.")
    session.close()
