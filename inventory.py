import json
import logging
from telegram import Update
from telegram.ext import ContextTypes
from models import Session, User

logger = logging.getLogger(__name__)

# Список разрешенных предметов (ИЗМЕНЕНИЕ 1: Убраны Камуфляж, Щит, Металлоискатель)
VALID_ITEMS = {
    "medkit": "Обычная аптечка",
    "energy_drink": "Энергетик",
    "bread": "Батон",
    "vodka": "Казаки"
}

# Список разрешенных питомцев (ИЗМЕНЕНИЕ 2: Убраны Алабай и Лис)
VALID_PETS = ["Овчарка", "Кот", "Ворон"]

def get_inventory(user):
    return json.loads(user.inventory) if user.inventory else []

def save_inventory(user, inventory):
    user.inventory = json.dumps(inventory)

async def show_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображение инвентаря пользователя"""
    user_id = update.effective_user.id
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    
    if not user:
        await update.message.reply_text("❌ Зарегистрируйтесь!")
        return

    inventory = get_inventory(user)
    
    if not inventory and user.medkits == 0:
        await update.message.reply_text("🎒 Ваш инвентарь пуст.")
        return

    text = "🎒 *Ваш инвентарь:*\n\n"
    # ИЗМЕНЕНИЕ 8: Аптечки вынесены как основной ресурс
    if user.medkits > 0:
        text += f"💉 Аптечки: {user.medkits} шт.\n"
    
    for item in inventory:
        item_name = VALID_ITEMS.get(item['item'], item['item'])
        text += f"📦 {item_name}: {item['count']} шт.\n"
    
    if user.pet:
        text += f"\n🐾 Питомец: {user.pet}"

    await update.message.reply_text(text, parse_mode='Markdown')
    session.close()

async def use_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Использование предмета"""
    if not context.args:
        await update.message.reply_text("❓ Что вы хотите использовать? Пример: `/use medkit`")
        return

    item_to_use = context.args[0].lower()
    user_id = update.effective_user.id
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()

    # Логика для аптечки
    if item_to_use == "medkit":
        if user.medkits > 0:
            # Аптечки теперь используются автоматически при смерти (в games.py),
            # но здесь можно оставить проверку здоровья или просто инфо.
            await update.message.reply_text("💉 Аптечка готова к использованию! Она сработает автоматически в случае опасности (шанс 25%).")
        else:
            await update.message.reply_text("❌ У вас нет аптечек.")
        return

    # Логика для остальных предметов
    inventory = get_inventory(user)
    item_found = False
    
    for item in inventory:
        if item['item'] == item_to_use:
            if item['count'] > 0:
                item['count'] -= 1
                item_found = True
                if item['count'] <= 0:
                    inventory.remove(item)
                break
    
    if item_found:
        save_inventory(user, inventory)
        session.commit()
        await update.message.reply_text(f"✅ Вы использовали {VALID_ITEMS.get(item_to_use, item_to_use)}.")
    else:
        await update.message.reply_text("❌ Предмет не найден в инвентаре.")
    
    session.close()

async def equip_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экипировка (Здесь была бы логика щитов/камуфляжа, но мы их убрали)"""
    await update.message.reply_text("🛡 Система брони будет обновлена в следующем патче.")
