from telegram import Update
from telegram.ext import ContextTypes
from models import Session, User, Clan
import logging

logger = logging.getLogger(__name__)

async def clan_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основное меню клана"""
    user_id = update.effective_user.id
    session = Session()
    
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        await update.message.reply_text("❌ Вы не зарегистрированы.")
        return

    if not user.clan_id:
        await update.message.reply_text(
            "🏳️ *Вы не состоите в клане*\n\n"
            "Используйте `/clan create [название]` чтобы создать свой (1000 RC)\n"
            "Используйте `/clan join [ID]` чтобы вступить в существующий",
            parse_mode='Markdown'
        )
        return

    clan = session.query(Clan).filter_by(id=user.clan_id).first()
    
    # ИСПРАВЛЕНИЕ 1: Казна теперь отображает кристаллы
    text = (
        f"🏰 *Клан: {clan.name}* (ID: {clan.id})\n"
        f"👑 Лидер: ID {clan.leader_id}\n\n"
        f"💰 *Казна клана:*\n"
        f"🪙 RadCoins: {clan.treasury_coins:,.2f}\n"
        f"💎 Кристаллы: {clan.treasury_crystals:,}\n\n"
        f"👤 Ваша роль: {user.clan_role}"
    )
    
    await update.message.reply_text(text, parse_mode='Markdown')
    session.close()

async def create_clan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание нового клана"""
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("❌ Укажите название клана: `/clan create [название]`")
        return

    clan_name = " ".join(context.args)
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()

    if user.clan_id:
        await update.message.reply_text("❌ Вы уже состоите в клане.")
        return

    if user.radcoins < 1000:
        await update.message.reply_text("❌ Создание клана стоит 1000 RC.")
        return

    try:
        new_clan = Clan(name=clan_name, leader_id=user_id)
        session.add(new_clan)
        session.flush() # Получаем ID клана

        user.radcoins -= 1000
        user.clan_id = new_clan.id
        user.clan_role = 'leader'
        
        session.commit()
        await update.message.reply_text(f"🎉 Клан *{clan_name}* успешно создан!", parse_mode='Markdown')
    except Exception as e:
        session.rollback()
        await update.message.reply_text("❌ Клан с таким названием уже существует.")
    finally:
        session.close()

async def clan_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Внос RadCoins в казну (Кристаллы вносятся только админом)"""
    user_id = update.effective_user.id
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()

    if not user.clan_id or not context.args:
        return

    try:
        amount = float(context.args[0])
        if amount <= 0 or user.radcoins < amount:
            await update.message.reply_text("❌ Недостаточно средств или некорректная сумма.")
            return

        clan = session.query(Clan).filter_by(id=user.clan_id).first()
        user.radcoins -= amount
        clan.treasury_coins += amount
        
        session.commit()
        await update.message.reply_text(f"✅ Вы внесли {amount:,} RC в казну клана.")
    except:
        await update.message.reply_text("❌ Ошибка при транзакции.")
    finally:
        session.close()
