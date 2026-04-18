import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Инициализация базы
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True) # Telegram ID
    username = Column(String)
    
    # --- Экономика ---
    radcoins = Column(Float, default=0.0)
    radfragments = Column(Integer, default=0)
    radcrystals = Column(Integer, default=0)
    
    # --- Уровни и Опыт ---
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    
    # --- Время и Кулдауны ---
    last_collection = Column(DateTime, nullable=True) # Последний сбор на заводе/работе
    next_collection_time = Column(DateTime, nullable=True)
    last_hunt = Column(DateTime, nullable=True)
    last_collect_date = Column(DateTime, nullable=True) # Для ежедневных наград
    
    # --- Бафы и Состояния ---
    cooldown_reducer_until = Column(DateTime, nullable=True)
    energy_drink_until = Column(DateTime, nullable=True)
    
    # --- Инвентарь и Снаряжение (храним как JSON-строки) ---
    # Изменения: Удалены щит, камуфляж, металлоискатель из логики обработки
    inventory = Column(String, default='[]') 
    equipped = Column(String, default='{}')
    medkits = Column(Integer, default=0) # Аптечки теперь учитываются отдельно для шанса 25%
    pet = Column(String, nullable=True) # Питомцы (без Лиса и Алабая)
    
    # --- Статистика ---
    mutants_killed = Column(Integer, default=0)
    deaths = Column(Integer, default=0)
    total_collects = Column(Integer, default=0)
    total_rc_earned = Column(Float, default=0.0)
    best_collect = Column(Float, default=0.0)
    daily_streak = Column(Integer, default=0)
    achievements = Column(String, default='[]')
    
    # --- Кланы ---
    clan_id = Column(Integer, ForeignKey('clans.id'), nullable=True)
    clan_role = Column(String, default='member') # leader, officer, member
    
    # --- Локации и Классы ---
    location = Column(String, default='normal') # Болото убрано из логики
    user_class = Column(String, default='stalker')
    last_free_class_change = Column(DateTime, nullable=True) # Для лимита раз в неделю
    
    # --- Системные ---
    is_admin = Column(Boolean, default=False)
    radio_active = Column(Boolean, default=False)

class Clan(Base):
    __tablename__ = 'clans'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    leader_id = Column(Integer)
    
    # Казна клана
    treasury_coins = Column(Float, default=0.0)
    # ИСПРАВЛЕНИЕ 1: Сюда зачисляются кристаллы при выдаче через /give
    treasury_crystals = Column(Integer, default=0) 
    
    # Характеристики клана
    level = Column(Integer, default=1)
    description = Column(String, default="Сталкерская группировка")
    members_count = Column(Integer, default=1)

# --- Настройка подключения к БД ---
# Файл базы данных будет называться radcoin_base.db
engine = create_engine('sqlite:///radcoin_base.db', pool_size=15, max_overflow=25)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def init_db():
    """Функция инициализации таблиц"""
    Base.metadata.create_all(engine)
