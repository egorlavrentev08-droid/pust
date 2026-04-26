# utils.py - Утилиты и механики
# Версия: 2.0.0
# Больше никаких сессий внутри! Только логика и расчёты.

import json
import random
from datetime import datetime, timedelta

# Импортируем из конфига
from config import logger, MAX_MEDKITS, MAX_LEVEL
# Для логов нам всё ещё нужна сессия, это исключение
from database import Session, User, UserLog


# ==================== ИНВЕНТАРЬ ====================

def get_inventory(user):
    return json.loads(user.inventory) if user.inventory else []

def save_inventory(user, inventory):
    user.inventory = json.dumps(inventory)

def get_equipped(user):
    return json.loads(user.equipped) if user.equipped else {}

def save_equipped(user, equipped):
    user.equipped = json.dumps(equipped)

def add_item_to_inventory(user, item_name, count=1, expires=None):
    inventory = get_inventory(user)
    for i in inventory:
        if i['item'] == item_name:
            i['count'] += count
            if expires and 'expires' not in i:
                i['expires'] = expires.isoformat() if expires else None
            save_inventory(user, inventory)
            return
    new_item = {'item': item_name, 'count': count}
    if expires:
        new_item['expires'] = expires.isoformat()
    inventory.append(new_item)
    save_inventory(user, inventory)

def remove_item_from_inventory(user, item_name, count=1):
    inventory = get_inventory(user)
    for i in inventory:
        if i['item'] == item_name:
            i['count'] -= count
            if i['count'] <= 0:
                inventory.remove(i)
            save_inventory(user, inventory)
            return True
    return False

def get_item_count(user, item_name):
    inventory = get_inventory(user)
    for i in inventory:
        if i['item'] == item_name:
            return i['count']
    return 0


# ==================== БОНУСЫ КЛАССОВ ====================

def apply_class_bonus(user, rc_gain, fragment_gain, exp_gain):
    class_name = getattr(user, 'user_class', 'stalker')
    if class_name == 'military':
        return int(rc_gain * 1.2), int(fragment_gain * 0.7), int(exp_gain * 1.3)
    elif class_name == 'bandit':
        return int(rc_gain * 1.15), int(fragment_gain * 1.4), int(exp_gain * 0.75)
    elif class_name == 'scientist':
        return int(rc_gain * 0.8), int(fragment_gain * 1.25), int(exp_gain * 1.5)
    return rc_gain, fragment_gain, exp_gain


# ==================== ВЫЖИВАЕМОСТЬ ====================

def calculate_survive_chance(user, target_level):
    armor_map = {'броня1': 'light', 'броня2': 'heavy', 'броня3': 'tactical',
                 'броня4': 'reinforced', 'броня5': 'power'}
    armor_bonus = {'light': 25, 'heavy': 40, 'tactical': 50, 'reinforced': 60, 'power': 75}
    base = 10
    equipped = get_equipped(user)
    armor = equipped.get('armor')
    if armor and armor in armor_map:
        base = armor_bonus.get(armor_map[armor], 10)
    if target_level == 3:
        base = min(100, base + 25)
    if get_item_count(user, 'аптечка') > 0:
        base = min(100, base + 25)
    return base


# ==================== ДОСТИЖЕНИЯ (БЕЗ СЕССИИ И КОММИТА!) ====================

def check_achievements(user):  # <-- СЕССИЯ БОЛЬШЕ НЕ НУЖНА!
    """Проверяет достижения и ВОЗВРАЩАЕТ СПИСОК НОВЫХ. НИЧЕГО НЕ СОХРАНЯЕТ."""
    achievements = json.loads(user.achievements) if user.achievements else []
    new_achievements = []

    if user.total_collects >= 10 and 'добытчик' not in achievements:
        new_achievements.append('добытчик')
    if user.level >= 10 and 'кандидат' not in achievements:
        new_achievements.append('кандидат')
    if user.level >= 50 and 'мастер' not in achievements:
        new_achievements.append('мастер')
    if user.level >= MAX_LEVEL and 'легенда' not in achievements:
        new_achievements.append('легенда')
    if user.daily_streak >= 7 and 'терпила' not in achievements:
        new_achievements.append('терпила')
    if user.daily_streak >= 30 and 'старатель' not in achievements:
        new_achievements.append('старатель')
    if user.total_purchases >= 10 and 'постоянный_клиент' not in achievements:
        new_achievements.append('постоянный_клиент')
    if user.radcoins >= 100000 and 'миллионер' not in achievements:
        new_achievements.append('миллионер')

    return new_achievements


# ==================== ОПЫТ ДЛЯ УРОВНЯ ====================

def get_exp_for_level(level):
    if level <= 1:
        return 0
    level = min(level, MAX_LEVEL)
    return sum(100 + (i - 2) * 50 for i in range(2, level + 1))


def get_user_by_username(session, username):
    """Найти пользователя по username (без учёта регистра)"""
    from sqlalchemy import func
    return session.query(User).filter(func.lower(User.username) == username.lower()).first()


# ==================== ЛОГИРОВАНИЕ ====================

def log_user_action(user_id, username, action, amount_rc=0, amount_rf=0, amount_crystals=0, item=None):
    """Запись действия пользователя в лог (ЭТО ИСКЛЮЧЕНИЕ, ТУТ СЕССИЯ НУЖНА)"""
    session = Session()
    try:
        log = UserLog(
            user_id=user_id, username=username, action=action,
            amount_rc=amount_rc, amount_rf=amount_rf,
            amount_crystals=amount_crystals, item=item,
            timestamp=datetime.now()
        )
        session.add(log)
        session.commit()
    except Exception as e:
        print(f"Error logging user action: {e}")
    finally:
        Session.remove()
