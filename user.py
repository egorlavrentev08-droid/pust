# user.py - Команды пользователя
# Версия: 2.0.0

from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from core import logger, MAX_LEVEL, get_exp_for_level, send_to_private
from database import Session, User, Clan
from utils import get_equipped, get_inventory

# ==================== ПРОФИЛЬ ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Стартовая команда"""
    user = update.effective_user
    session = Session()
    try:
        db_user = session.query(User).filter_by(user_id=user.id).first()
        is_new = False
        if not db_user:
            db_user = User(user_id=user.id, username=user.username)
            session.add(db_user)
            is_new = True
        elif user.username and db_user.username != user.username:
            db_user.username = user.username
        session.commit()
        
        if is_new:
            db_user.radcoins += 1000
            session.commit()
            await update.message.reply_text(
                "🌟 *RadCoin Bot — Пустошь*\n\n"
                "🎁 *Бонус новичка: 1000 RC!*\n\n"
                "💰 /collect — сбор ресурсов\n"
                "🏹 /hunt — охота на мутантов\n"
                "🛒 /shop — магазин\n"
                "📖 /help — справка",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "🌟 *RadCoin Bot — Пустошь*\n\n"
                "💰 /collect — сбор ресурсов\n"
                "🏹 /hunt — охота\n"
                "🛒 /shop — магазин\n"
                "📖 /help — справка",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error in start: {e}")
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка"""
    text = (
        "📖 *RadCoin Bot — Пустошь*\n\n"
        "🎲 */collect* — сбор ресурсов\n"
        "🏹 */hunt* — охота\n"
        "🛒 */shop* — магазин\n"
        "💰 */buy [товар] [кол-во]* — купить\n"
        "📦 */inv* — инвентарь\n"
        "👤 */profile* — профиль\n"
        "📊 */stats* — статистика\n"
        "🏆 */achievements* — достижения\n"
        "🎰 */casino [сумма]* — казино\n"
        "💱 */exchange [количество]* — RF→RC\n"
        "🛠️ */craft [предмет]* — крафт\n"
        "🔔 */announce on/off* — уведомления\n"
        "🗺️ */locate [название]* — сменить локацию\n"
        "🎭 */class [название]* — сменить класс\n"
        "🏆 */top [level/rc/boss/hunt/clan]* — таблица\n\n"
        "🐾 *Питомцы:* /pet accept/deny/bye\n"
        "🏰 *Кланы:* /clan create/join/info/invest/up/list/goodbye\n"
        "🎁 *Сундуки:* /chest list/chance/open\n"
        "📻 *Радио:* /radio [текст], /radion [код]\n"
        "📖 *Советы:* /advice [раздел]"
    )
    await send_to_private(update, context, text)

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Профиль пользователя"""
    user = update.effective_user
    session = Session()
    try:
        db_user = session.query(User).filter_by(user_id=user.id).first()
        if not db_user:
            db_user = User(user_id=user.id, username=user.username)
            session.add(db_user)
            session.commit()
        
        next_exp = get_exp_for_level(min(db_user.level + 1, MAX_LEVEL))
        exp_needed = max(0, next_exp - db_user.experience)
        
        class_names = {
            'stalker': '🟢 Сталкер',
            'military': '🔫 Военный',
            'bandit': '🗡️ Бандит',
            'scientist': '🔬 Учёный'
        }
        class_name = class_names.get(db_user.user_class, '🟢 Сталкер')
        
        equipped = get_equipped(db_user)
        armor_display = {
            'броня1': '🟢 Лёгкая броня (25%)',
            'броня2': '🔵 Утяжеленная броня (40%)',
            'броня3': '🟣 Тактическая броня (50%)',
            'броня4': '🟠 Тяжёлая броня (60%)',
            'броня5': '🔴 Силовая броня (75%)'
        }
        armor_text = ""
        if equipped.get('armor'):
            armor_text = f"\n🛡️ *Броня:* {armor_display.get(equipped['armor'], equipped['armor'])}"
        
        weapon_display = {
            'ружье': '🔫 Ружьё',
            'гарпун': '🎣 Гарпун',
            'винтовка': '🔫 Винтовка',
            'гаусс': '⚡ Винтовка Гаусса'
        }
        weapon_text = ""
        if equipped.get('weapon'):
            weapon_text = f"\n⚔️ *Оружие:* {weapon_display.get(equipped['weapon'], equipped['weapon'])}"
        
        text = (
            f"👤 *{db_user.username}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎭 *Класс:* {class_name}\n"
            f"☢️ *РадКоины:* {db_user.radcoins:.0f}\n"
            f"☣️ *РадФрагменты:* {db_user.radfragments}\n"
            f"⚠️ *Уровень:* {db_user.level}"
        )
        
        if db_user.level < MAX_LEVEL:
            text += f" ({exp_needed} опыта до {db_user.level + 1} уровня)"
        
        text += armor_text
        text += weapon_text
        
        if db_user.pet:
            pet_names = {
                'овчарка': '🐕 Овчарка', 'волк': '🐺 Волк',
                'рысь': '🐈 Рысь', 'пума': '🐆 Пума',
                'попугай': '🦜 Попугай', 'кайот': '🐕 Кайот'
            }
            text += f"\n🐾 *Питомец:* {pet_names.get(db_user.pet, db_user.pet)}"
        
        if db_user.clan_id:
            clan = session.query(Clan).filter_by(id=db_user.clan_id).first()
            if clan:
                text += f"\n🏰 *Клан:* {clan.name}"
        
        await send_to_private(update, context, text)
    except Exception as e:
        logger.error(f"Error in profile: {e}")
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика пользователя"""
    user = update.effective_user
    session = Session()
    try:
        db_user = session.query(User).filter_by(user_id=user.id).first()
        if not db_user:
            await update.message.reply_text("❌ /start")
            return
        text = (
            f"📊 *Статистика {db_user.username}*\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎲 *Сборов:* {db_user.total_collects}\n"
            f"☢️ *Всего RC:* {db_user.total_rc_earned:.0f}\n"
            f"🏆 *Лучший сбор:* {db_user.best_collect:.0f}\n"
            f"🧬 *Мутантов убито:* {db_user.mutants_killed}\n"
            f"👾 *Мутантов 3 ур:* {db_user.mutants_lvl3}\n"
            f"👑 *Боссов:* {db_user.bosses_killed}\n"
            f"💀 *Смертей:* {db_user.deaths}\n"
            f"📈 *Серия сборов:* {db_user.daily_streak} дней"
        )
        await send_to_private(update, context, text)
    except Exception as e:
        logger.error(f"Error in stats: {e}")
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Достижения пользователя"""
    user = update.effective_user
    session = Session()
    try:
        db_user = session.query(User).filter_by(user_id=user.id).first()
        if not db_user:
            await update.message.reply_text("❌ /start")
            return
        current = json.loads(db_user.achievements) if db_user.achievements else []
        text = "🏆 *Достижения*\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        ach_names = ['добытчик', 'инвестор', 'терпила', 'кандидат', 'мастер', 'легенда', 'старатель', 'постоянный_клиент', 'миллионер']
        for ach in ach_names:
            text += f"✅ {ach}\n" if ach in current else f"⬜ {ach}\n"
        await send_to_private(update, context, text)
    except Exception as e:
        logger.error(f"Error in achievements: {e}")
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настройка уведомлений"""
    user_id = update.effective_user.id
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            user = User(user_id=user_id, username=update.effective_user.username)
            session.add(user)
            session.commit()
        if not context.args:
            status = "включены ✅" if user.notifications_enabled else "выключены ❌"
            await update.message.reply_text(f"🔔 *Уведомления*\n\nСейчас уведомления {status}\n\n/announce on — включить\n/announce off — выключить", parse_mode='Markdown')
            return
        if context.args[0].lower() == 'on':
            user.notifications_enabled = True
            session.commit()
            await update.message.reply_text("✅ *Уведомления включены!*", parse_mode='Markdown')
        elif context.args[0].lower() == 'off':
            user.notifications_enabled = False
            session.commit()
            await update.message.reply_text("❌ *Уведомления выключены!*", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ /announce on или off")
    except Exception as e:
        logger.error(f"Error in announce: {e}")
        await update.message.reply_text("❌ Ошибка")
    finally:
        Session.remove()

async def phase_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о фазе Пустоши"""
    phase = context.bot_data.get('phase', 1)
    phases = {
        1: {'name': '🟢 МИРНАЯ', 'desc': 'Нет мутантов, нет охоты', 'bonus': 'Безопасно'},
        2: {'name': '🟡 ОПАСНАЯ', 'desc': 'Мутанты, охота, питомцы', 'bonus': 'Риск 10%'},
        3: {'name': '🔴 АПОКАЛИПТИЧЕСКАЯ', 'desc': 'Аномалии, высокий риск', 'bonus': 'Аномалии 10%'}
    }
    p = phases.get(phase, phases[1])
    text = f"🌍 *Фаза Пустоши: {p['name']}*\n━━━━━━━━━━━━━━━━━━━━━━━━\n📖 {p['desc']}\n\n⚡ {p['bonus']}"
    await send_to_private(update, context, text)
