from telegram import Update
from telegram.ext import ContextTypes
from models import Session, User
import logging

logger = logging.getLogger(__name__)

# Курс обмена: 1 RF = 10 RC (можно настроить под себя)
EXCHANGE_RATE = 10

async def exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обмен RadFragments (RF) на RadCoins (RC)"""
    user_id = update.effective_user.id
    session = Session()
    
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            await update.message.reply_text("❌ Вы не зарегистрированы! Используйте /start")
            return

        if not context.args:
            await update.message.reply_text(
                "💱 *Обменник*\n"
                f"Курс: 1 RF = {EXCHANGE_RATE} RC\n"
                "Использование: `/exchange [количество RF]`\n"
                "_Лимит: до 1,000,000 RF за раз_",
                parse_mode='Markdown'
            )
            return

        # Проверка введенного числа
        try:
            rf_amount = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Введите корректное целое число.")
            return

        if rf_amount <= 0:
            await update.message.reply_text("❌ Сумма должна быть больше 0.")
            return

        # ИЗМЕНЕНИЕ 5: Лимит до 1,000,000 RF
        if rf_amount > 1000000:
            await update.message.reply_text("❌ Ошибка: нельзя обменять более 1,000,000 RF за одну операцию.")
            return

        # Проверка наличия средств
        if user.radfragments < rf_amount:
            await update.message.reply_text(f"❌ У вас недостаточно RF (баланс: {user.radfragments} RF).")
            return

        # Проведение транзакции
        rc_gain = rf_amount * EXCHANGE_RATE
        user.radfragments -= rf_amount
        user.radcoins += rc_gain
        
        session.commit()

        await update.message.reply_text(
            f"✅ *Обмен завершен!*\n"
            f"📉 Списано: {rf_amount:,} RF\n"
            f"📈 Получено: {rc_gain:,} RC",
            parse_mode='Markdown'
        )

    except Exception as e:
        session.rollback()
        logger.error(f"Error in exchange: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при обмене.")
    finally:
        session.close()

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр баланса пользователя"""
    user_id = update.effective_user.id
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    
    if user:
        await update.message.reply_text(
            f"💰 *Ваш кошелек:*\n"
            f"🪙 RadCoins: {user.radcoins:,.2f}\n"
            f"🧩 RadFragments: {user.radfragments:,}\n"
            f"💎 RadCrystals: {user.radcrystals:,}",
            parse_mode='Markdown'
        )
    session.close()
