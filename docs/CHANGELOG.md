# 📝 Change Log

All notable changes to FreeMarket will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - 2025-11-XX

### Added
- **Категории v6**: Новая версия системы категорий с версионированием
  - Таблицы: `category_versions`, `categories_v6`, `category_mappings`
  - API endpoints: `GET /v1/categories`, `GET /v1/categories/permanent`, `GET /v1/categories/temporary`
  - Поддержка миграции legacy объявлений в новые структуры

- **Минимальный личный кабинет (LK)**
  - API endpoints: `GET /user/cabinet`, `GET /user/listings`, `GET /user/exchanges`
  - Профиль пользователя, список объявлений, активные обмены
  - Интеграция с фронтендом (LoginModal, UserCabinet компоненты)

- **JWT аутентификация с refresh токенами**
  - Short-lived access tokens (15 минут) + long-lived refresh tokens (30 дней)
  - Refresh tokens в HttpOnly, Secure cookies
  - Server-side revocation через Redis
  - Token rotation при каждом refresh
  - Rate limiting на auth endpoints

- **Документация безопасности (SECURITY.md)**
  - JWT flow и rotation
  - HttpOnly/Secure cookies
  - Redis revocation store
  - Password hashing (Argon2id/bcrypt)
  - Data privacy guidelines

- **Руководство по миграциям (MIGRATIONS.md)**
  - Step-by-step rollback procedures
  - Troubleshooting migration issues
  - Best practices для development/production

### Changed
- **API endpoints**: Добавлено 7 новых endpoints для auth, categories v6, LK
- **Database schema**: Исправлена миграция `50c3593832b4` - теперь создает `listings` вместо `market_listings`
- **UI improvements**: Удалены дублирующие элементы на главной странице
- **Nginx proxy**: Исправлено сохранение `/api` префикса при proxy_pass
- **Документация**: Обновлена в соответствии с текущей кодовой базой

### Fixed
- **Migration order**: Исправлена последовательность создания таблиц в Alembic миграциях
- **Foreign key constraints**: `listing_items` теперь корректно ссылается на `listings`
- **API proxy routing**: Nginx правильно проксирует `/api/*` запросы

---

## [2.0.0] - 2025-01-15

### Added
- **Category-based matching**: Новый алгоритм матчинга по категориям
- **Telegram notifications**: Уведомления о совпадениях в Telegram
- **Location filtering**: Фильтрация по городам (Алматы, Астана, Шымкент)
- **Chain matching**: Поиск многосторонних обменов (3+ участников)
- **Personal cabinet**: Просмотр совпадений на сайте
- **Unified matching pipeline**: 5-фазный pipeline матчинга

### Changed
- **Architecture**: Полностью переработана архитектура (7 слоев)
- **Database**: Нормализованная схема с поддержкой категорий
- **API**: 22 endpoint'а для всех функций
- **Documentation**: Консолидирована документация

### Technical Details
- **Matching algorithm**: CategoryMatchingEngine с configurable scoring
- **Database**: PostgreSQL с индексами для быстрого поиска
- **API**: FastAPI с Pydantic validation
- **Frontend**: React с category-based forms
- **Bot**: Telegram bot для уведомлений

---

## [1.0.0] - 2024-XX-XX

### Added
- Initial MVP with basic exchange functionality
- User registration and listings
- Basic matching by location
- Simple Telegram notifications

---

## Types of changes
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities

---

## Versioning Guidelines

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

---

## Release Process

1. Update version in `backend/main.py`
2. Update this CHANGELOG.md file
3. Create git tag: `git tag v2.0.1`
4. Push tag: `git push origin v2.0.1`
5. Deploy to production

---

## Contributing

When making changes:
1. Add entry to "Unreleased" section above
2. Categorize as Added/Changed/Fixed/etc.
3. Include technical details for complex changes
4. Update version number if breaking changes

See [CONTRIBUTING.md](../CONTRIBUTING.md) for more details.
