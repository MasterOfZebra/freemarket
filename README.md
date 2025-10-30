# 🎁 FreeMarket - Free Marketplace for Mutual Aid & Exchange

**Version:** 2.0 (Phase 5 - Production Ready)
**Status:** ✅ Clean, Unified, Tested

---

## 🚀 Quick Start

FreeMarket is a **peer-to-peer marketplace** for mutual aid and resource exchange with:
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

### 1. User Registration
```
POST /api/users/
- username
- contact (Telegram)
- locations (select 1-3 cities)
```

### 2. Market Listings
```
POST /api/market-listings/
- Type: wants (request) or offers (provide)
- Category: food, tools, clothes, etc.
- Description
```

### 3. Unified Matching Pipeline
```
POST /api/matching/run-pipeline

5 Phases:
1. Location-aware filtering
2. Unified scoring
3. Bilateral matching (2-way)
4. Chain discovery (3+ way)
5. Notifications sent
```

### 4. Exchange Execution
- Users meet in shared location
- Exchange items
- Leave ratings

---

## 📁 Project Structure

```
FreeMarket/
├── docs/                       📚 UNIFIED DOCUMENTATION
│   ├── INDEX.md               (Start here)
│   ├── ARCHITECTURE.md        (System design)
│   ├── API_REFERENCE.md       (All endpoints)
│   ├── TESTING.md             (Test scenarios)
│   └── ... (more in docs/)
│
├── backend/                    🔧 API & Logic
│   ├── api/
│   │   ├── endpoints/         (Modular endpoints)
│   │   │   ├── health.py
│   │   │   ├── users.py
│   │   │   ├── market_listings.py
│   │   │   ├── exchange_chains.py
│   │   │   ├── notifications.py
│   │   │   └── matching.py    (Unified pipeline)
│   │   └── router.py
│   ├── matching/
│   │   ├── __init__.py
│   │   └── flow.py            (MatchingEngine - core logic)
│   ├── models.py              (DB models)
│   ├── main.py                (FastAPI app)
│   └── ...
│
├── src/                        🎨 Frontend
│   ├── components/
│   ├── pages/
│   ├── services/
│   ├── App.jsx
│   └── ...
│
├── docker/                     🐳 Deployment
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── Dockerfile.bot
│   └── docker-compose.prod.yml
│
└── scripts/                    📜 Utilities
    ├── deploy/
    └── test/
```

---

## 🔄 Core Algorithm: Unified Matching Engine

**Single source of truth:** `backend/matching/flow.py`

```python
class MatchingEngine:
    # Phase 1: Filter by location overlap
    def find_location_aware_candidates(item) -> List[Item]

    # Phase 2: Score with all factors
    def calculate_score(item_a, item_b) -> float
    # = text_similarity(0.7) + trust_bonus(0.2) + location_bonus(0.1)

    # Phase 3: Find mutual exchanges
    def find_bilateral_matches(item) -> List[Match]
    # Alice.want ⊆ Bob.offer AND Bob.want ⊆ Alice.offer

    # Phase 4: Discover chains
    def discover_chains() -> int
    # DFS graph search for cycles (3-10 participants)

    # Phase 5: Notify participants
    def notify_matches(matches) -> None

    # Orchestrate all phases
    def run_full_pipeline(user_id=None) -> Dict
```

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

See [docs/INDEX.md](./docs/INDEX.md) for complete navigation.

---

## ✅ Current Status (Phase 5)

```
✅ Code:           Unified & Clean
✅ Architecture:   Production Ready
✅ Matching:       5-Phase Pipeline
✅ Locations:      Multi-city support
✅ Documentation:  Consolidated
✅ Testing:        Ready
✅ Deployment:     Docker Compose
```

---

## 📊 Version History

- **v2.0** (Jan 2025) - Phase 5: Unified architecture, clean codebase
- **v1.0** - Initial MVP

See [docs/CHANGELOG.md](./docs/CHANGELOG.md) for details.

---

**📖 Ready to start? Go to [docs/INDEX.md](./docs/INDEX.md)**
