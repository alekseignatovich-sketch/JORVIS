import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Определяем путь к БД
DB_PATH = "jarvis.db"  # Railway поддерживает локальные файлы (но данные сбрасываются при перезапуске)
# Для продакшена лучше использовать PostgreSQL на Railway

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Позволяет обращаться к колонкам по имени
        self.create_tables()
        logger.info(f"✅ База данных инициализирована: {self.db_path}")
    
    def create_tables(self):
        """Создаём все таблицы при первом запуске"""
        cursor = self.conn.cursor()
        
        # Пользователи
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT DEFAULT 'ru',
                is_premium BOOLEAN DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Закладки
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message_text TEXT,
                message_type TEXT DEFAULT 'text',
                file_id TEXT,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags TEXT DEFAULT ''
            )
        ''')
        
        # Напоминания
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                remind_at TIMESTAMP NOT NULL,
                is_completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Заметки
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Индексы для ускорения запросов
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON bookmarks(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_user ON reminders(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id)')
        
        self.conn.commit()
        logger.info("✅ Таблицы созданы / проверены")
    
    # ==================== ПОЛЬЗОВАТЕЛИ ====================
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, 
                 last_name: str = None, language_code: str = 'ru'):
        """Добавить или обновить пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, language_code, joined_at)
            VALUES (?, ?, ?, ?, ?, COALESCE(
                (SELECT joined_at FROM users WHERE user_id = ?), 
                CURRENT_TIMESTAMP
            ))
        ''', (user_id, username, first_name, last_name, language_code, user_id))
        self.conn.commit()
        logger.debug(f"👤 Пользователь {user_id} сохранён")
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить данные пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # ==================== ЗАКЛАДКИ ====================
    
    def add_bookmark(self, user_id: int, message_text: str = None, 
                     message_type: str = 'text', file_id: str = None, tags: str = '') -> int:
        """Сохранить закладку"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO bookmarks (user_id, message_text, message_type, file_id, tags)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, message_text, message_type, file_id, tags))
        self.conn.commit()
        bookmark_id = cursor.lastrowid
        logger.debug(f"🔖 Закладка #{bookmark_id} сохранена для пользователя {user_id}")
        return bookmark_id
    
    def get_bookmarks(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Получить закладки пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM bookmarks 
            WHERE user_id = ? 
            ORDER BY saved_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_bookmark(self, bookmark_id: int, user_id: int) -> bool:
        """Удалить одну закладку"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM bookmarks WHERE id = ? AND user_id = ?', (bookmark_id, user_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def clear_bookmarks(self, user_id: int) -> int:
        """Очистить ВСЕ закладки пользователя. Возвращает количество удалённых."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM bookmarks WHERE user_id = ?', (user_id,))
        self.conn.commit()
        deleted = cursor.rowcount
        logger.info(f"🧹 Очищено {deleted} закладок для пользователя {user_id}")
        return deleted
    
    def count_bookmarks(self, user_id: int) -> int:
        """Подсчитать количество закладок"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM bookmarks WHERE user_id = ?', (user_id,))
        return cursor.fetchone()[0]
    
    # ==================== НАПОМИНАНИЯ ====================
    
    def add_reminder(self, user_id: int, text: str, remind_at: datetime) -> int:
        """Создать напоминание"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO reminders (user_id, text, remind_at)
            VALUES (?, ?, ?)
        ''', (user_id, text, remind_at.strftime('%Y-%m-%d %H:%M:%S')))
        self.conn.commit()
        reminder_id = cursor.lastrowid
        logger.debug(f"⏰ Напоминание #{reminder_id} установлено на {remind_at}")
        return reminder_id
    
    def get_active_reminders(self, user_id: int) -> List[Dict]:
        """Получить активные (не выполненные) напоминания"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM reminders 
            WHERE user_id = ? AND is_completed = 0 
            ORDER BY remind_at ASC
        ''', (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_due_reminders(self) -> List[Dict]:
        """Получить напоминания, время которых наступило"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM reminders 
            WHERE is_completed = 0 AND remind_at <= datetime('now', 'localtime')
        ''')
        return [dict(row) for row in cursor.fetchall()]
    
    def mark_reminder_completed(self, reminder_id: int):
        """Отметить напоминание как выполненное"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE reminders SET is_completed = 1 WHERE id = ?', (reminder_id,))
        self.conn.commit()
        logger.debug(f"✅ Напоминание #{reminder_id} выполнено")
    
    def delete_reminder(self, reminder_id: int, user_id: int) -> bool:
        """Удалить напоминание"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM reminders WHERE id = ? AND user_id = ?', (reminder_id, user_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def count_active_reminders(self, user_id: int) -> int:
        """Подсчитать активные напоминания"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM reminders WHERE user_id = ? AND is_completed = 0', (user_id,))
        return cursor.fetchone()[0]
    
    # ==================== ЗАМЕТКИ ====================
    
    def add_note(self, user_id: int, title: str, content: str = '') -> int:
        """Создать заметку"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO notes (user_id, title, content)
            VALUES (?, ?, ?)
        ''', (user_id, title, content))
        self.conn.commit()
        note_id = cursor.lastrowid
        logger.debug(f"📝 Заметка #{note_id} создана")
        return note_id
    
    def get_notes(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Получить заметки пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM notes 
            WHERE user_id = ? 
            ORDER BY updated_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]
    
    def update_note(self, note_id: int, user_id: int, title: str = None, content: str = None):
        """Обновить заметку"""
        cursor = self.conn.cursor()
        if title and content:
            cursor.execute('''
                UPDATE notes 
                SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ? AND user_id = ?
            ''', (title, content, note_id, user_id))
        elif title:
            cursor.execute('''
                UPDATE notes 
                SET title = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ? AND user_id = ?
            ''', (title, note_id, user_id))
        elif content:
            cursor.execute('''
                UPDATE notes 
                SET content = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ? AND user_id = ?
            ''', (content, note_id, user_id))
        self.conn.commit()
        logger.debug(f"✏️ Заметка #{note_id} обновлена")
    
    def delete_note(self, note_id: int, user_id: int) -> bool:
        """Удалить заметку"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM notes WHERE id = ? AND user_id = ?', (note_id, user_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def count_notes(self, user_id: int) -> int:
        """Подсчитать заметки"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM notes WHERE user_id = ?', (user_id,))
        return cursor.fetchone()[0]
    
    # ==================== СТАТИСТИКА ====================
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Получить статистику пользователя"""
        return {
            'bookmarks_count': self.count_bookmarks(user_id),
            'reminders_count': self.count_active_reminders(user_id),
            'notes_count': self.count_notes(user_id),
            'total_items': self.count_bookmarks(user_id) + self.count_active_reminders(user_id) + self.count_notes(user_id)
        }
    
    # ==================== ЗАКРЫТИЕ ====================
    
    def close(self):
        """Закрыть соединение с БД"""
        if self.conn:
            self.conn.close()
            logger.info("🔌 Соединение с БД закрыто")

# Глобальный экземпляр БД (для простоты использования)
db = Database()

# Автоматическое закрытие при завершении программы
import atexit
atexit.register(db.close)
