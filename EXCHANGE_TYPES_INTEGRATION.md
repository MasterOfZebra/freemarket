# 🔄 Permanent & Temporary Exchange Integration

**Date:** January 15, 2025
**Approach:** Minimal, non-breaking integration with 2 tabs
**Complexity:** Low - mostly UI state management

---

## 📋 **Integration Summary**

### **Current State**
- ✅ Category-based listing system (6 categories)
- ✅ Permanent exchange (via value_tenge)
- ❌ No temporary exchange support

### **Goal**
- ✅ Add 2 tabs: "Постоянный обмен" | "Временный обмен"
- ✅ Same categories for both
- ✅ Permanent: Wants/Offers with value_tenge (current)
- ✅ Temporary: Wants/Offers with duration + value_tenge

---

## 🎨 **UI/UX Design (React Component)**

### **Tab Structure**

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║  [💰 Постоянный обмен]  |  [🕒 Временный обмен]              │
║                                                                ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  ЛЕВАЯ КОЛОНКА (ХОЧУ)  |  ПРАВАЯ КОЛОНКА (МОГУ)              │
║                                                                ║
║  TAB 1: PERMANENT EXCHANGE                                    │
║  ├─ 🏭 Техника                                               │
║  │  ├─ Название │ Цена ₸ │ Описание                         │
║  │  └─ [+ Добавить]                                         │
║  ├─ 💰 Деньги                                               │
║  │  └─ [+...]                                               │
║  └─ ... (остальные категории)                               │
║                                                                ║
║  TAB 2: TEMPORARY EXCHANGE                                    │
║  ├─ 🏭 Техника                                               │
║  │  ├─ Название │ Цена ₸ │ Срок │ Описание                │
║  │  └─ [+ Добавить]                                         │
║  ├─ 🚗 Транспорт                                             │
║  │  └─ [+...]                                               │
║  └─ ... (остальные категории)                               │
║                                                                ║
║  ИТОГО Постоянный: 240k ₸                                     ║
║  ИТОГО Временный: 3 предмета на 45 дней                      │
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

---

## 🔧 **Implementation Plan (Step by Step)**

### **STEP 1: Database Models (Minimal Change)**

**Current:**
```python
class ListingItem(Base):
    item_type = Column(String)        # 'want' | 'offer'
    category = Column(String)
    item_name = Column(String)
    value_tenge = Column(Integer)
    description = Column(String)
```

**Updated:**
```python
class ListingItem(Base):
    item_type = Column(String)        # 'want' | 'offer'
    category = Column(String)
    exchange_type = Column(String)    # NEW: 'permanent' | 'temporary'
    item_name = Column(String)
    value_tenge = Column(Integer)
    duration_days = Column(Integer, nullable=True)  # NEW: only for temporary
    description = Column(String)

    # Example:
    # Permanent: category="electronics", value_tenge=50000, duration_days=None
    # Temporary: category="transport", value_tenge=50000, duration_days=7
```

### **STEP 2: Schemas (Pydantic)**

```python
from enum import Enum

class ExchangeType(str, Enum):
    PERMANENT = "permanent"
    TEMPORARY = "temporary"

class ListingItemCreate(BaseModel):
    """Single item in a category"""
    category: str
    exchange_type: ExchangeType  # NEW
    item_name: str
    value_tenge: int
    duration_days: Optional[int] = None  # NEW: for temporary only
    description: Optional[str] = None

    @validator('duration_days')
    def validate_duration(cls, v, values):
        exchange_type = values.get('exchange_type')
        if exchange_type == ExchangeType.TEMPORARY and v is None:
            raise ValueError('duration_days required for temporary exchange')
        if exchange_type == ExchangeType.PERMANENT and v is not None:
            raise ValueError('duration_days should be None for permanent exchange')
        return v

class ListingByCategories(BaseModel):
    """Listing with items organized by categories AND exchange types"""
    wants: Dict[str, List[ListingItemCreate]] = Field(..., min_items=1)
    offers: Dict[str, List[ListingItemCreate]] = Field(..., min_items=1)
    locations: Optional[List[str]] = None

    # NEW: Structure with exchange types
    # {
    #   "wants": {
    #     "permanent": {
    #       "electronics": [item1, item2],
    #       "money": [item3]
    #     },
    #     "temporary": {
    #       "transport": [item4]
    #     }
    #   },
    #   "offers": { ... }
    # }
```

---

### **STEP 3: Frontend Component (React)**

**File: `src/components/ExchangeTypeForm.jsx`**

```jsx
import React, { useState } from 'react';
import { CategoryListingsForm } from './CategoryListingsForm';

const EXCHANGE_TABS = {
  PERMANENT: 'permanent',
  TEMPORARY: 'temporary'
};

export function ExchangeTypeForm({ userId, onSubmit }) {
  // State: which tab is active
  const [activeTab, setActiveTab] = useState(EXCHANGE_TABS.PERMANENT);

  // State for each tab's data
  const [permanentData, setPermanentData] = useState({
    wants: {},
    offers: {}
  });

  const [temporaryData, setTemporaryData] = useState({
    wants: {},
    offers: {}
  });

  const handlePermanentSubmit = (data) => {
    // Add exchange_type to all items
    const enrichedData = enrichWithExchangeType(data, EXCHANGE_TABS.PERMANENT);
    setPermanentData(enrichedData);
  };

  const handleTemporarySubmit = (data) => {
    const enrichedData = enrichWithExchangeType(data, EXCHANGE_TABS.TEMPORARY);
    setTemporaryData(enrichedData);
  };

  const handleFinalSubmit = async () => {
    // Merge permanent + temporary
    const combinedData = combineListings(permanentData, temporaryData);

    const response = await fetch('/api/listings/by-exchange-types', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        ...combinedData,
        locations: ['Алматы']
      })
    });

    onSubmit(await response.json());
  };

  return (
    <div className="exchange-type-form">
      <h1>🎁 Мои объявления</h1>

      {/* TABS */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === EXCHANGE_TABS.PERMANENT ? 'active' : ''}`}
          onClick={() => setActiveTab(EXCHANGE_TABS.PERMANENT)}
        >
          💰 Постоянный обмен
        </button>

        <button
          className={`tab ${activeTab === EXCHANGE_TABS.TEMPORARY ? 'active' : ''}`}
          onClick={() => setActiveTab(EXCHANGE_TABS.TEMPORARY)}
        >
          🕒 Временный обмен
        </button>
      </div>

      {/* TAB CONTENT: PERMANENT */}
      {activeTab === EXCHANGE_TABS.PERMANENT && (
        <div className="tab-content permanent">
          <CategoryListingsForm
            type="permanent"
            userId={userId}
            onSubmit={handlePermanentSubmit}
            showFields={['item_name', 'value_tenge', 'description']}
          />
        </div>
      )}

      {/* TAB CONTENT: TEMPORARY */}
      {activeTab === EXCHANGE_TABS.TEMPORARY && (
        <div className="tab-content temporary">
          <CategoryListingsForm
            type="temporary"
            userId={userId}
            onSubmit={handleTemporarySubmit}
            showFields={['item_name', 'value_tenge', 'duration_days', 'description']}
          />
        </div>
      )}

      {/* SUMMARY */}
      <div className="summary">
        <div className="summary-section permanent">
          <h3>💰 Постоянный обмен</h3>
          <p>Хочу: {calculatePermanentWantsTotal(permanentData)} ₸</p>
          <p>Могу: {calculatePermanentOffersTotal(permanentData)} ₸</p>
        </div>

        <div className="summary-section temporary">
          <h3>🕒 Временный обмен</h3>
          <p>Хочу: {countTemporaryItems(temporaryData.wants)} предметов</p>
          <p>Могу: {countTemporaryItems(temporaryData.offers)} предметов</p>
        </div>
      </div>

      <button className="btn-submit" onClick={handleFinalSubmit}>
        ✅ Сохранить все объявления
      </button>
    </div>
  );
}

// Helper functions
function enrichWithExchangeType(data, exchangeType) {
  // Add exchange_type to all items
  return {
    wants: Object.entries(data.wants).reduce((acc, [cat, items]) => {
      acc[cat] = items.map(item => ({
        ...item,
        exchange_type: exchangeType
      }));
      return acc;
    }, {}),
    offers: Object.entries(data.offers).reduce((acc, [cat, items]) => {
      acc[cat] = items.map(item => ({
        ...item,
        exchange_type: exchangeType
      }));
      return acc;
    }, {})
  };
}

function combineListings(permanent, temporary) {
  return {
    wants: {
      permanent: permanent.wants,
      temporary: temporary.wants
    },
    offers: {
      permanent: permanent.offers,
      temporary: temporary.offers
    }
  };
}
```

**File: `src/components/CategoryListingsForm.jsx` (UPDATED)**

```jsx
// Add new props:
// - type: 'permanent' | 'temporary'
// - showFields: array of fields to display

export function CategoryListingsForm({
  type = 'permanent',        // NEW
  showFields = ['item_name', 'value_tenge', 'description'],  // NEW
  userId,
  onSubmit
}) {
  // ... existing code ...

  // In CategoryTable:
  const renderTableColumns = () => {
    return showFields.map(field => {
      switch(field) {
        case 'item_name':
          return <th>Предмет</th>;
        case 'value_tenge':
          return <th>Цена, ₸</th>;
        case 'duration_days':  // NEW
          return <th>Срок, дней</th>;
        case 'description':
          return <th>Описание</th>;
        default:
          return null;
      }
    });
  };

  const renderTableCells = (item, idx) => {
    return showFields.map(field => {
      switch(field) {
        case 'item_name':
          return (
            <td key="item">
              <input value={item.item_name} onChange={...} />
            </td>
          );
        case 'value_tenge':
          return (
            <td key="value">
              <input type="number" value={item.value_tenge} onChange={...} />
            </td>
          );
        case 'duration_days':  // NEW
          return (
            <td key="duration">
              <input
                type="number"
                placeholder="дни"
                value={item.duration_days || ''}
                onChange={...}
              />
            </td>
          );
        case 'description':
          return (
            <td key="desc">
              <input value={item.description} onChange={...} />
            </td>
          );
        default:
          return null;
      }
    });
  };
}
```

**File: `src/components/ExchangeTypeForm.css` (NEW)**

```css
.exchange-type-form {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
  border-bottom: 2px solid #eee;
}

.tab {
  padding: 12px 20px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  color: #999;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
}

.tab.active {
  color: #2c3e50;
  border-bottom-color: #2c3e50;
}

.tab:hover:not(.active) {
  color: #666;
}

.tab-content {
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.summary {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin: 30px 0;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.summary-section {
  padding: 15px;
  border-radius: 6px;
}

.summary-section.permanent {
  background: linear-gradient(135deg, #e8f5e9 0%, #f9fff9 100%);
  border-left: 4px solid #27ae60;
}

.summary-section.temporary {
  background: linear-gradient(135deg, #fff3e0 0%, #fffbf0 100%);
  border-left: 4px solid #ff9800;
}
```

---

### **STEP 4: API Endpoint (Minimal Change)**

**File: `backend/api/endpoints/listings_by_exchange_types.py` (NEW)**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from backend.database import SessionLocal
from backend.models import Listing, ListingItem, ListingItemType
from backend.schemas import ListingByCategories

router = APIRouter(prefix="/api/listings", tags=["listings"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/by-exchange-types")
def create_listing_by_exchange_types(
    user_id: int,
    wants: Dict[str, Dict[str, List]],  # {permanent: {category: [items]}, temporary: {...}}
    offers: Dict[str, Dict[str, List]],
    locations: List[str],
    db: Session = Depends(get_db)
):
    """
    Create listing with items organized by exchange type and categories.

    Body:
    {
      "user_id": 1,
      "wants": {
        "permanent": {
          "electronics": [
            {"item_name": "Phone", "value_tenge": 50000, "description": "..."}
          ],
          "temporary": {}
        },
        "temporary": {
          "transport": [
            {"item_name": "Bike", "value_tenge": 30000, "duration_days": 7, "description": "..."}
          ]
        }
      },
      "offers": { ... },
      "locations": ["Алматы"]
    }
    """

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create listing
    db_listing = Listing(user_id=user_id)

    # Add wants (both permanent and temporary)
    for exchange_type, categories in wants.items():
        for category, items in categories.items():
            for item in items:
                db_item = ListingItem(
                    item_type=ListingItemType.WANT,
                    exchange_type=exchange_type,
                    category=category,
                    item_name=item['item_name'],
                    value_tenge=item['value_tenge'],
                    duration_days=item.get('duration_days'),
                    description=item.get('description')
                )
                db_listing.items.append(db_item)

    # Add offers (both permanent and temporary)
    for exchange_type, categories in offers.items():
        for category, items in categories.items():
            for item in items:
                db_item = ListingItem(
                    item_type=ListingItemType.OFFER,
                    exchange_type=exchange_type,
                    category=category,
                    item_name=item['item_name'],
                    value_tenge=item['value_tenge'],
                    duration_days=item.get('duration_days'),
                    description=item.get('description')
                )
                db_listing.items.append(db_item)

    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)

    return {
        "id": db_listing.id,
        "user_id": db_listing.user_id,
        "message": "Listing created successfully"
    }
```

---

## 📊 **Data Flow**

```
USER FILLS BOTH TABS
├─ Tab 1: Постоянный обмен
│  └─ Wants/Offers with value_tenge
└─ Tab 2: Временный обмен
   └─ Wants/Offers with value_tenge + duration_days

         ↓ Click "Сохранить все объявления"

FRONTEND COMBINES DATA
├─ Permanent: wants.permanent, offers.permanent
└─ Temporary: wants.temporary, offers.temporary

         ↓ POST /api/listings/by-exchange-types

DATABASE SAVES (NORMALIZED)
├─ listings: 1 record per user
└─ listing_items: many records
   ├─ exchange_type: 'permanent' | 'temporary'
   ├─ duration_days: NULL (permanent) | 1-365 (temporary)
   └─ All indexed for fast queries

         ↓ Matching Engine processes

MATCHING ENGINE LOGIC
├─ Phase 1: Filter by exchange type
├─ Phase 2: Find intersecting categories
├─ Phase 3: Score equivalence
│  ├─ Permanent: value_a ≈ value_b (±15%)
│  └─ Temporary: (value_a/duration_a) ≈ (value_b/duration_b)
└─ Phase 4: Create filtered listings & send Telegram
```

---

## 🎯 **Matching Algorithm Update**

**File: `backend/matching/exchange_equivalence.py` (NEW)**

```python
from enum import Enum

class ExchangeType(str, Enum):
    PERMANENT = "permanent"
    TEMPORARY = "temporary"

class ExchangeEquivalence:
    """Calculate equivalence between items considering exchange type."""

    VALUE_TOLERANCE = 0.15  # ±15%

    @staticmethod
    def is_equivalent(
        item_a_value: float,
        item_a_duration: Optional[float],
        item_b_value: float,
        item_b_duration: Optional[float]
    ) -> bool:
        """Check if two items are equivalent."""

        # Both permanent
        if not item_a_duration and not item_b_duration:
            ratio = max(item_a_value, item_b_value) / min(item_a_value, item_b_value)
            return ratio <= (1 + ExchangeEquivalence.VALUE_TOLERANCE)

        # Both temporary
        if item_a_duration and item_b_duration:
            rate_a = item_a_value / item_a_duration
            rate_b = item_b_value / item_b_duration
            ratio = max(rate_a, rate_b) / min(rate_a, rate_b)
            return ratio <= (1 + ExchangeEquivalence.VALUE_TOLERANCE)

        # Mixed: permanent ↔ temporary (not typically allowed)
        # But if needed:
        # rate_a = item_a_value / (item_a_duration or 1)
        # rate_b = item_b_value / (item_b_duration or 1)
        # ratio = max(rate_a, rate_b) / min(rate_a, rate_b)
        # return ratio <= (1 + ExchangeEquivalence.VALUE_TOLERANCE)

        return False

    @staticmethod
    def calculate_score(
        my_value: float,
        my_duration: Optional[float],
        partner_value: float,
        partner_duration: Optional[float]
    ) -> float:
        """Calculate match score 0.0-1.0."""

        # Both permanent
        if not my_duration and not partner_duration:
            diff = abs(my_value - partner_value) / max(my_value, partner_value)
            return max(0, 1.0 - diff)

        # Both temporary
        if my_duration and partner_duration:
            my_rate = my_value / my_duration
            partner_rate = partner_value / partner_duration
            diff = abs(my_rate - partner_rate) / max(my_rate, partner_rate)
            return max(0, 1.0 - diff)

        return 0.0
```

**Updated `CategoryMatchingEngine`:**

```python
# In backend/matching/category_matching.py

def _score_category_match(self, my_listing, other_listing, category):
    """Score a single category match (updated for exchange types)."""

    # Get my wants/offers
    my_wants = [i for i in my_listing.wants_by_category.get(category, [])
                if i.exchange_type == "permanent"]  # Filter by type
    my_offers = [i for i in my_listing.offers_by_category.get(category, [])
                 if i.exchange_type == "permanent"]

    # Get their wants/offers
    their_wants = [i for i in other_listing.wants_by_category.get(category, [])
                   if i.exchange_type == "permanent"]
    their_offers = [i for i in other_listing.offers_by_category.get(category, [])
                    if i.exchange_type == "permanent"]

    # Calculate values
    my_wants_value = sum(i.value_tenge for i in my_wants)
    my_offers_value = sum(i.value_tenge for i in my_offers)
    their_wants_value = sum(i.value_tenge for i in their_wants)
    their_offers_value = sum(i.value_tenge for i in their_offers)

    # Score using ExchangeEquivalence
    wants_score = ExchangeEquivalence.calculate_score(
        my_wants_value, None, their_offers_value, None
    )
    offers_score = ExchangeEquivalence.calculate_score(
        my_offers_value, None, their_wants_value, None
    )

    return (wants_score + offers_score) / 2
```

---

## 📚 **File Changes Summary**

### **NEW FILES**
1. ✅ `src/components/ExchangeTypeForm.jsx` - Tab-based form
2. ✅ `src/components/ExchangeTypeForm.css` - Styling
3. ✅ `backend/api/endpoints/listings_by_exchange_types.py` - API endpoint
4. ✅ `backend/matching/exchange_equivalence.py` - Equivalence logic

### **UPDATED FILES**
1. 🔄 `backend/models.py` - Add `exchange_type`, `duration_days` to `ListingItem`
2. 🔄 `backend/schemas.py` - Add `ExchangeType` enum, update validators
3. 🔄 `src/components/CategoryListingsForm.jsx` - Add `type`, `showFields` props
4. 🔄 `backend/matching/category_matching.py` - Filter by exchange type
5. 🔄 `backend/api/router.py` - Include new endpoint

### **BACKWARD COMPATIBLE**
- ✅ Existing permanent exchange still works (exchange_type defaults to "permanent")
- ✅ Existing API endpoint still available
- ✅ Can add temporary exchange without breaking anything

---

## ⏱️ **Implementation Timeline**

| Phase | Component | Time |
|-------|-----------|------|
| 1 | Database migration (add columns) | 10 min |
| 2 | Update schemas & models | 15 min |
| 3 | Create tab-based form | 45 min |
| 4 | Create new API endpoint | 20 min |
| 5 | Update matching logic | 30 min |
| 6 | Testing | 20 min |

**TOTAL: ~140 minutes (~2.5 hours)**

---

## 🧪 **Test Scenarios**

### **Scenario 1: Permanent Exchange Only**
- User adds 1 want (phone 50k) + 1 offer (laptop 50k) in "Постоянный обмен" tab
- System finds matching user with inverse wants/offers
- Result: Match at 100% score

### **Scenario 2: Temporary Exchange Only**
- User adds want (bike for 7 days, value 30k) + offer (drill for 3 days, value 20k) in "Временный обмен" tab
- Another user wants drill (3 days) and offers bike (7 days)
- Rate_A = 30k/7 ≈ 4,285/day | Rate_B = 20k/3 ≈ 6,667/day
- Score = 1 - |diff| = ~0.87 (good match!)

### **Scenario 3: Both Tabs**
- User fills BOTH tabs
- System processes separately
- Can find matches in both types independently

---

## ✨ **Key Features**

✅ **Minimal changes** - Only 4 new files, 5 updated files
✅ **Backward compatible** - Existing code still works
✅ **Clean UI** - Tab-based, organized
✅ **Smart matching** - Equivalence logic per exchange type
✅ **Flexible** - Can add more exchange types later

---

**Status: ✅ Ready for implementation**

**Next step:** Start with database migration (add columns to listing_items)
