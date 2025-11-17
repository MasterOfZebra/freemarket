"""
Configuration for SQLAdmin panel
"""

import os


# Admin panel configuration
ADMIN_CONFIG = {
    "title": "FreeMarket Admin",
    "logo_url": "/static/logo.svg",
    "login_logo_url": "/static/logo.svg",
    "admin_path": "/admin",
    "database_url": os.getenv("DATABASE_URL"),
    "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
    "language": "ru",  # Russian interface
    "theme": "light",
}

# Security settings
ADMIN_SECURITY = {
    "session_cookie_name": "freemarket_admin_session",
    "session_max_age": 3600 * 24 * 7,  # 7 days
    "secret_key": os.getenv("ADMIN_SECRET_KEY", os.getenv("JWT_SECRET_KEY")),
}

# Role permissions mapping
ADMIN_PERMISSIONS = {
    "admin": [
        "users.*", "listings.*", "complaints.*", "audit.*",
        "admin.*", "moderation.*", "reports.*"
    ],
    "moderator": [
        "users.view", "users.edit", "users.ban",
        "listings.view", "listings.edit", "listings.moderate",
        "complaints.view", "complaints.resolve"
    ],
    "user": [
        "listings.view"
    ]
}

# Menu structure
ADMIN_MENU = [
    {
        "name": "Пользователи",
        "icon": "fas fa-users",
        "children": [
            {"name": "Все пользователи", "url": "/admin/user/list"},
            {"name": "Заблокированные", "url": "/admin/user/banned"},
        ]
    },
    {
        "name": "Объявления",
        "icon": "fas fa-list",
        "children": [
            {"name": "Все объявления", "url": "/admin/listing/list"},
            {"name": "На модерации", "url": "/admin/listing/pending"},
            {"name": "Архив", "url": "/admin/listing/archived"},
        ]
    },
    {
        "name": "Модерация",
        "icon": "fas fa-gavel",
        "children": [
            {"name": "Жалобы", "url": "/admin/complaint/list"},
            {"name": "Нарушения", "url": "/admin/violation/list"},
        ]
    },
    {
        "name": "Аудит",
        "icon": "fas fa-history",
        "url": "/admin/audit/list"
    },
    {
        "name": "Аналитика",
        "icon": "fas fa-chart-bar",
        "children": [
            {"name": "Статистика", "url": "/admin/analytics/dashboard"},
            {"name": "Отчёты", "url": "/admin/analytics/reports"},
        ]
    }
]
