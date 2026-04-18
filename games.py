import random
import logging
from telegram import Update
from telegram.ext import ContextTypes
from models import Session, User

logger = logging.getLogger(__name__)

def calculate_survive_chance(user):
    """
    Логика выживания (ИЗМЕНЕНИЯ 7 и 8).
    Убрана Тересса. Убраны виды аптечек. 
    Только обычная аптечка дает 25% шанс на выживание (100% успех при срабатывании).
    """
    # Базовый шанс выжить без ничего — 10%
    base_chance = 0.10
    
    # Если у игрока есть аптечки
    if user.medkits > 0:
        # Шанс 25%, что аптечка поможет
        if random.random() < 0.25:
            return True # Игрок спасен
            
    # Если аптечка не сработала или её нет, проверяем базовый шанс
    return random.random() < base_chance

async def casino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда казино (ИЗМЕНЕНИЕ 4).
    Лимиты: от 100 до 100,000 RC.
    """
    user_id = update.effective_user.id
    session = Session()
    
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            await update.message.reply_text("❌ Сначала зарегистрируйтесь!")
            return

        if not context.args:
            await update.message.reply_text(
                "🎰 *Казино RadCoin*\n"
                "Использование: `/casino [ставка]`\n"
                "💰 Лимиты: от 100 до 100,000 RC",
                parse_mode='Markdown'
            )
            return

        try:
            bet = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Ставка должна быть целым числом.")
            return

        # ИЗМЕНЕНИЕ 4: Проверка лимитов
        if bet < 100 or bet > 100000:
            await update.message.reply_text("❌ Лимит ставки: от 100 до 100,000 RC.")
            return

        if user.radcoins < bet:
            await update.message.reply_text(f"❌ Недостаточно RadCoins (баланс: {user.radcoins:.2f})")
            return

        # Механика игры (50/50)
        if random.random() < 0.48: # Шанс чуть меньше 50% в пользу заведения
            win_amount = bet # Выигрыш равен ставке (удвоение)
            user.radcoins += win_amount
            result_text = f"🎉 Победа! Вы выиграли {win_amount:,} RC!"
        else:
            user.radcoins -= bet
            result_text = f"💀 Проигрыш! Вы потеряли {bet:,} RC."

        session.commit()
        await update.message.reply_text(
            f"{result_text}\n💰 Ваш баланс: {user.radcoins:,.2f} RC",
            parse_mode='Markdown'
        )

    except Exception as e:
        session.rollback()
        logger.error(f"Error in casino: {e}")
        await update.message.reply_text("⚠️ Ошибка в работе казино.")
    finally:
        session.close()
