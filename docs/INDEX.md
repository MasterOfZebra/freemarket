# 📚 FreeMarket Documentation - Master Index

**Version:** 2.2 (Personal Cabinet, Real-Time Communications & Moderation)
**Last Updated:** Ноябрь 2025
**Status:** ✅ Production Ready with Full User Experience

---

## 🚀 **Quick Navigation**

### **I'm a...**

- **👤 User** → [Getting Started](#getting-started) (2 min)
- **👨‍💻 Developer** → [Development Setup](#for-developers) (10 min)
- **🏗️ DevOps** → [Deployment Guide](#for-devops) (15 min)
- **🧪 QA Tester** → [Testing Guide](#for-qa--testing) (20 min)

---

## ✨ **Quick Facts**

| Feature | Status | Location |
|---------|--------|----------|
| **🤖 AI Semantic Matching** | ✅ Active | [ARCHITECTURE.md#language-normalization--scoring-engine](./ARCHITECTURE.md#language-normalization--scoring-engine) |
| **🔄 Cross-Category Exchanges** | ✅ Active | [ARCHITECTURE.md#equivalenceengine-adaptive-tolerance](./ARCHITECTURE.md#equivalenceengine-adaptive-tolerance) |
| **Category Matching** | ✅ Active | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| **Telegram Notifications** | ✅ Active | [ARCHITECTURE.md#telegram-integration](./ARCHITECTURE.md#telegram-integration) |
| **Категории v6, JWT-аутентификация, Nginx** | ✅ Active | [ARCHITECTURE.md#categories-v6-jwt-nginx](./ARCHITECTURE.md#categories-v6-jwt-nginx) |
| **Location Filtering** | ✅ Active | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| **API (44 endpoints)** | ✅ Complete | [API_REFERENCE.md](./API_REFERENCE.md) |
| **Testing (15+ AI scenarios)** | ✅ Ready | [TESTING.md](./TESTING.md) |
| **Production Deployment** | ✅ Ready | [DEPLOYMENT.md](./DEPLOYMENT.md) |
| **Security (JWT, Redis, Rate Limiting)** | ✅ Active | [SECURITY.md](./SECURITY.md) |
| **DB Migrations (Alembic)** | ✅ Documented | [MIGRATIONS.md](./MIGRATIONS.md) |

---

## 🎯 **System Overview (60 seconds)**

**FreeMarket** это платформа для эквивалентного обмена:

1. **User fills form** - что хочет, что может предложить (по категориям)
2. **System matches** - находит ПЕРЕСЕЧЕНИЯ категорий и проверяет стоимость
3. **Gets notification** - Telegram уведомление о совпадении (ТОЛЬКО нужные категории!)
4. **Sees in cabinet** - просмотр всех совпадений на сайте
5. **Connects** - юзеры договариваются в Telegram и встречаются

**Key difference:** Система показывает партнёра ТОЛЬКО в тех категориях, которые вас интересуют!

---

## 📖 **Documentation Structure**

### **🏛️ Core Architecture**

**[ARCHITECTURE.md](./ARCHITECTURE.md)** (20 min read)
- Project overview & features
- 7-layer system architecture
- Complete user journey
- Data model (normalized schema)
- Category matching algorithm
- Категории v6, JWT-аутентификация и Nginx
- Telegram integration
- API endpoints overview

### **📡 API Reference**

**[API_REFERENCE.md](./API_REFERENCE.md)** (20 min read)
- All 37 endpoints documented
- Authentication flow (JWT + refresh tokens)
- Category v6 endpoints
- User cabinet endpoints
- Request/response examples
- Integration examples

### **🧪 Testing Guide**

**[TESTING.md](./TESTING.md)** (35 min read)
- 9 complete test scenarios
- Категории v6 миграции
- Auth rotation & LK access
- Step-by-step instructions
- Expected outputs
- Integration testing
- Troubleshooting guide

### **🔒 Security Guide**

**[SECURITY.md](./SECURITY.md)** (15 min read)
- JWT authentication security
- HttpOnly/Secure cookies
- Token rotation & revocation
- Redis revocation store
- Password hashing guidelines
- Data privacy policies

### **🗄️ Migrations Guide**

**[MIGRATIONS.md](./MIGRATIONS.md)** (25 min read)
- Database migration structure
- Step-by-step rollback procedures
- Troubleshooting migration issues
- Production deployment safety
- Version control best practices

### **🚀 Deployment Guide**

**[DEPLOYMENT.md](./DEPLOYMENT.md)** (25 min read)
- Local development setup
- Server deployment steps
- Docker configuration
- Database migration
- Environment variables
- Health checks & monitoring

---

## 👨‍💻 **For Developers**

### **Getting Started (Local Development)**

1. **Read:** [DEVELOPMENT.md](../DEVELOPMENT.md) (10 min)
2. **Setup:** Install dependencies, configure database
3. **Run:** `python backend/quick_test.py`
4. **Test:** Run test scenarios from [TESTING.md](./TESTING.md)

### **Understanding the Architecture**

1. **Start:** [ARCHITECTURE.md](./ARCHITECTURE.md) - complete overview
2. **Deep dive:** Category matching algorithm section
3. **API:** [API_REFERENCE.md](./API_REFERENCE.md) - all endpoints
4. **Code:** `backend/matching/category_matching.py` - implementation

### **Key Components**

| Component | File | Purpose |
|-----------|------|---------|
| **CategoryMatchingEngine** | `backend/matching/category_matching.py` | Core matching logic |
| **Category Form** | `src/components/CategoryListingsForm.jsx` | Two-column UI |
| **API Endpoint** | `backend/api/endpoints/listings_by_category.py` | Save listings |
| **Telegram Bot** | `backend/bot.py` | Send notifications |
| **Cabinet** | `src/pages/CabinetPage.jsx` | Match display |

### **Common Tasks**

- **Add new category?** Update `CATEGORIES` in frontend, add enum in backend
- **Change matching threshold?** Edit `min_category_score` in `CategoryMatchingEngine`
- **Add API endpoint?** Create file in `backend/api/endpoints/`, include in `router.py`
- **Modify Telegram message?** Edit template in `send_match_notification()` in `bot.py`

---

## 🏗️ **For DevOps**

### **Production Deployment**

1. **Prepare:** [DEPLOYMENT.md](./DEPLOYMENT.md) - full checklist
2. **Deploy:** Docker Compose, Nginx, PostgreSQL
3. **Monitor:** Health checks, logs, error tracking
4. **Maintain:** Database backups, updates, scaling

### **Quick Deployment Checklist**

```
☐ Set environment variables (.env)
☐ Configure PostgreSQL database
☐ Build Docker images
☐ Run docker-compose up
☐ Run health check
☐ Verify all 37 endpoints working
☐ Test Telegram notifications
☐ Check cabinet display
☐ Monitor logs for errors
```

### **Important Files**

- **docker-compose.prod.yml** - Production services
- **nginx config** - Web server setup
- **.env** - Environment variables
- **requirements.txt** - Python dependencies

---

## 🧪 **For QA / Testing**

### **Test Scenarios (9 Total)**

See [TESTING.md](./TESTING.md) for complete guide with:

1. **Basic Category Matching** - Single category with perfect match
2. **Multi-Category Matching** - Multiple intersecting categories
3. **Location-Based Filtering** - Different location combinations
4. **Filtered Listing Display** - Only showing matching categories
5. **Telegram Notification** - Message format & delivery
6. **Cabinet Display** - Match details in personal cabinet
7. **Chain Matching** - 3+ way exchange discovery
8. **Категории v6 миграции**
9. **Auth rotation & LK access**

### **Quick Test Commands**

```bash
# Run basic structure test
python backend/quick_test.py

# Test category matching
curl -X POST https://assistance-kz.ru/api/listings/create-by-categories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d @test_payload.json

# Find matches
curl -X POST https://assistance-kz.ru/api/matching/run-pipeline \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"user_id":null}'

# Check Telegram notifications sent
# (Check Telegram chat with bot)
```

See [TESTING_QUICK_COMMANDS.md](../TESTING_QUICK_COMMANDS.md) for all commands.

### **Expected Results**

Each test scenario has:
- ✅ Expected HTTP response codes
- ✅ Expected database changes
- ✅ Expected Telegram messages
- ✅ Verification checklist

---

## 📚 **Reference Materials**

### **Project Audit**

[PROJECT_AUDIT_REPORT.md](../PROJECT_AUDIT_REPORT.md) - Historical reference
- Initial project structure analysis
- Issues identified
- Optimization recommendations
- Now mostly resolved ✅

### **Local Development**

[DEVELOPMENT.md](../DEVELOPMENT.md)
- Python environment setup
- Database configuration
- Running tests locally
- Common errors & solutions

### **Quick Commands**

[TESTING_QUICK_COMMANDS.md](../TESTING_QUICK_COMMANDS.md)
- Copy-paste ready test commands
- API curl examples
- Database queries

### **Deployment Checklist**

[DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md)
- 6-phase production rollout plan
- Pre-deployment validation
- Post-deployment verification
- Rollback procedures

---

## 🔍 **Finding What You Need**

| I want to... | Read this | Time |
|-------------|----------|------|
| Understand the system | [ARCHITECTURE.md](./ARCHITECTURE.md) | 20 min |
| Use the API | [API_REFERENCE.md](./API_REFERENCE.md) | 15 min |
| Run tests | [TESTING.md](./TESTING.md) | 30 min |
| Deploy to production | [DEPLOYMENT.md](./DEPLOYMENT.md) | 25 min |
| Set up locally | [DEVELOPMENT.md](../DEVELOPMENT.md) | 10 min |
| Run quick test | [TESTING_QUICK_COMMANDS.md](../TESTING_QUICK_COMMANDS.md) | 5 min |
| Learn category matching | [ARCHITECTURE.md#category-matching-engine](./ARCHITECTURE.md#category-matching-engine) | 15 min |
| Implement Telegram | [ARCHITECTURE.md#telegram-integration](./ARCHITECTURE.md#telegram-integration) | 10 min |
| Understand security | [SECURITY.md](./SECURITY.md) | 15 min |
| Understand DB migrations | [MIGRATIONS.md](./MIGRATIONS.md) | 25 min |

---

## 🎓 **Learning Path**

### **For New Developers (1-2 hours)**

1. **10 min** - Read project overview above
2. **15 min** - Skim [ARCHITECTURE.md](./ARCHITECTURE.md)
3. **10 min** - Look at [API_REFERENCE.md](./API_REFERENCE.md) endpoints
4. **15 min** - Run `python backend/quick_test.py`
5. **30 min** - Run one test scenario from [TESTING.md](./TESTING.md)
6. **15 min** - Explore code in `backend/matching/category_matching.py`

### **For Feature Implementation**

1. Design feature → Add to [ARCHITECTURE.md](./ARCHITECTURE.md)
2. Create models → Update [database schema](./ARCHITECTURE.md#database-schema)
3. Add schemas → Update [API_REFERENCE.md](./API_REFERENCE.md)
4. Implement → Write code following patterns
5. Test → Add to [TESTING.md](./TESTING.md)

### **For Troubleshooting**

1. Check [TESTING.md](./TESTING.md) - "Troubleshooting" section
2. Review error in [DEVELOPMENT.md](../DEVELOPMENT.MD)
3. Check logs: `docker logs backend` or console output
4. Read relevant section in [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## 📊 **Project Statistics**

- **Documentation files:** 15 (consolidated and expanded)
- **API endpoints:** 44 (7 new for auth, categories v6, LK + 7 new for chat, reviews, moderation, SSE)
- **Test scenarios:** 15+ (added AI, chat, SSE, moderation, trust analytics scenarios)
- **Categories:** v6 with versioning (permanent/temporary exchange types)
- **Max locations:** 3 (Алматы, Астана, Шымкент)
- **Matching threshold:** 0.70 (70%)
- **Value tolerance:** ±15% (adaptive for cross-category)
- **Security:** JWT + refresh tokens with Redis revocation + rate limiting + Sentry
- **Real-time features:** WebSocket chat, SSE notifications, event-driven matching
- **Trust system:** Weighted ratings, anti-spam reviews, trust analytics
- **Moderation:** Auto-escalation, complaint processing, user safety

---

## ✅ **Documentation Status**

| Status | Count |
|--------|-------|
| ✅ Current & Complete | 11 files |
| 🗑️ Removed (duplicates) | 14 files |
| 📝 In active use | All |
| 🔄 Last updated | Ноябрь 2025 |

---

## 🚀 **Next Steps**

### **To Get Started:**

```bash
# 1. Clone/download project
cd FreeMarket

# 2. Read DEVELOPMENT.md for setup
cat DEVELOPMENT.md

# 3. Run quick test
python backend/quick_test.py

# 4. Read TESTING.md and run scenarios
cat docs/TESTING.md
```

### **To Deploy:**

```bash
# 1. Read DEPLOYMENT.md
cat docs/DEPLOYMENT.md

# 2. Follow deployment checklist
cat DEPLOYMENT_CHECKLIST.md

# 3. Deploy using docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

---

## 💬 **Questions?**

- **"How does matching work?"** → [ARCHITECTURE.md#category-matching-engine](./ARCHITECTURE.md#category-matching-engine)
- **"What's the API?"** → [API_REFERENCE.md](./API_REFERENCE.md)
- **"How to test?"** → [TESTING.md](./TESTING.md)
- **"How to deploy?"** → [DEPLOYMENT.md](./DEPLOYMENT.md)
- **"Local setup?"** → [DEVELOPMENT.md](../DEVELOPMENT.MD)
- **"Understand security?"** → [SECURITY.md](./SECURITY.md)
- **"Understand DB migrations?"** → [MIGRATIONS.md](./MIGRATIONS.md)

---

## 📌 **Key Files Reference**

```
docs/
├── INDEX.md                    ← You are here
├── ARCHITECTURE.md             ← System design (READ THIS FIRST!)
├── API_REFERENCE.md            ← All endpoints
├── TESTING.md                  ← Test guide & scenarios
├── SECURITY.md                 ← Security guidelines
├── MIGRATIONS.md               ← Database migration guide
└── DEPLOYMENT.md               ← Production setup

root/
├── README.md                   ← Quick intro
├── DEVELOPMENT.md              ← Local dev guide
├── TESTING_QUICK_COMMANDS.md   ← Copy-paste commands
├── DEPLOYMENT_CHECKLIST.md     ← 6-phase rollout
└── PROJECT_AUDIT_REPORT.md     ← Historical reference
```

---

**🎉 Welcome to FreeMarket!**

Start with [ARCHITECTURE.md](./ARCHITECTURE.md) to understand the system, then choose your path above based on your role. Happy coding! 🚀
