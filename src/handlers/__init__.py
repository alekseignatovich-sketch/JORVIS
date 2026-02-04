# Импортируем все роутеры
from .bookmarks import router as bookmarks_router
from .reminders import router as reminders_router
from .notes import router as notes_router
from .settings import router as settings_router

# Экспортируем для удобства
__all__ = ['bookmarks_router', 'reminders_router', 'notes_router', 'settings_router']

# Алиасы для обратной совместимости
router = bookmarks_router  # Главный роутер (можно изменить)
