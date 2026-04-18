from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True) # ID пользователя в Telegram
    username = Column(String)
    
    # Валюты
    radcoins = Column(Float, default=0)
    radfragments = Column(Integer, default=0)
    radcrystals = Column(Integer, default=0)
    
    # Прогресс
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    
    # Кулдауны и временные эффекты
    last_collection = Column(DateTime, nullable=True)
    next_collection_time = Column(DateTime, nullable=True)
    last_hunt = Column(DateTime, nullable=True)
    cooldown_reducer_until = Column(DateTime, nullable=True)
    energy_drink_until = Column(DateTime, nullable=True)
    
    # Снаряжение и инвентарь (JSON строки)
    inventory = Column(String, default='[]')
    equipped = Column(String, default='{}')
    medkits = Column(Integer, default=0)
    
    # Статистика
    mutants_killed = Column(Integer, default=0)
    deaths = Column(Integer, default=0)
    total_collects = Column(Integer, default=0)
    
    # Классы и Роли
    user_class = Column(String, default='stalker')
    last_free_class_change = Column(DateTime, nullable=True)
    
    # Кланы
    clan_id = Column(Integer, ForeignKey('clans.id'), nullable=True)
    clan_role = Column(String, default='member') # leader, officer, member
    
    # Локации и другое
    location = Column(String, default='normal')
    is_admin = Column(Boolean, default=False)

class Clan(Base):
    __tablename__ = 'clans'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    leader_id = Column(Integer)
    
    # Казна клана
    treasury_coins = Column(Float, default=0)
    treasury_crystals = Column(Integer, default=0) # Сюда будут падать кристаллы из /give
    
    # Уровни и улучшения клана
    level = Column(Integer, default=1)
    description = Column(String, default="Новый клан")

# Настройка подключения
# Используем SQLite для простоты. Файл будет называться bot_data.db
engine = create_engine('sqlite:///bot_data.db', pool_size=10, max_overflow=20)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def init_db():
    Base.metadata.create_all(engine)
