# 📝 Change Log

All notable changes to FreeMarket will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - 2025-11-XX

### Fixed
- **Authentication Module Refactoring** (2025-11-11)
  - Resolved circular import issues between `backend/auth.py` and `backend/api/endpoints/auth.py`
  - Moved all auth utilities (`get_current_user`, `get_current_user_optional`, `hash_password`, `verify_password`, `verify_token`, `create_access_token`, `create_refresh_token`, `hash_refresh_token`) to centralized `backend/auth.py` module
  - Updated all imports across codebase to use centralized auth module
  - Fixed `NameError` and `ImportError` issues during application startup

- **Database Schema Fixes** (2025-11-11)
  - Added missing `telegram_username` and `telegram_first_name` columns to `users` table
  - Added missing `rating_count` and `last_rating_update` columns to `users` table
  - Created `refresh_tokens` table for JWT refresh token storage with proper indexes
  - Created `auth_events` table for authentication event logging
  - Fixed `UndefinedColumn` and `UndefinedTable` errors during registration and login

- **Error Logging Improvements** (2025-11-11)
  - Added detailed error logging with traceback for registration failures
  - Added detailed error logging with traceback for login failures
  - Improved error messages in HTTPException responses for better debugging

### Added
- **Phase 2.5 Production Hardening**
  - Separate WebSocket gateway container (`freemarket-ws`)
  - Rate limiting middleware (Redis-based)
  - Sentry error tracking integration
  - Message delivery guarantees (TTL cache, re-delivery)
  - Auto-moderation escalation rules

- **Database Migrations** (2025-11-11)
  - Migration `m1n2o3p4q5r6`: Add missing telegram and rating fields to users table
  - Migration `n2o3p4q5r6s7`: Create refresh_tokens and auth_events tables

### Changed
- **Documentation**: Comprehensive updates across all docs for Phase 2.2 features
- **API endpoints**: Updated to 44 total endpoints
- **Testing scenarios**: Expanded to 15 comprehensive test cases
- **Database Schema**: Now includes 30+ tables with proper relationships and indexes

---

## [2.2.0] - 2025-11-XX

### Added
- **Phase 2.5: Personal Cabinet, Communications & Moderation**
  - Real-time WebSocket chat with delivery guarantees
  - Server-Sent Events (SSE) for live notifications
  - Review & trust analytics system with anti-spam
  - Comprehensive moderation & complaint system
  - Exchange history with export functionality
  - User action audit logging
  - Auto-cleanup of completed exchanges

- **New Database Tables (8 additional)**
  - `exchange_messages` - Chat messages with delivery tracking
  - `user_events` - Notification events system
  - `user_reviews` - Trust rating system
  - `exchange_history` - Complete exchange timelines
  - `reports` - Moderation complaint system
  - `user_trust_index` - Trust score analytics
  - `user_action_log` - Audit trail
  - `match_index` - Incremental matching optimization

- **API Endpoints (7 new groups, 44 total)**
  - Chat: WebSocket `/ws/exchange/{id}`, history, unread counts
  - SSE: `/api/events/stream` for real-time updates
  - Reviews: `/api/reviews`, trust ratings, analytics
  - Moderation: `/api/reports`, admin actions, dashboard
  - History: `/api/history/my-exchanges`, export functionality

### Changed
- **Architecture**: Event-driven system with Redis Streams
- **Matching**: 7-phase pipeline with incremental updates
- **Frontend**: Real-time synchronization without polling
- **Security**: Enhanced with rate limiting and monitoring

---

## [2.1.0] - 2025-11-XX

### Added
- **Phase 2: AI-Enhanced Matching & Incremental Updates**
  - Incremental matching system (MatchIndex table)
  - Event-driven match recalculations
  - Partial listing updates API
  - Auto-archive of completed exchanges
  - Enhanced AI semantic matching
  - Cross-category exchange support

### Changed
- **Matching Pipeline**: 7 phases with event-driven updates
- **API**: PATCH `/listings/{id}` for incremental updates
- **Database**: Optimized with GIN indexes and partial updates

---

## [2.0.0] - 2025-11-XX

### Added
- **Phase 1: Categories v6, JWT Authentication, Nginx**
  - Версионированная система категорий (35 permanent, 25 temporary)
  - JWT аутентификация с refresh токенами
  - HttpOnly, Secure cookies для безопасности
  - Nginx reverse proxy configuration
  - Минимальный личный кабинет
  - Rate limiting на auth endpoints

### Changed
- **Database Schema**: Полная реструктуризация с нормализацией
- **API**: 22 базовых endpoint'а
- **Architecture**: 7-layer system design

### Fixed
- **Migration Order**: Исправлена последовательность создания таблиц
- **Foreign Key Constraints**: Корректные связи между таблицами
- **API Proxy Routing**: Nginx правильно сохраняет URL префиксы

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
