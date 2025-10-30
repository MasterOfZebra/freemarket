# ⚡ PHASE 3 QUICK START GUIDE

**Status:** Ready to implement
**Scope:** Frontend + API Integration for local Russian site
**Estimated Time:** 4 weeks
**Target Users:** 10-50 concurrent

---

## 🎯 WHAT PHASE 3 DELIVERS

```
┌─────────────────────────────────────────────────────────────┐
│                     USER EXPERIENCE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. User fills TWO tabs:                                    │
│     🟢 Permanent: value-based exchange                      │
│     🟠 Temporary: rental/lease with daily rates             │
│                                                             │
│  2. System finds matches:                                   │
│     • Compares values (±15% tolerance)                      │
│     • Compares daily rates                                  │
│     • Filters by location                                   │
│     • Scores matches (0.0-1.0)                              │
│                                                             │
│  3. User sees results:                                      │
│     • Partner info + rating                                 │
│     • Match quality (green/yellow/red)                      │
│     • Matching categories                                   │
│     • Contact button (Telegram)                             │
│                                                             │
│  4. Notifications:                                          │
│     • Telegram: "New match! 87% Score"                      │
│     • Email: Optional details                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 ARCHITECTURE SUMMARY

```
FRONTEND (React)
  ├── Tab 1: Permanent Exchange (Green)
  │    └── Form: Category, Item, Value, Description
  ├── Tab 2: Temporary Exchange (Orange)
  │    └── Form: Category, Item, Value, Duration, Daily Rate
  └── Matches Display
       ├── Filter by Category
       ├── Color-coded scores
       └── Contact buttons

         ↓ API Calls ↓

BACKEND (FastAPI)
  ├── Phase 1: Database + Models
  │    └── Listings, Items, Users (SQLAlchemy ORM)
  ├── Phase 2: Matching Engine
  │    ├── Language Normalization (Russian/English)
  │    ├── Location Filtering
  │    ├── Core Matching (permanent vs temporary)
  │    ├── Category Matching
  │    ├── Score Aggregation
  │    └── Notifications (Telegram)
  └── API Endpoints
       ├── GET /api/listings/user/{user_id}
       ├── POST /api/listings/create-by-categories
       └── GET /api/listings/find-matches/{user_id}

         ↓ Data ↓

DATABASE (PostgreSQL)
  ├── Users + Locations
  └── Listings + Items (exchange_type, duration_days, value_tenge)
```

---

## 🚀 IMPLEMENTATION ROADMAP

### **WEEK 1: Frontend UI Structure**

**Task 1.1: Create Tab Component**
```typescript
// src/components/ExchangeTabs.tsx

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import PermanentTab from './PermanentTab';
import TemporaryTab from './TemporaryTab';

export default function ExchangeTabs() {
  return (
    <Tabs defaultValue="permanent" className="w-full">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="permanent" className="flex items-center gap-2">
          🟢 Постоянный обмен
        </TabsTrigger>
        <TabsTrigger value="temporary" className="flex items-center gap-2">
          🟠 Временный обмен
        </TabsTrigger>
      </TabsList>

      <TabsContent value="permanent">
        <PermanentTab />
      </TabsContent>

      <TabsContent value="temporary">
        <TemporaryTab />
      </TabsContent>
    </Tabs>
  );
}
```

**Task 1.2: Create Form Component (Permanent)**
```typescript
// src/components/PermanentTab.tsx

export default function PermanentTab() {
  const [items, setItems] = useState<ItemForm[]>([
    { category: '', item_name: '', value_tenge: '', description: '' }
  ]);

  const handleAddItem = () => {
    setItems([...items, { category: '', item_name: '', value_tenge: '', description: '' }]);
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Мои предметы (Постоянный обмен)</h2>

      <div className="space-y-4">
        {items.map((item, idx) => (
          <ItemFormField key={idx} item={item} onChange={(updated) => {
            const newItems = [...items];
            newItems[idx] = updated;
            setItems(newItems);
          }} />
        ))}
      </div>

      <button onClick={handleAddItem} className="mt-4 btn-primary">
        + Добавить предмет
      </button>

      <button className="mt-6 btn-success" onClick={handleSubmit}>
        🔍 Найти совпадения
      </button>
    </div>
  );
}
```

### **WEEK 2: Temporary Tab + Daily Rate Calculation**

**Task 2.1: Create Temporary Tab Component**
```typescript
// src/components/TemporaryTab.tsx

export default function TemporaryTab() {
  const [items, setItems] = useState<TemporaryItemForm[]>([
    { category: '', item_name: '', value_tenge: '', duration_days: '', description: '' }
  ]);

  const calculateDailyRate = (value: number, days: number): number => {
    if (!days || days <= 0) return 0;
    return value / days;
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Мои предметы (Временный обмен)</h2>

      <div className="space-y-6">
        {items.map((item, idx) => (
          <div key={idx} className="border rounded p-4">
            <input
              type="text"
              placeholder="Название предмета"
              value={item.item_name}
              onChange={(e) => {
                const newItems = [...items];
                newItems[idx].item_name = e.target.value;
                setItems(newItems);
              }}
              className="w-full input"
            />

            <div className="grid grid-cols-2 gap-4 mt-4">
              <input
                type="number"
                placeholder="Стоимость ₸"
                value={item.value_tenge}
                onChange={(e) => {
                  const newItems = [...items];
                  newItems[idx].value_tenge = e.target.value;
                  setItems(newItems);
                }}
              />

              <input
                type="number"
                placeholder="Дни (1-365)"
                min="1"
                max="365"
                value={item.duration_days}
                onChange={(e) => {
                  const newItems = [...items];
                  newItems[idx].duration_days = e.target.value;
                  setItems(newItems);
                }}
              />
            </div>

            {/* Auto-calculated daily rate */}
            {item.value_tenge && item.duration_days && (
              <div className="mt-2 p-3 bg-blue-100 rounded">
                <strong>Дневной тариф:</strong> {
                  calculateDailyRate(
                    Number(item.value_tenge),
                    Number(item.duration_days)
                  ).toFixed(2)
                } ₸/день
              </div>
            )}
          </div>
        ))}
      </div>

      <button className="mt-6 btn-success" onClick={handleSubmit}>
        🔍 Найти совпадения
      </button>
    </div>
  );
}
```

### **WEEK 3: API Integration + Matching Display**

**Task 3.1: Create API Service**
```typescript
// src/services/api.ts

import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export const matchingAPI = {
  // Create listing with all categories
  createListing: async (userId: number, data: ListingData) => {
    return axios.post(`${API_BASE}/listings/create-by-categories`, {
      user_id: userId,
      ...data
    });
  },

  // Find matches
  findMatches: async (userId: number, exchangeType?: string) => {
    let url = `${API_BASE}/listings/find-matches/${userId}`;
    if (exchangeType) {
      url += `?exchange_type=${exchangeType}`;
    }
    return axios.get(url);
  },

  // Filter by category
  findMatchesByCategory: async (userId: number, category: string) => {
    return axios.get(`${API_BASE}/listings/find-matches/${userId}/category/${category}`);
  }
};
```

**Task 3.2: Create Matches Display Component**
```typescript
// src/components/MatchesDisplay.tsx

export default function MatchesDisplay({ matches, onFilter }) {
  const [selectedCategory, setSelectedCategory] = useState('all');

  const getQualityColor = (score: number) => {
    if (score >= 0.85) return 'bg-green-100 border-green-400';
    if (score >= 0.70) return 'bg-yellow-100 border-yellow-400';
    return 'bg-red-100 border-red-400';
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Найденные совпадения</h2>

      {/* Category Filter */}
      <div className="flex gap-2 mb-6 flex-wrap">
        <button
          onClick={() => setSelectedCategory('all')}
          className={selectedCategory === 'all' ? 'btn-active' : 'btn'}
        >
          Все
        </button>
        {['electronics', 'furniture', 'transport', 'services', 'money', 'other'].map(cat => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={selectedCategory === cat ? 'btn-active' : 'btn'}
          >
            {getCategoryEmoji(cat)} {cat}
          </button>
        ))}
      </div>

      {/* Matches List */}
      <div className="space-y-4">
        {matches.map(match => (
          <div key={match.match_id} className={`border-l-4 p-4 rounded ${getQualityColor(match.final_score)}`}>
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-bold text-lg">{match.partner_name}</h3>
                <p className="text-sm">⭐ {match.partner_rating}/5.0 | {match.quality.toUpperCase()}</p>
                <p className="text-sm text-gray-600">📱 {match.partner_telegram}</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold">{(match.final_score * 100).toFixed(0)}%</p>
                <p className="text-sm">Score</p>
              </div>
            </div>

            {/* Matching categories */}
            <div className="mt-3">
              <p className="text-sm font-semibold">Совпадающие категории:</p>
              <div className="flex gap-2 mt-2 flex-wrap">
                {match.matching_categories.map(cat => (
                  <span key={cat} className="badge">{getCategoryEmoji(cat)} {cat}</span>
                ))}
              </div>
            </div>

            {/* Category scores */}
            <div className="mt-3 bg-white bg-opacity-50 p-2 rounded text-sm">
              {Object.entries(match.category_scores).map(([cat, score]) => (
                <div key={cat} className="flex justify-between">
                  <span>{cat}:</span>
                  <strong>{(score * 100).toFixed(0)}%</strong>
                </div>
              ))}
            </div>

            <button className="mt-4 btn-primary w-full">
              📞 Написать {match.partner_telegram}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### **WEEK 4: Notifications + Deployment**

**Task 4.1: Update Backend Notification Messages (Russian)**
```python
# backend/notifications/notification_service.py

def format_telegram_message(notification: MatchNotification) -> str:
    """Format notification message in Russian"""

    quality_emoji = {
        'excellent': '🌟',
        'good': '✨',
        'fair': '⭐',
        'poor': '👎'
    }

    emoji = quality_emoji.get(notification.match_quality, '⭐')

    categories = ', '.join(notification.matching_categories)

    message = f"""
{emoji} НОВОЕ СОВПАДЕНИЕ НАЙДЕНО!

🎯 Качество: {notification.match_quality.upper()}
📊 Оценка: {notification.match_score * 100:.0f}%

👤 Партнер: {notification.partner_name}
⭐ Рейтинг: {notification.partner_rating}/5.0
📱 Контакт: {notification.partner_telegram}

📦 Совпадающие категории:
{categories}

💡 Напишите {notification.partner_telegram} чтобы обсудить обмен!
    """
    return message.strip()
```

**Task 4.2: Deploy Locally**
```bash
# 1. Install dependencies
pip install -r backend/requirements.txt
npm install --prefix src

# 2. Configure environment
cp .env.example .env
# Edit DATABASE_URL, TELEGRAM_BOT_TOKEN, etc.

# 3. Start backend
cd backend
uvicorn main:app --reload --port 8000

# 4. Start frontend (in another terminal)
cd src
npm start

# 5. Access at: https://localhost:3000
```

---

## ✅ CHECKLIST FOR WEEK 1

**Frontend:**
- [ ] Create `src/components/ExchangeTabs.tsx`
- [ ] Create `src/components/PermanentTab.tsx`
- [ ] Create `src/components/TemporaryTab.tsx`
- [ ] Add form validation
- [ ] Test on desktop and mobile

**API:**
- [ ] Verify all endpoints from Phase 2 exist
- [ ] Add request/response logging
- [ ] Test endpoints with Postman

**Testing:**
- [ ] Unit tests for daily_rate calculation
- [ ] Integration test: form → API → database

---

## ⚡ QUICK TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| **Daily rate shows NaN** | Check `duration_days > 0` before dividing |
| **Matches not found** | Verify Phase 2 engine is running; check logs |
| **Language normalization fails** | Ensure `get_normalizer()` is called once globally |
| **Telegram notification not sent** | Check `TELEGRAM_BOT_TOKEN` is valid in `.env` |
| **CORS errors** | Verify `allow_origins` in FastAPI includes frontend URL |

---

## 📈 SUCCESS METRICS (Day 1)

✅ **By end of Week 1:**
- User can input permanent/temporary items
- Form validates correctly
- Submit button works

✅ **By end of Week 2:**
- Daily rate auto-calculates
- Data sent to backend successfully

✅ **By end of Week 3:**
- Matches retrieved from backend
- Displayed with scores and categories

✅ **By end of Week 4:**
- Telegram notifications working
- Deployed locally and accessible

---

## 🔗 HELPFUL REFERENCES

- **Phase 1 Docs:** `PHASE_1_QUICK_REFERENCE.md`
- **Phase 2 Docs:** `PHASE_2_FINAL_REPORT.md`
- **Edge Cases Analysis:** `PHASE_2_EDGE_CASES_ANALYSIS.md`
- **Full Spec:** `PHASE_3_IMPLEMENTATION_GUIDE.md`

---

**Ready to start? 🚀 Begin with Task 1.1: ExchangeTabs Component**

*Phase 3 is optimized for local Russian-language MVP — no unnecessary complexity!*
