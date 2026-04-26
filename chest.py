# chest.py - Сундуки и фабрики
# Версия: 2.0.0

import random
import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from config import logger, FACTORIES
from core import send_to_private, is_admin
from database import Session, User
from utils import add_item_to_inventory, get_item_count, remove_item_from_inventory, log_user_action

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
        Session.remove()

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
        
        # Логирование открытия сундука
        if rc_gain > 0 or rf_gain > 0:
            log_user_action(
                user_id=log_user_id,
                username=log_username,
                action='chest_open',
                amount_rc=rc_gain,
                amount_rf=rf_gain,
                item=chest_type
            )
        
        text = f"🎁 *{name} открыт!*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n📦 *Находки:*\n" + "\n".join(f"• {r}" for r in rewards)
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in chest_open: {e}")
        session.rollback()
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def chest_open_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Открыть все сундуки подряд"""
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
            f"🎁 *Открываю сундуки...*\n\n"
            f"🟢 Обычных: {total_common}\n"
            f"🔵 Редких: {total_rare}\n"
            f"🟣 Эпических: {total_epic}\n"
            f"🟡 Мифических: {total_mythic}\n"
            f"🟠 Легендарных: {total_legendary}\n\n"
            f"⏳ Подождите...",
            parse_mode='Markdown'
        )
        
        total_rc = 0
        total_rf = 0
        items_gained = {}
        pet_gained = None
        log_user_id = user.user_id
        log_username = user.username
        
        # Открываем все сундуки (упрощённая версия без дублирования кода)
        for _ in range(user.chest_common):
            amt_rc = random.randint(100, 500)
            amt_rf = random.randint(2, 10)
            total_rc += amt_rc
            total_rf += amt_rf
            user.chest_common -= 1
        
        for _ in range(user.chest_rare):
            amt_rc = random.randint(500, 1500)
            amt_rf = random.randint(10, 50)
            total_rc += amt_rc
            total_rf += amt_rf
            if random.random() < 0.3:
                add_item_to_inventory(user, 'гарпун', 1)
                items_gained['🎣 Гарпун'] = items_gained.get('🎣 Гарпун', 0) + 1
            if random.random() < 0.3:
                add_item_to_inventory(user, 'броня1', 1)
                items_gained['🥉 Лёгкая броня'] = items_gained.get('🥉 Лёгкая броня', 0) + 1
            user.chest_rare -= 1
        
        for _ in range(user.chest_epic):
            amt_rc = random.randint(1000, 3000)
            amt_rf = random.randint(50, 200)
            total_rc += amt_rc
            total_rf += amt_rf
            if random.random() < 0.4:
                add_item_to_inventory(user, 'броня2', 1)
                items_gained['🥈 Утяжеленная броня'] = items_gained.get('🥈 Утяжеленная броня', 0) + 1
            if random.random() < 0.3:
                add_item_to_inventory(user, 'редуктор', 1)
                items_gained['⏱️ Редуктор'] = items_gained.get('⏱️ Редуктор', 0) + 1
            user.chest_epic -= 1
        
        for _ in range(user.chest_mythic):
            amt_rc = random.randint(2500, 6000)
            amt_rf = random.randint(150, 500)
            total_rc += amt_rc
            total_rf += amt_rf
            if random.random() < 0.4:
                add_item_to_inventory(user, 'броня3', 1)
                items_gained['🥉 Тактическая броня'] = items_gained.get('🥉 Тактическая броня', 0) + 1
            if random.random() < 0.3:
                add_item_to_inventory(user, 'винтовка', 1)
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

        # Вспомогательная функция для добавления предметов
        def add_item(item_name, count=1):
            if item_name in items_gained:
                items_gained[item_name] += count
            else:
                items_gained[item_name] = count

        # ------------------------------------------------------------------
        # 1. Обычные сундуки
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # 2. Редкие сундуки
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # 3. Эпические сундуки
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # 4. Мифические сундуки
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # 5. Легендарные сундуки
        # ------------------------------------------------------------------
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

        # Сохраняем изменения
        session.commit()

        # Логирование
        log_user_action(
            user_id=log_user_id,
            username=log_username,
            action='chest_open_all',
            amount_rc=total_rc,
            amount_rf=total_rf,
            item=f"common:{total_common}, rare:{total_rare}, epic:{total_epic}, mythic:{total_mythic}, legendary:{total_legendary}"
        )

        # Формируем результат
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
        Session.remove()


# ==================== ФАБРИКИ (РЕСУРСНЫЕ ТОЧКИ) ====================

async def factory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление фабриками"""
    if not context.args:
        text = "🏭 *Ресурсные точки*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for key, f in FACTORIES.items():
            text += f"{f['name']}\n"
            text += f"   • Мест: {f['slots']}\n"
            text += f"   • Цена: {f['price']} RC (3 суток)\n"
            text += f"   • Доход: {f['income']} {f['income_type']}/час\n"
            if f['level'] > 1:
                text += f"   • Требуется: {f['level']} уровень\n"
            text += "\n"
        text += "📝 Команды:\n"
        text += "/factory list — список точек\n"
        text += "/factory buy [название] — купить точку\n"
        text += "/factory money — забрать доход\n"
        text += "/factory my — мои точки\n"
        text += "/factory leave [название] — освободить точку"
        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    action = context.args[0].lower()
    
    if action == 'list':
        await factory_list(update, context)
    elif action == 'buy':
        if len(context.args) < 2:
            await update.message.reply_text("❌ /factory buy [название]")
            return
        await factory_buy(update, context, ' '.join(context.args[1:]).lower())
    elif action == 'money':
        await factory_money(update, context)
    elif action == 'my':
        await factory_my(update, context)
    elif action == 'leave':
        if len(context.args) < 2:
            await update.message.reply_text("❌ /factory leave [название]")
            return
        await factory_leave(update, context, ' '.join(context.args[1:]).lower())
    else:
        await update.message.reply_text("❌ Используйте: list, buy, money, my, leave")

async def factory_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список точек со свободными местами"""
    session = Session()
    try:
        users = session.query(User).all()
        occupied = {}
        for user in users:
            if user.factories and user.factories != '[]':
                factories = json.loads(user.factories)
                for f in factories:
                    name = f.get('name')
                    if name:
                        occupied[name] = occupied.get(name, 0) + 1
        
        text = "🏭 *Доступные точки*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for key, f in FACTORIES.items():
            free = f['slots'] - occupied.get(key, 0)
            text += f"{f['name']}\n"
            text += f"   • Свободно: {free}/{f['slots']}\n"
            text += f"   • Цена: {f['price']} RC (3 суток)\n"
            text += f"   • Доход: {f['income']} {f['income_type']}/час\n"
            if f['level'] > 1:
                text += f"   • Требуется: {f['level']} уровень\n"
            text += "\n"
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in factory_list: {e}")
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def factory_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, factory_name: str):
    """Купить/арендовать точку"""
    if factory_name not in FACTORIES:
        await update.message.reply_text("❌ Неизвестная точка. Используйте: свалка, мастерская, станция, дамба, химка, комплекс, реактор")
        return
    
    factory = FACTORIES[factory_name]
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=update.effective_user.id).first()
        if not user:
            await update.message.reply_text("❌ /start")
            return
        
        if user.level < factory['level']:
            await update.message.reply_text(f"❌ Нужен {factory['level']} уровень! У вас {user.level}")
            return
        
        if user.radcoins < factory['price']:
            await update.message.reply_text(f"❌ Нужно {factory['price']} RC, у вас {user.radcoins:.0f}")
            return
        
        # Проверяем свободные места
        users = session.query(User).all()
        occupied = 0
        for u in users:
            if u.factories and u.factories != '[]':
                facs = json.loads(u.factories)
                for f in facs:
                    if f.get('name') == factory_name:
                        occupied += 1
        
        if occupied >= factory['slots']:
            await update.message.reply_text(f"❌ Нет свободных мест на {factory['name']}!")
            return
        
        # Проверяем, не арендовал ли уже эту точку
        current = json.loads(user.factories) if user.factories else []
        for f in current:
            if f.get('name') == factory_name:
                await update.message.reply_text(f"❌ Вы уже арендуете {factory['name']}!")
                return
        
        # Покупаем
        user.radcoins -= factory['price']
        current.append({
            'name': factory_name,
            'bought_at': datetime.now().isoformat(),
            'last_collect': datetime.now().isoformat()
        })
        user.factories = json.dumps(current)
        
        log_user_id = user.user_id
        log_username = user.username
        log_price = factory['price']
        
        session.commit()
        
        # Логирование покупки фабрики
        log_user_action(
            user_id=log_user_id,
            username=log_username,
            action='factory_buy',
            amount_rc=-log_price,
            item=factory_name
        )
        
        await update.message.reply_text(
            f"✅ *Арендована {factory['name']}!*\n\n"
            f"💰 Потрачено: {factory['price']} RC\n"
            f"⏰ Срок: 3 суток\n"
            f"📈 Доход: {factory['income']} {factory['income_type']}/час\n\n"
            f"💡 Забирайте доход командой `/factory money`",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in factory_buy: {e}")
        session.rollback()
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def factory_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Забрать накопленный доход (без 36-часового блокиратора)"""
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=update.effective_user.id).first()
        if not user:
            await update.message.reply_text("❌ /start")
            return
        
        if not user.factories or user.factories == '[]':
            await update.message.reply_text("❌ У вас нет арендованных точек")
            return
        
        factories = json.loads(user.factories)
        now = datetime.now()
        total_income = 0
        updated = []
        expired = []
        income_type = 'RC'
        log_user_id = user.user_id
        log_username = user.username
        
        for f in factories:
            name = f.get('name')
            if name not in FACTORIES:
                continue
            
            factory = FACTORIES[name]
            bought_at = datetime.fromisoformat(f['bought_at'])
            last_collect = datetime.fromisoformat(f.get('last_collect', bought_at.isoformat()))
            
            # Проверка срока аренды (3 суток)
            if now - bought_at > timedelta(hours=72):
                expired.append(name)
                continue
            
            # Расчёт дохода (без блокировки 36 часов)
            hours = (now - last_collect).total_seconds() / 3600
            income = int(hours * factory['income'])
            total_income += income
            income_type = factory['income_type']
            
            # Обновляем время последнего сбора
            f['last_collect'] = now.isoformat()
            updated.append(f)
        
        if expired:
            # Удаляем просроченные точки
            for name in expired:
                factories = [f for f in factories if f.get('name') != name]
            await update.message.reply_text(
                f"⚠️ *Точки аннулированы!*\n\n"
                f"❌ {', '.join(expired)} — срок аренды истёк",
                parse_mode='Markdown'
            )
        
        if total_income > 0:
            # Добавляем доход
            for f in updated:
                factory = FACTORIES[f['name']]
                if factory['income_type'] == 'RC':
                    user.radcoins += total_income
                else:
                    user.radfragments += total_income
            
            user.factories = json.dumps(factories)
            session.commit()
            
            # Логирование получения дохода
            if income_type == 'RC':
                log_user_action(
                    user_id=log_user_id,
                    username=log_username,
                    action='factory_money',
                    amount_rc=total_income,
                    item=f"{len(updated)} точек"
                )
            else:
                log_user_action(
                    user_id=log_user_id,
                    username=log_username,
                    action='factory_money',
                    amount_rf=total_income,
                    item=f"{len(updated)} точек"
                )
            
            await update.message.reply_text(
                f"💰 *Доход получен!*\n\n"
                f"📦 Сумма: +{total_income} {income_type}\n"
                f"🏭 Точки: {', '.join([f['name'] for f in factories if f not in expired])}",
                parse_mode='Markdown'
            )
        elif expired:
            user.factories = json.dumps(factories)
            session.commit()
        else:
            await update.message.reply_text("💰 Нет накопленного дохода. Зайдите позже!")
        
    except Exception as e:
        logger.error(f"Error in factory_money: {e}")
        session.rollback()
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def factory_my(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать мои точки"""
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=update.effective_user.id).first()
        if not user:
            await update.message.reply_text("❌ /start")
            return
        
        if not user.factories or user.factories == '[]':
            await update.message.reply_text("🏭 У вас нет арендованных точек", parse_mode='Markdown')
            return
        
        factories = json.loads(user.factories)
        now = datetime.now()
        text = "🏭 *Мои точки*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for f in factories:
            name = f.get('name')
            if name not in FACTORIES:
                continue
            
            factory = FACTORIES[name]
            bought_at = datetime.fromisoformat(f['bought_at'])
            
            expires_in = (bought_at + timedelta(hours=72)) - now
            hours_left = expires_in.seconds // 3600
            minutes_left = (expires_in.seconds % 3600) // 60
            
            text += f"{factory['name']}\n"
            text += f"   • Доход: {factory['income']} {factory['income_type']}/час\n"
            text += f"   • Срок: {hours_left}ч {minutes_left}мин\n"
            text += f"   • Накоплено: зайдите за доходом!\n\n"
        
        text += "💡 `/factory money` — забрать доход"
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in factory_my: {e}")
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def factory_leave(update: Update, context: ContextTypes.DEFAULT_TYPE, factory_name: str):
    """Освободить точку"""
    if factory_name not in FACTORIES:
        await update.message.reply_text("❌ Неизвестная точка")
        return
    
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=update.effective_user.id).first()
        if not user:
            await update.message.reply_text("❌ /start")
            return
        
        if not user.factories or user.factories == '[]':
            await update.message.reply_text("❌ У вас нет арендованных точек")
            return
        
        factories = json.loads(user.factories)
        new_factories = [f for f in factories if f.get('name') != factory_name]
        
        if len(new_factories) == len(factories):
            await update.message.reply_text(f"❌ У вас нет точки {factory_name}")
            return
        
        user.factories = json.dumps(new_factories)
        
        log_user_id = user.user_id
        log_username = user.username
        
        session.commit()
        
        # Логирование освобождения точки
        log_user_action(
            user_id=log_user_id,
            username=log_username,
            action='factory_leave',
            item=factory_name
        )
        
        await update.message.reply_text(
            f"✅ *Точка {FACTORIES[factory_name]['name']} освобождена*",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in factory_leave: {e}")
        session.rollback()
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()


# ==================== АДМИН-КОМАНДЫ ФАБРИК ====================

async def afactory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ-команды для управления фабриками"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Нет прав!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "👑 *Админ-панель фабрик*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "/afactory list — список всех точек\n"
            "/afactory list [название] — игроки на точке\n"
            "/afactory remove @ник [точка] — убрать игрока\n"
            "/afactory add @ник [точка] — добавить игрока\n"
            "/afactory ban @ник [точка] — заблокировать\n"
            "/afactory unban @ник [точка] — разблокировать\n"
            "/afactory clean [точка] — очистить точку",
            parse_mode='Markdown'
        )
        return
    
    action = context.args[0].lower()
    
    if action == 'list':
        if len(context.args) > 1:
            await afactory_list_point(update, context, context.args[1].lower())
        else:
            await afactory_list_all(update, context)
    elif action == 'remove':
        if len(context.args) < 3:
            await update.message.reply_text("❌ /afactory remove @ник [точка]")
            return
        await afactory_remove(update, context, context.args[1].lstrip('@'), context.args[2].lower())
    elif action == 'add':
        if len(context.args) < 3:
            await update.message.reply_text("❌ /afactory add @ник [точка]")
            return
        await afactory_add(update, context, context.args[1].lstrip('@'), context.args[2].lower())
    elif action == 'ban':
        if len(context.args) < 3:
            await update.message.reply_text("❌ /afactory ban @ник [точка]")
            return
        await afactory_ban(update, context, context.args[1].lstrip('@'), context.args[2].lower())
    elif action == 'unban':
        if len(context.args) < 3:
            await update.message.reply_text("❌ /afactory unban @ник [точка]")
            return
        await afactory_unban(update, context, context.args[1].lstrip('@'), context.args[2].lower())
    elif action == 'clean':
        if len(context.args) < 2:
            await update.message.reply_text("❌ /afactory clean [точка]")
            return
        await afactory_clean(update, context, context.args[1].lower())
    else:
        await update.message.reply_text("❌ Неизвестная команда")

async def afactory_list_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список всех точек с занятостью"""
    session = Session()
    try:
        users = session.query(User).all()
        occupied = {}
        banned = {}
        
        for user in users:
            if user.factories and user.factories != '[]':
                factories = json.loads(user.factories)
                for f in factories:
                    name = f.get('name')
                    if name:
                        occupied[name] = occupied.get(name, 0) + 1
            if user.factory_bans and user.factory_bans != '[]':
                bans = json.loads(user.factory_bans)
                for name in bans:
                    banned[name] = banned.get(name, 0) + 1
        
        text = "👑 *Список фабрик*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for key, f in FACTORIES.items():
            free = f['slots'] - occupied.get(key, 0)
            banned_count = banned.get(key, 0)
            text += f"🏭 *{f['name']}*\n"
            text += f"   • Свободно: {free}/{f['slots']}\n"
            text += f"   • Забанено: {banned_count}\n"
            text += "\n"
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in afactory_list_all: {e}")
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def afactory_list_point(update: Update, context: ContextTypes.DEFAULT_TYPE, point_name: str):
    """Список игроков на конкретной точке"""
    if point_name not in FACTORIES:
        await update.message.reply_text("❌ Неизвестная точка. Доступны: свалка, мастерская, станция, дамба, химка, комплекс, реактор")
        return
    
    session = Session()
    try:
        users = session.query(User).all()
        players = []
        banned_players = []
        
        for user in users:
            if user.factories and user.factories != '[]':
                factories = json.loads(user.factories)
                for f in factories:
                    if f.get('name') == point_name:
                        players.append(user)
                        break
            if user.factory_bans and user.factory_bans != '[]':
                bans = json.loads(user.factory_bans)
                if point_name in bans:
                    banned_players.append(user)
        
        text = f"👑 *{FACTORIES[point_name]['name']}*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        text += f"📊 *Всего мест:* {FACTORIES[point_name]['slots']}\n"
        text += f"🔓 *Свободно:* {FACTORIES[point_name]['slots'] - len(players)}\n"
        text += f"👥 *Активных:* {len(players)}\n"
        text += f"🔴 *Забанено:* {len(banned_players)}\n\n"
        
        if players:
            text += "*✅ Активные игроки:*\n"
            for i, p in enumerate(players, 1):
                text += f"{i}. @{p.username or f'ID:{p.user_id}'}\n"
        
        if banned_players:
            text += "\n*❌ Забаненные:*\n"
            for i, p in enumerate(banned_players, 1):
                text += f"{i}. @{p.username or f'ID:{p.user_id}'}\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in afactory_list_point: {e}")
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def afactory_remove(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str, point_name: str):
    """Убрать игрока с точки"""
    if point_name not in FACTORIES:
        await update.message.reply_text("❌ Неизвестная точка")
        return
    
    session = Session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if not user:
            await update.message.reply_text(f"❌ @{username} не найден")
            return
        
        if not user.factories or user.factories == '[]':
            await update.message.reply_text(f"❌ У @{username} нет арендованных точек")
            return
        
        factories = json.loads(user.factories)
        new_factories = [f for f in factories if f.get('name') != point_name]
        
        if len(new_factories) == len(factories):
            await update.message.reply_text(f"❌ У @{username} нет точки {point_name}")
            return
        
        user.factories = json.dumps(new_factories)
        session.commit()
        
        log_user_action(
            user_id=user.user_id,
            username=user.username,
            action='factory_admin_remove',
            item=f"{point_name} (админ)"
        )
        
        await update.message.reply_text(
            f"✅ *@{username} убран с точки {FACTORIES[point_name]['name']}*",
            parse_mode='Markdown'
        )
        
        try:
            await context.bot.send_message(
                user.user_id,
                f"👑 *Администратор убрал вас с точки {FACTORIES[point_name]['name']}!*"
            )
        except:
            pass
    except Exception as e:
        logger.error(f"Error in afactory_remove: {e}")
        session.rollback()
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def afactory_add(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str, point_name: str):
    """Добавить игрока на точку (бесплатно)"""
    if point_name not in FACTORIES:
        await update.message.reply_text("❌ Неизвестная точка")
        return
    
    session = Session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if not user:
            await update.message.reply_text(f"❌ @{username} не найден")
            return
        
        bans = json.loads(user.factory_bans) if user.factory_bans else []
        if point_name in bans:
            await update.message.reply_text(f"❌ @{username} забанен на точке {point_name}")
            return
        
        current = json.loads(user.factories) if user.factories else []
        
        for f in current:
            if f.get('name') == point_name:
                await update.message.reply_text(f"❌ @{username} уже арендует точку {point_name}")
                return
        
        current.append({
            'name': point_name,
            'bought_at': datetime.now().isoformat(),
            'last_collect': datetime.now().isoformat()
        })
        user.factories = json.dumps(current)
        session.commit()
        
        log_user_action(
            user_id=user.user_id,
            username=user.username,
            action='factory_admin_add',
            item=f"{point_name} (админ)"
        )
        
        await update.message.reply_text(
            f"✅ *@{username} добавлен на точку {FACTORIES[point_name]['name']}!*",
            parse_mode='Markdown'
        )
        
        try:
            await context.bot.send_message(
                user.user_id,
                f"👑 *Администратор добавил вас на точку {FACTORIES[point_name]['name']}!*\n\n"
                f"💰 Доход: {FACTORIES[point_name]['income']} {FACTORIES[point_name]['income_type']}/час\n"
                f"📝 Забирайте доход командой `/factory money`",
                parse_mode='Markdown'
            )
        except:
            pass
    except Exception as e:
        logger.error(f"Error in afactory_add: {e}")
        session.rollback()
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def afactory_ban(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str, point_name: str):
    """Забанить игрока на точке"""
    if point_name not in FACTORIES:
        await update.message.reply_text("❌ Неизвестная точка")
        return
    
    session = Session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if not user:
            await update.message.reply_text(f"❌ @{username} не найден")
            return
        
        bans = json.loads(user.factory_bans) if user.factory_bans else []
        if point_name in bans:
            await update.message.reply_text(f"❌ @{username} уже забанен на точке {point_name}")
            return
        
        bans.append(point_name)
        user.factory_bans = json.dumps(bans)
        
        if user.factories and user.factories != '[]':
            factories = json.loads(user.factories)
            new_factories = [f for f in factories if f.get('name') != point_name]
            user.factories = json.dumps(new_factories)
        
        session.commit()
        
        log_user_action(
            user_id=user.user_id,
            username=user.username,
            action='factory_admin_ban',
            item=point_name
        )
        
        await update.message.reply_text(
            f"✅ *@{username} забанен на точке {FACTORIES[point_name]['name']}*",
            parse_mode='Markdown'
        )
        
        try:
            await context.bot.send_message(
                user.user_id,
                f"🔴 *Вас забанили на точке {FACTORIES[point_name]['name']}!*"
            )
        except:
            pass
    except Exception as e:
        logger.error(f"Error in afactory_ban: {e}")
        session.rollback()
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def afactory_unban(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str, point_name: str):
    """Разбанить игрока на точке"""
    if point_name not in FACTORIES:
        await update.message.reply_text("❌ Неизвестная точка")
        return
    
    session = Session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if not user:
            await update.message.reply_text(f"❌ @{username} не найден")
            return
        
        bans = json.loads(user.factory_bans) if user.factory_bans else []
        if point_name not in bans:
            await update.message.reply_text(f"❌ @{username} не забанен на точке {point_name}")
            return
        
        bans.remove(point_name)
        user.factory_bans = json.dumps(bans)
        session.commit()
        
        log_user_action(
            user_id=user.user_id,
            username=user.username,
            action='factory_admin_unban',
            item=point_name
        )
        
        await update.message.reply_text(
            f"✅ *@{username} разбанен на точке {FACTORIES[point_name]['name']}*",
            parse_mode='Markdown'
        )
        
        try:
            await context.bot.send_message(
                user.user_id,
                f"🟢 *Вас разбанили на точке {FACTORIES[point_name]['name']}!*"
            )
        except:
            pass
    except Exception as e:
        logger.error(f"Error in afactory_unban: {e}")
        session.rollback()
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def afactory_clean(update: Update, context: ContextTypes.DEFAULT_TYPE, point_name: str):
    """Очистить точку — удалить всех игроков"""
    if point_name not in FACTORIES:
        await update.message.reply_text("❌ Неизвестная точка")
        return
    
    session = Session()
    try:
        users = session.query(User).all()
        removed = 0
        
        for user in users:
            if user.factories and user.factories != '[]':
                factories = json.loads(user.factories)
                new_factories = [f for f in factories if f.get('name') != point_name]
                if len(new_factories) != len(factories):
                    user.factories = json.dumps(new_factories)
                    removed += 1
        
        session.commit()
        
        await update.message.reply_text(
            f"✅ *Точка {FACTORIES[point_name]['name']} очищена!*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 Удалено игроков: {removed}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in afactory_clean: {e}")
        session.rollback()
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()
