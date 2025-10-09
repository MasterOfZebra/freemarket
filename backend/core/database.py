import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- 1. Читаем URL из переменной окружения ---
DATABASE_URL = os.getenv("DATABASE_URL")

# --- 2. Если переменная не задана — используем SQLite по умолчанию ---
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./app.db"
    connect_args = {"check_same_thread": False}  # нужно только для SQLite
else:
    connect_args = {}  # PostgreSQL и другие движки не требуют этого

# --- 3. Создаём движок SQLAlchemy ---
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# --- 4. Фабрика сессий ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- 5. Базовый класс моделей ---
Base = declarative_base()

# --- 6. Dependency для FastAPI ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
