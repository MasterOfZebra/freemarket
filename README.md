# 🎁 FreeMarket - AI-Powered Marketplace for Mutual Aid & Exchange

**Version:** 2.2.1 (Production Ready & Fully Tested)
**Status:** ✅ Production Ready with Full User Experience

---

## 🚀 Quick Start

FreeMarket is a **complete peer-to-peer marketplace platform** for mutual aid and resource exchange with:
- 🤖 **AI Semantic Matching** - Vector similarity & fuzzy matching for cross-category exchanges
- 💬 **Real-Time Chat** - WebSocket-based messaging in exchanges
- 🔔 **Live Notifications** - SSE streams for instant updates
- ⭐ **Review System** - Trust analytics and user ratings
- 🚨 **Moderation Tools** - Complaint system with auto-moderation
- 📱 **Personal Cabinet** - Full user dashboard with history & controls
- ✅ Multi-location support (Алматы, Астана, Шымкент)
- ✅ Bilateral matching (2-way exchanges)
- ✅ Chain matching (3+ participant exchanges)
- ✅ Telegram bot notifications
- ✅ Real-time status updates

### 📚 Documentation

**START HERE:** [📖 Documentation Index](./docs/INDEX.md)

| Role | Quick Links |
|------|------------|
| **👥 Users** | [Getting Started](./docs/GETTING_STARTED.md) • [User Guide](./docs/USER_GUIDE.md) |
| **👨‍💻 Developers** | [Architecture](./docs/ARCHITECTURE.md) • [API Reference](./docs/API_REFERENCE.md) • [Setup](./docs/DEVELOPMENT.md) |
| **🚀 DevOps** | [Deployment](./docs/DEPLOYMENT.md) • [Configuration](./docs/CONFIGURATION.md) |
| **🧪 QA/Testing** | [Test Guide](./docs/TESTING.md) • [Integration Tests](./docs/INTEGRATION_TESTS.md) |

---

## 🎯 Key Features

### 1. User Registration (JWT)
```
POST /auth/register
- email
- password
- username
- full_name
- city
- telegram_contact
```

### 2. Market Listings (v6 Categories)
```
POST /api/listings/create-by-categories
- wants: { "PERMANENT": [...], "TEMPORARY": [...] }
- offers: { "PERMANENT": [...], "TEMPORARY": [...] }
```

### 3. AI-Powered Matching Pipeline
```
POST /api/matching/run-pipeline

6 Enhanced Phases:
1. Location-aware filtering
2. AI Semantic Scoring (SentenceTransformers + Fuzzy)
3. Adaptive Tolerance (Cross-category support)
4. Bilateral matching (2-way)
5. Chain discovery (3+ way)
6. Smart Notifications sent
```

**AI Matching Features:**
- 🤖 **Vector Similarity** - Semantic understanding across languages
- 🔍 **Fuzzy Matching** - Handles typos and variations
- 🎯 **Cross-Category Matching** - Items can match across different categories
- 📊 **Adaptive Scoring** - Dynamic thresholds for better accuracy

### 4. Personal Cabinet & Communications
```
GET /user/cabinet
- Profile management
- Active exchanges tracking
- Exchange history with filters

WebSocket /ws/exchange/{id}
- Real-time chat during exchanges
- Message delivery guarantees
- Online/offline status

SSE /api/events/stream
- Live notifications
- Real-time updates
- Push events (Firebase integration)
```

### 5. Review & Trust System
```
POST /api/reviews
- Post-exchange ratings
- Anti-spam controls
- Public/private reviews

GET /api/users/{id}/rating
- Trust score calculation
- Weighted ratings analytics
- Verified user badges
```

### 6. Moderation & Safety
```
POST /api/reports
- Complaint submission
- Auto-moderation triggers
- Admin dashboard access

Admin /admin/users/{id}/ban
- User suspension system
- Automated escalation
- Appeal mechanisms
```

### 7. AI-Powered Matching Pipeline
```
POST /api/matching/run-pipeline

7 Enhanced Phases:
1. Location-aware filtering
2. AI Semantic Scoring (SentenceTransformers + Fuzzy)
3. Adaptive Tolerance (Cross-category support)
4. Incremental index updates (MatchIndex table)
5. Bilateral matching (2-way)
6. Chain discovery (3+ way)
7. Smart Notifications sent
```

**AI Matching Features:**
- 🤖 **Vector Similarity** - Semantic understanding across languages
- 🔍 **Fuzzy Matching** - Handles typos and variations
- 🎯 **Cross-Category Matching** - Items can match across different categories
- 📊 **Adaptive Scoring** - Dynamic thresholds for better accuracy
- 🔄 **Incremental Updates** - Event-driven matching recalculations
- ⚡ **Real-Time Sync** - Auto-cleanup and profile updates

---
### 🚀 Version 2.2 User Experience Enhancements
- **Real-Time Communications** - WebSocket чат с гарантией доставки и SSE уведомления
- **Personal Cabinet** - Полный дашборд пользователя с историей обменов и фильтрами
- **Review & Trust System** - Система отзывов с анти-спам контролем и trust-аналитикой
- **Moderation & Safety** - Автоматическая модерация жалоб с эскалацией и банами
- **Production Hardening** - Rate limiting, Sentry monitoring, отдельный WebSocket gateway
- **Incremental Matching** - Событийно-ориентированные обновления мэтчинга без полной пересчета
- **Auto-Sync & Cleanup** - Автоматическая синхронизация истории и удаление завершенных обменов

## 📁 Project Structure

```
FreeMarket/
├── docs/                       📚 UNIFIED DOCUMENTATION
│   ├── INDEX.md               (Start here)
│   ├── ARCHITECTURE.md        (System design)
│   ├── API_REFERENCE.md       (All endpoints)
│   ├── TESTING.md             (Test scenarios)
│   ├── SECURITY.md            (Security guidelines)
│   ├── MIGRATIONS.md          (Database migration guide)
│   └── DEPLOYMENT.md          (Deployment guide)
│
├── backend/                    🔧 Production-Ready API & Logic
│   ├── api/
│   │   ├── endpoints/         (Modular endpoints - 44 total)
│   │   │   ├── auth.py        (JWT authentication)
│   │   │   ├── categories.py  (v6 categories system)
│   │   │   ├── health.py      (Health checks)
│   │   │   ├── listings_exchange.py (AI matching + incremental)
│   │   │   ├── matching.py    (Pipeline orchestration)
│   │   │   ├── notifications.py (Telegram + real-time)
│   │   │   ├── chat.py        (WebSocket chat)
│   │   │   ├── reviews.py     (Trust & ratings)
│   │   │   ├── moderation.py  (Reports & admin)
│   │   │   ├── exchange_history.py (History & export)
│   │   │   ├── sse.py         (Server-sent events)
│   │   │   ├── user_profile.py (Cabinet access)
│   │   │   └── users.py       (User management)
│   │   └── router.py          (API routing)
│   ├── matching/              🤖 AI Matching Engine
│   │   ├── __init__.py
│   │   ├── engine.py          (Core matching logic)
│   │   ├── flow.py            (Pipeline orchestration)
│   │   ├── semantic_embedder.py (SentenceTransformers)
│   │   ├── rule_based.py      (Traditional matching)
│   │   ├── threshold_tuner.py (Adaptive thresholds)
│   │   └── model_predictor.py (ML predictions)
│   ├── events.py              🔄 Event-driven architecture
│   ├── match_index_service.py 🔄 Incremental matching
│   ├── match_updater.py       🔄 Background match updates
│   ├── chat_service.py        💬 Real-time chat
│   ├── notification_service.py 🔔 Live notifications
│   ├── reviews_service.py     ⭐ Trust analytics
│   ├── moderation_service.py  🚨 Auto-moderation
│   ├── exchange_sync.py       📜 History sync
│   ├── report_processor.py    🚨 Background moderation
│   ├── language_normalization.py 🤖 NLP Processing
│   ├── scoring.py             📊 Composite Scoring
│   ├── equivalence_engine.py  ⚖️ Value Matching
│   ├── rate_limiting.py       🛡️ Security middleware
│   ├── error_tracking.py      📊 Sentry integration
│   ├── models.py              (SQLAlchemy DB models - 30+ tables)
│   ├── auth.py                (Centralized auth utilities)
│   ├── main.py                (FastAPI application)
│   └── ...
│
├── frontend/                   🎨 Frontend
│   ├── components/
│   ├── pages/
│   ├── services/
│   ├── App.jsx
│   └── ...
│
├── docker/                     🐳 AI-Optimized Deployment
│   ├── Dockerfile.backend      (Main API service)
│   ├── Dockerfile.matcher      (AI Matching engine)
│   ├── Dockerfile.frontend     (React SPA)
│   ├── Dockerfile.bot          (Telegram notifications)
│   ├── nginx/
│   │   └── conf.d/
│   │       └── default.conf
│   └── docker-compose.prod.yml
│
└── scripts/                    📜 Utilities
    ├── deploy/
    └── test/
```

---

## 🤖 AI-Powered Matching System

**Core Engine:** `backend/matching/engine.py` + `backend/scoring.py` + `backend/match_updater.py`

```python
class EnhancedMatchingEngine:
    # Phase 1: Location-aware filtering
    def find_location_aware_candidates(item) -> List[Item]

    # Phase 2: AI Semantic Scoring
    def calculate_ai_score(item_a, item_b) -> MatchingScore
    # = semantic_vector(0.4) + word_overlap(0.6) + cost_priority + duration_penalty

    # Phase 3: Cross-category matching
    def find_cross_category_matches() -> List[Match]
    # Dynamic thresholds for cross-category exchanges

    # Phase 4: Incremental index updates (NEW!)
    def update_match_index(user_id, changes) -> None
    # Event-driven updates via MatchIndex table

    # Phase 5: Find mutual exchanges
    def find_bilateral_matches(item) -> List[Match]
    # Alice.want ↔ Bob.offer AND Bob.want ↔ Alice.offer

    # Phase 6: Discover exchange chains
    def discover_chains() -> int
    # Graph search with AI-optimized scoring

    # Phase 7: Smart notifications & auto-cleanup
    def notify_matches(matches) -> None
    def auto_archive_completed_exchanges() -> None

    # Orchestrate enhanced pipeline
    def run_ai_pipeline(user_id=None) -> Dict
```

**AI Components:**
- **Semantic Embedder** (`semantic_embedder.py`) - Vector similarity
- **Language Processor** (`language_normalization.py`) - Text cleaning & synonyms
- **Composite Scorer** (`scoring.py`) - Multi-factor scoring
- **Adaptive Engine** (`equivalence_engine.py`) - Dynamic thresholds
- **Match Index Service** (`match_index_service.py`) - Incremental updates
- **Match Updater Worker** (`match_updater.py`) - Background recalculation
- **Event Bus** (`events.py`) - Asynchronous event handling

---

## 🚀 Getting Started

### For Development
```bash
# 1. Clone and setup
git clone <repo>
cd FreeMarket

# 2. Follow docs/DEVELOPMENT.md
# - Install dependencies
# - Setup database
# - Run locally
```

### For Production
```bash
# Follow docs/DEPLOYMENT.md
docker-compose -f docker/docker-compose.prod.yml up
```

---

## 📞 Documentation

**Everything is in `/docs/`:**
- User guides
- API reference
- Architecture
- Testing scenarios
- Deployment guide
- Configuration
- Security
- Database Migrations

See [docs/INDEX.md](./docs/INDEX.md) for complete navigation.

---

## ✅ Current Status (Phase 2.5)

```
✅ Code:           Production Hardened & Fully Tested
✅ Architecture:   Event-Driven & Real-Time
✅ Matching:       7-Phase Pipeline + Incremental
✅ Communications: WebSocket Chat + SSE Notifications
✅ Cabinet:        Full User Dashboard
✅ Reviews:        Trust Analytics & Anti-Spam
✅ Moderation:     Auto-Escalation & Safety
✅ Documentation:  Updated & Comprehensive
✅ Testing:        15+ AI Scenarios
✅ Deployment:     Docker Compose + Monitoring
✅ Security:       JWT + Rate Limiting + Sentry
✅ Migrations:     30+ Tables + Event Streams
✅ Authentication: Fully Functional (Register/Login/Refresh)
✅ Database:       All Tables Created & Tested
```

---

## 📊 Version History

- **v2.2.1** (Ноябрь 2025) - Bug Fixes: Исправлены циклические импорты, добавлены недостающие таблицы БД, улучшено логирование ошибок
- **v2.2** (Ноябрь 2025) - Phase 2.5: Личный кабинет, чат, отзывы, модерация, production hardening
- **v2.1** (Ноябрь 2025) - Phase 2: AI мэтчинг, инкрементальные обновления, автосинхронизация
- **v2.0** (Ноябрь 2025) - Phase 1: Категории v6, JWT-аутентификация, Nginx
- **v1.0** - Initial MVP

See [docs/CHANGELOG.md](./docs/CHANGELOG.md) for details.

---

**📖 Ready to start? Go to [docs/INDEX.md](./docs/INDEX.md)**
