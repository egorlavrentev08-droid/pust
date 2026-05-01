# chest.py - Сундуки
# Версия: 3.0.0

import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from config import logger
from core import send_to_private
from database import Session, User
from utils import add_item_to_inventory, log_user_action


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def escape_markdown(text: str) -> str:
    """Экранирует спецсимволы для Markdown"""
    if not text:
        return ""
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for ch in chars:
        text = text.replace(ch, f'\\{ch}')
    return text


def safe_log_user_action(user_id, username, action, amount_rc=0, amount_rf=0, amount_crystals=0, item=None):
    """Безопасное логирование — не ломает основную команду"""
    try:
        session = Session()
        from database import UserLog
        log = UserLog(
            user_id=user_id, username=username, action=action,
            amount_rc=amount_rc, amount_rf=amount_rf,
            amount_crystals=amount_crystals, item=item,
            timestamp=datetime.now()
        )
        session.add(log)
        session.commit()
        session.close()
    except Exception as e:
        logger.error(f"⚠️ Ошибка логирования: {e}")


# ==================== СУНДУКИ ====================

async def chest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главная команда сундуков"""
    if not context.args:
        await update.message.reply_text(
            "🎁 *Сундуки Пустоши*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "/chest list — список сундуков\n"
            "/chest chance — шансы выпадения\n"
            "/chest open common — открыть обычный\n"
            "/chest open rare — открыть редкий\n"
            "/chest open epic — открыть эпический\n"
            "/chest open mythic — открыть мифический\n"
            "/chest open legendary — открыть легендарный\n"
            "/chest open all — открыть все сундуки сразу",
            parse_mode='Markdown'
        )
        return
    
    action = context.args[0].lower()
    
    if action == 'list':
        await chest_list(update, context)
    elif action == 'chance':
        await chest_chance(update, context)
    elif action == 'open':
        if len(context.args) > 1:
            if context.args[1].lower() == 'all':
                await chest_open_all(update, context)
            else:
                await chest_open(update, context, context.args[1].lower())
        else:
            await update.message.reply_text("❌ /chest open [common/rare/epic/mythic/legendary/all]")
    else:
        await update.message.reply_text("❌ Используйте: list, chance, open")


async def chest_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список сундуков пользователя"""
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=update.effective_user.id).first()
        if not user:
            await update.message.reply_text("❌ /start")
            return
        text = (
            f"🎁 *Ваши сундуки*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🟢 *Обычные:* {user.chest_common}\n"
            f"🔵 *Редкие:* {user.chest_rare}\n"
            f"🟣 *Эпические:* {user.chest_epic}\n"
            f"🟡 *Мифические:* {user.chest_mythic}\n"
            f"🟠 *Легендарные:* {user.chest_legendary}\n\n"
            "💡 /chest open [тип] — открыть"
        )
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in chest_list: {e}")
        await update.message.reply_text("❌ Ошибка")
    finally:
        session.close()


async def chest_chance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шансы выпадения из сундуков"""
    text = (
        "🎲 *Шансы выпадения в сундуках*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "*🟢 ОБЫЧНЫЙ* (2 предмета)\n"
        "☢️ RC 100-500\n☣️ RF 2-10\n💊 Аптечка\n\n"
        "*🔵 РЕДКИЙ* (3 предмета)\n"
        "☢️ RC 500-1500\n☣️ RF 10-50\n🎣 Гарпун\n🥉 Лёгкая броня\n💊 Аптечка\n⚡ Энергетик\n\n"
        "*🟣 ЭПИЧЕСКИЙ* (4 предмета)\n"
        "☢️ RC 1000-3000\n☣️ RF 50-200\n🥈 Утяжеленная броня\n🎣 Гарпун\n💊 Аптечка\n⚡ Энергетик\n⏱️ Редуктор\n🟢 Обычный сундук\n\n"
        "*🟡 МИФИЧЕСКИЙ* (4 предмета)\n"
        "☢️ RC 2500-6000\n☣️ RF 150-500\n🥉 Тактическая броня\n🔫 Винтовка\n🎣 Гарпун\n💊 Аптечка\n⏱️ Редуктор\n⚡ Энергетик\n🐾 Питомец (0.5%)\n🟣 Эпический сундук\n\n"
        "*🟠 ЛЕГЕНДАРНЫЙ* (5 предметов)\n"
        "☢️ RC 5000-15000\n☣️ RF 500-1500\n🥇 Силовая броня\n⚡ Винтовка Гаусса\n💊 Аптечка\n⏱️ Редуктор\n⚡ Энергетик\n🐾 Питомец (2%)\n🎣 Гарпун\n🟡 Мифический сундук"
    )
    await update.message.reply_text(text, parse_mode='Markdown')


async def chest_open(update: Update, context: ContextTypes.DEFAULT_TYPE, chest_type: str):
    """Открыть сундук определённого типа"""
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=update.effective_user.id).first()
        if not user:
            await update.message.reply_text("❌ /start")
            return
        
        rc_gain = 0
        rf_gain = 0
        log_user_id = user.user_id
        log_username = user.username
        
        if chest_type == 'common':
            if user.chest_common <= 0:
                await update.message.reply_text("❌ Нет обычных сундуков")
                return
            user.chest_common -= 1
            items = ['rc', 'rf', 'medkit']
            random.shuffle(items)
            selected = items[:2]
            rewards = []
            for r in selected:
                if r == 'rc':
                    amt = random.randint(100, 500)
                    rc_gain += amt
                    user.radcoins += amt
                    rewards.append(f"☢️ {amt} RC")
                elif r == 'rf':
                    amt = random.randint(2, 10)
                    rf_gain += amt
                    user.radfragments += amt
                    rewards.append(f"☣️ {amt} RF")
                elif r == 'medkit':
                    add_item_to_inventory(user, 'аптечка', 1)
                    rewards.append("💊 Аптечка")
            name = "🟢 Обычный сундук"
        
        elif chest_type == 'rare':
            if user.chest_rare <= 0:
                await update.message.reply_text("❌ Нет редких сундуков")
                return
            user.chest_rare -= 1
            items = ['rc', 'rf', 'harpoon', 'armor1', 'medkit', 'energy']
            random.shuffle(items)
            selected = items[:3]
            rewards = []
            for r in selected:
                if r == 'rc':
                    amt = random.randint(500, 1500)
                    rc_gain += amt
                    user.radcoins += amt
                    rewards.append(f"☢️ {amt} RC")
                elif r == 'rf':
                    amt = random.randint(10, 50)
                    rf_gain += amt
                    user.radfragments += amt
                    rewards.append(f"☣️ {amt} RF")
                elif r == 'harpoon':
                    add_item_to_inventory(user, 'гарпун', 1)
                    rewards.append("🎣 Гарпун")
                elif r == 'armor1':
                    add_item_to_inventory(user, 'броня1', 1)
                    rewards.append("🥉 Лёгкая броня")
                elif r == 'medkit':
                    amt = random.randint(1, 3)
                    add_item_to_inventory(user, 'аптечка', amt)
                    rewards.append(f"💊 Аптечка x{amt}")
                elif r == 'energy':
                    add_item_to_inventory(user, 'энергетик', 1)
                    rewards.append("⚡ Энергетик")
            name = "🔵 Редкий сундук"
        
        elif chest_type == 'epic':
            if user.chest_epic <= 0:
                await update.message.reply_text("❌ Нет эпических сундуков")
                return
            user.chest_epic -= 1
            items = ['rc', 'rf', 'armor2', 'harpoon', 'medkit', 'energy', 'reducer', 'chest_common']
            random.shuffle(items)
            selected = items[:4]
            rewards = []
            for r in selected:
                if r == 'rc':
                    amt = random.randint(1000, 3000)
                    rc_gain += amt
                    user.radcoins += amt
                    rewards.append(f"☢️ {amt} RC")
                elif r == 'rf':
                    amt = random.randint(50, 200)
                    rf_gain += amt
                    user.radfragments += amt
                    rewards.append(f"☣️ {amt} RF")
                elif r == 'armor2':
                    add_item_to_inventory(user, 'броня2', 1)
                    rewards.append("🥈 Утяжеленная броня")
                elif r == 'harpoon':
                    add_item_to_inventory(user, 'гарпун', 1)
                    rewards.append("🎣 Гарпун")
                elif r == 'medkit':
                    amt = random.randint(1, 3)
                    add_item_to_inventory(user, 'аптечка', amt)
                    rewards.append(f"💊 Аптечка x{amt}")
                elif r == 'energy':
                    add_item_to_inventory(user, 'энергетик', 1)
                    rewards.append("⚡ Энергетик")
                elif r == 'reducer':
                    add_item_to_inventory(user, 'редуктор', 1)
                    rewards.append("⏱️ Редуктор")
                elif r == 'chest_common':
                    user.chest_common += 1
                    rewards.append("🟢 Обычный сундук")
            name = "🟣 Эпический сундук"
        
        elif chest_type == 'mythic':
            if user.chest_mythic <= 0:
                await update.message.reply_text("❌ Нет мифических сундуков")
                return
            user.chest_mythic -= 1
            items = ['rc', 'rf', 'armor3', 'rifle', 'harpoon', 'medkit', 'reducer', 'energy', 'pet', 'chest_epic']
            random.shuffle(items)
            selected = items[:4]
            rewards = []
            pet_added = False
            for r in selected:
                if r == 'rc':
                    amt = random.randint(2500, 6000)
                    rc_gain += amt
                    user.radcoins += amt
                    rewards.append(f"☢️ {amt} RC")
                elif r == 'rf':
                    amt = random.randint(150, 500)
                    rf_gain += amt
                    user.radfragments += amt
                    rewards.append(f"☣️ {amt} RF")
                elif r == 'armor3':
                    add_item_to_inventory(user, 'броня3', 1)
                    rewards.append("🥉 Тактическая броня")
                elif r == 'rifle':
                    add_item_to_inventory(user, 'винтовка', 1)
                    rewards.append("🔫 Винтовка")
                elif r == 'harpoon':
                    add_item_to_inventory(user, 'гарпун', 1)
                    rewards.append("🎣 Гарпун")
                elif r == 'medkit':
                    amt = random.randint(2, 5)
                    add_item_to_inventory(user, 'аптечка', amt)
                    rewards.append(f"💊 Аптечка x{amt}")
                elif r == 'reducer':
                    add_item_to_inventory(user, 'редуктор', 1)
                    rewards.append("⏱️ Редуктор")
                elif r == 'energy':
                    amt = random.randint(2, 3)
                    add_item_to_inventory(user, 'энергетик', amt)
                    rewards.append(f"⚡ Энергетик x{amt}")
                elif r == 'pet':
                    if not pet_added and random.random() < 0.005:
                        pets = ['овчарка', 'волк', 'рысь', 'пума', 'попугай', 'кайот']
                        pet = random.choice(pets)
                        user.pet = pet
                        pet_names = {
                            'овчарка': '🐕 Овчарка', 'волк': '🐺 Волк',
                            'рысь': '🐈 Рысь', 'пума': '🐆 Пума',
                            'попугай': '🦜 Попугай', 'кайот': '🐕 Кайот'
                        }
                        rewards.append(f"🐾 {pet_names.get(pet, pet)}")
                        pet_added = True
                elif r == 'chest_epic':
                    user.chest_epic += 1
                    rewards.append("🟣 Эпический сундук")
            name = "🟡 Мифический сундук"
        
        elif chest_type == 'legendary':
            if user.chest_legendary <= 0:
                await update.message.reply_text("❌ Нет легендарных сундуков")
                return
            user.chest_legendary -= 1
            items = ['rc', 'rf', 'armor5', 'gauss', 'medkit', 'reducer', 'energy', 'pet', 'harpoon', 'chest_mythic']
            random.shuffle(items)
            selected = items[:5]
            rewards = []
            pet_added = False
            for r in selected:
                if r == 'rc':
                    amt = random.randint(5000, 15000)
                    rc_gain += amt
                    user.radcoins += amt
                    rewards.append(f"☢️ {amt} RC")
                elif r == 'rf':
                    amt = random.randint(500, 1500)
                    rf_gain += amt
                    user.radfragments += amt
                    rewards.append(f"☣️ {amt} RF")
                elif r == 'armor5':
                    add_item_to_inventory(user, 'броня5', 1)
                    rewards.append("🥇 Силовая броня")
                elif r == 'gauss':
                    add_item_to_inventory(user, 'гаусс', 1)
                    rewards.append("⚡ Винтовка Гаусса")
                elif r == 'medkit':
                    amt = random.randint(2, 5)
                    add_item_to_inventory(user, 'аптечка', amt)
                    rewards.append(f"💊 Аптечка x{amt}")
                elif r == 'reducer':
                    add_item_to_inventory(user, 'редуктор', 1)
                    rewards.append("⏱️ Редуктор")
                elif r == 'energy':
                    amt = random.randint(3, 5)
                    add_item_to_inventory(user, 'энергетик', amt)
                    rewards.append(f"⚡ Энергетик x{amt}")
                elif r == 'pet':
                    if not pet_added and random.random() < 0.02:
                        pets = ['овчарка', 'волк', 'рысь', 'пума', 'попугай', 'кайот']
                        pet = random.choice(pets)
                        user.pet = pet
                        pet_names = {
                            'овчарка': '🐕 Овчарка', 'волк': '🐺 Волк',
                            'рысь': '🐈 Рысь', 'пума': '🐆 Пума',
                            'попугай': '🦜 Попугай', 'кайот': '🐕 Кайот'
                        }
                        rewards.append(f"🐾 {pet_names.get(pet, pet)}")
                        pet_added = True
                elif r == 'harpoon':
                    add_item_to_inventory(user, 'гарпун', 1)
                    rewards.append("🎣 Гарпун")
                elif r == 'chest_mythic':
                    user.chest_mythic += 1
                    rewards.append("🟡 Мифический сундук")
            name = "🟠 Легендарный сундук"
        else:
            await update.message.reply_text("❌ Тип: common, rare, epic, mythic, legendary")
            return
        
        session.commit()
        
        if rc_gain > 0 or rf_gain > 0:
            safe_log_user_action(
                log_user_id, log_username, 'chest_open',
                amount_rc=rc_gain, amount_rf=rf_gain, item=chest_type
            )
        
        text = f"🎁 *{name} открыт!*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n📦 *Находки:*\n" + "\n".join(f"• {r}" for r in rewards)
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in chest_open: {e}")
        session.rollback()
        await update.message.reply_text("❌ Ошибка")
    finally:
        session.close()


async def chest_open_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Открыть все сундуки подряд, получая все предметы"""
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=update.effective_user.id).first()
        if not user:
            await update.message.reply_text("❌ /start")
            return

        total_common = user.chest_common
        total_rare = user.chest_rare
        total_epic = user.chest_epic
        total_mythic = user.chest_mythic
        total_legendary = user.chest_legendary

        if total_common == 0 and total_rare == 0 and total_epic == 0 and total_mythic == 0 and total_legendary == 0:
            await update.message.reply_text("🎁 *У вас нет сундуков!*", parse_mode='Markdown')
            return

        await update.message.reply_text(
            f"🎁 *Начинаю открывать сундуки...*\n\n"
            f"🟢 Обычных: {total_common}\n"
            f"🔵 Редких: {total_rare}\n"
            f"🟣 Эпических: {total_epic}\n"
            f"🟡 Мифических: {total_mythic}\n"
            f"🟠 Легендарных: {total_legendary}\n\n"
            f"⏳ Подождите, идёт открытие...",
            parse_mode='Markdown'
        )

        total_rc = 0
        total_rf = 0
        items_gained = {}
        pet_gained = None
        log_user_id = user.user_id
        log_username = user.username

        def add_item(item_name, count=1):
            if item_name in items_gained:
                items_gained[item_name] += count
            else:
                items_gained[item_name] = count

        # 1. Обычные сундуки
        for _ in range(user.chest_common):
            items = ['rc', 'rf', 'medkit']
            random.shuffle(items)
            selected = items[:2]
            for r in selected:
                if r == 'rc':
                    amt = random.randint(100, 500)
                    total_rc += amt
                    user.radcoins += amt
                elif r == 'rf':
                    amt = random.randint(2, 10)
                    total_rf += amt
                    user.radfragments += amt
                elif r == 'medkit':
                    add_item('💊 Аптечка')
                    add_item_to_inventory(user, 'аптечка', 1)
            user.chest_common -= 1

        # 2. Редкие сундуки
        for _ in range(user.chest_rare):
            items = ['rc', 'rf', 'harpoon', 'armor1', 'medkit', 'energy']
            random.shuffle(items)
            selected = items[:3]
            for r in selected:
                if r == 'rc':
                    amt = random.randint(500, 1500)
                    total_rc += amt
                    user.radcoins += amt
                elif r == 'rf':
                    amt = random.randint(10, 50)
                    total_rf += amt
                    user.radfragments += amt
                elif r == 'harpoon':
                    add_item('🎣 Гарпун')
                    add_item_to_inventory(user, 'гарпун', 1)
                elif r == 'armor1':
                    add_item('🥉 Лёгкая броня')
                    add_item_to_inventory(user, 'броня1', 1)
                elif r == 'medkit':
                    amt = random.randint(1, 3)
                    add_item(f'💊 Аптечка x{amt}')
                    add_item_to_inventory(user, 'аптечка', amt)
                elif r == 'energy':
                    add_item('⚡ Энергетик')
                    add_item_to_inventory(user, 'энергетик', 1)
            user.chest_rare -= 1

        # 3. Эпические сундуки
        for _ in range(user.chest_epic):
            items = ['rc', 'rf', 'armor2', 'harpoon', 'medkit', 'energy', 'reducer', 'chest_common']
            random.shuffle(items)
            selected = items[:4]
            for r in selected:
                if r == 'rc':
                    amt = random.randint(1000, 3000)
                    total_rc += amt
                    user.radcoins += amt
                elif r == 'rf':
                    amt = random.randint(50, 200)
                    total_rf += amt
                    user.radfragments += amt
                elif r == 'armor2':
                    add_item('🥈 Утяжеленная броня')
                    add_item_to_inventory(user, 'броня2', 1)
                elif r == 'harpoon':
                    add_item('🎣 Гарпун')
                    add_item_to_inventory(user, 'гарпун', 1)
                elif r == 'medkit':
                    amt = random.randint(1, 3)
                    add_item(f'💊 Аптечка x{amt}')
                    add_item_to_inventory(user, 'аптечка', amt)
                elif r == 'energy':
                    add_item('⚡ Энергетик')
                    add_item_to_inventory(user, 'энергетик', 1)
                elif r == 'reducer':
                    add_item('⏱️ Редуктор')
                    add_item_to_inventory(user, 'редуктор', 1)
                elif r == 'chest_common':
                    add_item('🟢 Обычный сундук')
                    user.chest_common += 1
            user.chest_epic -= 1

        # 4. Мифические сундуки
        for _ in range(user.chest_mythic):
            items = ['rc', 'rf', 'armor3', 'rifle', 'harpoon', 'medkit', 'reducer', 'energy', 'pet', 'chest_epic']
            random.shuffle(items)
            selected = items[:4]
            pet_added_this = False
            for r in selected:
                if r == 'rc':
                    amt = random.randint(2500, 6000)
                    total_rc += amt
                    user.radcoins += amt
                elif r == 'rf':
                    amt = random.randint(150, 500)
                    total_rf += amt
                    user.radfragments += amt
                elif r == 'armor3':
                    add_item('🥉 Тактическая броня')
                    add_item_to_inventory(user, 'броня3', 1)
                elif r == 'rifle':
                    add_item('🔫 Винтовка')
                    add_item_to_inventory(user, 'винтовка', 1)
                elif r == 'harpoon':
                    add_item('🎣 Гарпун')
                    add_item_to_inventory(user, 'гарпун', 1)
                elif r == 'medkit':
                    amt = random.randint(2, 5)
                    add_item(f'💊 Аптечка x{amt}')
                    add_item_to_inventory(user, 'аптечка', amt)
                elif r == 'reducer':
                    add_item('⏱️ Редуктор')
                    add_item_to_inventory(user, 'редуктор', 1)
                elif r == 'energy':
                    amt = random.randint(2, 3)
                    add_item(f'⚡ Энергетик x{amt}')
                    add_item_to_inventory(user, 'энергетик', amt)
                elif r == 'pet':
                    if not pet_added_this and not pet_gained and random.random() < 0.005:
                        pets = ['овчарка', 'волк', 'рысь', 'пума', 'попугай', 'кайот']
                        pet_gained = random.choice(pets)
                        user.pet = pet_gained
                        pet_names = {
                            'овчарка': '🐕 Овчарка', 'волк': '🐺 Волк',
                            'рысь': '🐈 Рысь', 'пума': '🐆 Пума',
                            'попугай': '🦜 Попугай', 'кайот': '🐕 Кайот'
                        }
                        add_item(f'🐾 {pet_names.get(pet_gained, pet_gained)}')
                        pet_added_this = True
                elif r == 'chest_epic':
                    add_item('🟣 Эпический сундук')
                    user.chest_epic += 1
            user.chest_mythic -= 1

        # 5. Легендарные сундуки
        for _ in range(user.chest_legendary):
            items = ['rc', 'rf', 'armor5', 'gauss', 'medkit', 'reducer', 'energy', 'pet', 'harpoon', 'chest_mythic']
            random.shuffle(items)
            selected = items[:5]
            pet_added_this = False
            for r in selected:
                if r == 'rc':
                    amt = random.randint(5000, 15000)
                    total_rc += amt
                    user.radcoins += amt
                elif r == 'rf':
                    amt = random.randint(500, 1500)
                    total_rf += amt
                    user.radfragments += amt
                elif r == 'armor5':
                    add_item('🥇 Силовая броня')
                    add_item_to_inventory(user, 'броня5', 1)
                elif r == 'gauss':
                    add_item('⚡ Винтовка Гаусса')
                    add_item_to_inventory(user, 'гаусс', 1)
                elif r == 'medkit':
                    amt = random.randint(2, 5)
                    add_item(f'💊 Аптечка x{amt}')
                    add_item_to_inventory(user, 'аптечка', amt)
                elif r == 'reducer':
                    add_item('⏱️ Редуктор')
                    add_item_to_inventory(user, 'редуктор', 1)
                elif r == 'energy':
                    amt = random.randint(3, 5)
                    add_item(f'⚡ Энергетик x{amt}')
                    add_item_to_inventory(user, 'энергетик', amt)
                elif r == 'pet':
                    if not pet_added_this and not pet_gained and random.random() < 0.02:
                        pets = ['овчарка', 'волк', 'рысь', 'пума', 'попугай', 'кайот']
                        pet_gained = random.choice(pets)
                        user.pet = pet_gained
                        pet_names = {
                            'овчарка': '🐕 Овчарка', 'волк': '🐺 Волк',
                            'рысь': '🐈 Рысь', 'пума': '🐆 Пума',
                            'попугай': '🦜 Попугай', 'кайот': '🐕 Кайот'
                        }
                        add_item(f'🐾 {pet_names.get(pet_gained, pet_gained)}')
                        pet_added_this = True
                elif r == 'harpoon':
                    add_item('🎣 Гарпун')
                    add_item_to_inventory(user, 'гарпун', 1)
                elif r == 'chest_mythic':
                    add_item('🟡 Мифический сундук')
                    user.chest_mythic += 1
            user.chest_legendary -= 1

        session.commit()

        safe_log_user_action(
            log_user_id, log_username, 'chest_open_all',
            amount_rc=total_rc, amount_rf=total_rf,
            item=f"common:{total_common}, rare:{total_rare}, epic:{total_epic}, mythic:{total_mythic}, legendary:{total_legendary}"
        )

        result_text = f"🎁 *Результат открытия сундуков*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        result_text += f"💰 *Получено:*\n"
        result_text += f"☢️ +{total_rc} RC\n"
        result_text += f"☣️ +{total_rf} RF\n\n"

        if items_gained:
            result_text += f"📦 *Предметы:*\n"
            for item, count in items_gained.items():
                result_text += f"• {item} x{count}\n"

        if pet_gained:
            pet_names = {
                'овчарка': '🐕 Овчарка', 'волк': '🐺 Волк',
                'рысь': '🐈 Рысь', 'пума': '🐆 Пума',
                'попугай': '🦜 Попугай', 'кайот': '🐕 Кайот'
            }
            result_text += f"\n🐾 *Новый питомец:* {pet_names.get(pet_gained, pet_gained)}!\n"

        await update.message.reply_text(result_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in chest_open_all: {e}")
        session.rollback()
        await update.message.reply_text("❌ Ошибка при открытии сундуков")
    finally:
        session.close()
