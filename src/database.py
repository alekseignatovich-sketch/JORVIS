"""
Database module for JARVIS bot - PostgreSQL version
"""
import os
from datetime import datetime
from typing import Optional, List, Dict
import logging
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, 
    DateTime, ForeignKey, Index, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем строку подключения из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jarvis.db")

# Создаём движок SQLAlchemy
# Для Railway PostgreSQL используем пул соединений
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Проверяем соединение перед использованием
        pool_size=5,          # Размер пула
        max_overflow=10,      # Максимальное количество дополнительных соединений
        echo=False            # True для отладки SQL-запросов
    )
    logger.info("✅ Подключено к PostgreSQL")
else:
    # Fallback на SQLite для локальной разработки
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    logger.info("✅ Подключено к SQLite")

# Создаём сессию
SessionLocal = scoped_session(sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
))

Base = declarative_base()

# ==================== МОДЕЛИ ====================

class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    language_code = Column(String, default="ru")
    is_premium = Column(Boolean, default=False)
    joined_at = Column(DateTime, default=func.now())
    
    # Связи
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.user_id} @{self.username}>"

class Bookmark(Base):
    """Модель закладки"""
    __tablename__ = "bookmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    message_text = Column(Text, nullable=True)
    message_type = Column(String, default="text")  # text, photo, video, document
    file_id = Column(String, nullable=True)
    saved_at = Column(DateTime, default=func.now(), index=True)
    tags = Column(String, default="")  # через запятую: "работа,идеи"
    
    # Связь
    user = relationship("User", back_populates="bookmarks")
    
    def __repr__(self):
        return f"<Bookmark {self.id} user={self.user_id}>"

class Reminder(Base):
    """Модель напоминания"""
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    remind_at = Column(DateTime, nullable=False, index=True)
    is_completed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=func.now())
    
    # Связь
    user = relationship("User", back_populates="reminders")
    
    def __repr__(self):
        return f"<Reminder {self.id} user={self.user_id} at={self.remind_at}>"

class Note(Base):
    """Модель заметки"""
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)
    
    # Связь
    user = relationship("User", back_populates="notes")
    
    def __repr__(self):
        return f"<Note {self.id} user={self.user_id} title={self.title}>"

# Создаём все таблицы
Base.metadata.create_all(bind=engine)
logger.info("✅ Таблицы созданы / проверены")

# ==================== КОНТЕКСТНЫЙ МЕНЕДЖЕР ДЛЯ СЕССИЙ ====================

@contextmanager
def get_db_session():
    """Контекстный менеджер для безопасной работы с сессией"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка в сессии БД: {e}")
        raise
    finally:
        session.close()

# ==================== КЛАСС БАЗЫ ДАННЫХ ====================

class Database:
    """Основной класс для работы с базой данных"""
    
    # ==================== ПОЛЬЗОВАТЕЛИ ====================
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, 
                 last_name: str = None, language_code: str = 'ru'):
        """Добавить или обновить пользователя"""
        with get_db_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            
            if user:
                # Обновляем существующего
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                user.language_code = language_code
            else:
                # Создаём нового
                user = User(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    language_code=language_code
                )
                session.add(user)
            
            logger.debug(f"👤 Пользователь {user_id} сохранён")
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить данные пользователя"""
        with get_db_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                return {
                    'user_id': user.user_id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'language_code': user.language_code,
                    'is_premium': user.is_premium,
                    'joined_at': user.joined_at
                }
            return None
    
    # ==================== ЗАКЛАДКИ ====================
    
    def add_bookmark(self, user_id: int, message_text: str = None, 
                     message_type: str = 'text', file_id: str = None, tags: str = '') -> int:
        """Сохранить закладку"""
        with get_db_session() as session:
            # Проверяем, есть ли пользователь
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                self.add_user(user_id)
            
            bookmark = Bookmark(
                user_id=user_id,
                message_text=message_text,
                message_type=message_type,
                file_id=file_id,
                tags=tags
            )
            session.add(bookmark)
            session.flush()  # Получаем ID до коммита
            bookmark_id = bookmark.id
            
            logger.debug(f"🔖 Закладка #{bookmark_id} сохранена для пользователя {user_id}")
            return bookmark_id
    
    def get_bookmarks(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Получить закладки пользователя"""
        with get_db_session() as session:
            bookmarks = session.query(Bookmark)\
                .filter(Bookmark.user_id == user_id)\
                .order_by(Bookmark.saved_at.desc())\
                .limit(limit)\
                .all()
            
            return [{
                'id': bm.id,
                'user_id': bm.user_id,
                'message_text': bm.message_text,
                'message_type': bm.message_type,
                'file_id': bm.file_id,
                'saved_at': bm.saved_at,
                'tags': bm.tags
            } for bm in bookmarks]
    
    def delete_bookmark(self, bookmark_id: int, user_id: int) -> bool:
        """Удалить одну закладку"""
        with get_db_session() as session:
            result = session.query(Bookmark)\
                .filter(Bookmark.id == bookmark_id, Bookmark.user_id == user_id)\
                .delete()
            return result > 0
    
    def clear_bookmarks(self, user_id: int) -> int:
        """Очистить ВСЕ закладки пользователя. Возвращает количество удалённых."""
        with get_db_session() as session:
            result = session.query(Bookmark)\
                .filter(Bookmark.user_id == user_id)\
                .delete()
            logger.info(f"🧹 Очищено {result} закладок для пользователя {user_id}")
            return result
    
    def count_bookmarks(self, user_id: int) -> int:
        """Подсчитать количество закладок"""
        with get_db_session() as session:
            return session.query(Bookmark)\
                .filter(Bookmark.user_id == user_id)\
                .count()
    
    # ==================== НАПОМИНАНИЯ ====================
    
    def add_reminder(self, user_id: int, text: str, remind_at: datetime) -> int:
        """Создать напоминание"""
        with get_db_session() as session:
            # Проверяем, есть ли пользователь
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                self.add_user(user_id)
            
            reminder = Reminder(
                user_id=user_id,
                text=text,
                remind_at=remind_at
            )
            session.add(reminder)
            session.flush()
            reminder_id = reminder.id
            
            logger.debug(f"⏰ Напоминание #{reminder_id} установлено на {remind_at}")
            return reminder_id
    
    def get_active_reminders(self, user_id: int) -> List[Dict]:
        """Получить активные (не выполненные) напоминания"""
        with get_db_session() as session:
            reminders = session.query(Reminder)\
                .filter(Reminder.user_id == user_id, Reminder.is_completed == False)\
                .order_by(Reminder.remind_at.asc())\
                .all()
            
            return [{
                'id': rm.id,
                'user_id': rm.user_id,
                'text': rm.text,
                'remind_at': rm.remind_at,
                'is_completed': rm.is_completed,
                'created_at': rm.created_at
            } for rm in reminders]
    
    def get_due_reminders(self) -> List[Dict]:
        """Получить напоминания, время которых наступило"""
        with get_db_session() as session:
            now = datetime.now()
            reminders = session.query(Reminder)\
                .filter(Reminder.is_completed == False, Reminder.remind_at <= now)\
                .all()
            
            return [{
                'id': rm.id,
                'user_id': rm.user_id,
                'text': rm.text,
                'remind_at': rm.remind_at,
                'is_completed': rm.is_completed
            } for rm in reminders]
    
    def mark_reminder_completed(self, reminder_id: int):
        """Отметить напоминание как выполненное"""
        with get_db_session() as session:
            reminder = session.query(Reminder).filter(Reminder.id == reminder_id).first()
            if reminder:
                reminder.is_completed = True
                logger.debug(f"✅ Напоминание #{reminder_id} выполнено")
    
    def delete_reminder(self, reminder_id: int, user_id: int) -> bool:
        """Удалить напоминание"""
        with get_db_session() as session:
            result = session.query(Reminder)\
                .filter(Reminder.id == reminder_id, Reminder.user_id == user_id)\
                .delete()
            return result > 0
    
    def count_active_reminders(self, user_id: int) -> int:
        """Подсчитать активные напоминания"""
        with get_db_session() as session:
            return session.query(Reminder)\
                .filter(Reminder.user_id == user_id, Reminder.is_completed == False)\
                .count()
    
    # ==================== ЗАМЕТКИ ====================
    
    def add_note(self, user_id: int, title: str, content: str = '') -> int:
        """Создать заметку"""
        with get_db_session() as session:
            # Проверяем, есть ли пользователь
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                self.add_user(user_id)
            
            note = Note(
                user_id=user_id,
                title=title,
                content=content
            )
            session.add(note)
            session.flush()
            note_id = note.id
            
            logger.debug(f"📝 Заметка #{note_id} создана")
            return note_id
    
    def get_notes(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Получить заметки пользователя"""
        with get_db_session() as session:
            notes = session.query(Note)\
                .filter(Note.user_id == user_id)\
                .order_by(Note.updated_at.desc())\
                .limit(limit)\
                .all()
            
            return [{
                'id': n.id,
                'user_id': n.user_id,
                'title': n.title,
                'content': n.content,
                'created_at': n.created_at,
                'updated_at': n.updated_at
            } for n in notes]
    
    def update_note(self, note_id: int, user_id: int, title: str = None, content: str = None):
        """Обновить заметку"""
        with get_db_session() as session:
            note = session.query(Note)\
                .filter(Note.id == note_id, Note.user_id == user_id)\
                .first()
            
            if note:
                if title:
                    note.title = title
                if content:
                    note.content = content
                logger.debug(f"✏️ Заметка #{note_id} обновлена")
    
    def delete_note(self, note_id: int, user_id: int) -> bool:
        """Удалить заметку"""
        with get_db_session() as session:
            result = session.query(Note)\
                .filter(Note.id == note_id, Note.user_id == user_id)\
                .delete()
            return result > 0
    
    def count_notes(self, user_id: int) -> int:
        """Подсчитать заметки"""
        with get_db_session() as session:
            return session.query(Note)\
                .filter(Note.user_id == user_id)\
                .count()
    
    # ==================== СТАТИСТИКА ====================
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Получить статистику пользователя"""
        return {
            'bookmarks_count': self.count_bookmarks(user_id),
            'reminders_count': self.count_active_reminders(user_id),
            'notes_count': self.count_notes(user_id),
            'total_items': self.count_bookmarks(user_id) + 
                          self.count_active_reminders(user_id) + 
                          self.count_notes(user_id)
        }

# Глобальный экземпляр БД
db = Database()
