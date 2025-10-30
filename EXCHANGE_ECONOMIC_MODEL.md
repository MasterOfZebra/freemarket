# 💰 Unified Economic Exchange Model

**Version:** 1.0 - Complete Economic Framework
**Date:** January 15, 2025
**Status:** ✅ Ready for Implementation

---

## 🎯 **Core Concept**

A **single economic model** where every asset can be exchanged based on its **equivalent value form**:

| Exchange Type | Equivalence Measure | Mechanism | Return Policy |
|---------------|-------------------|-----------|----------------|
| **Permanent** | Monetary/Market Value (₸) | Swap equal values | No return |
| **Temporary** | Time-Based Rate (₸/day) | Rent equivalent duration | Return after deadline |

---

## 📐 **Mathematical Framework**

### **Permanent Exchange**

```
Equivalence Rule:
  Item_A.value ≈ Item_B.value  (within ±15%)

Example:
  Alice: Phone (50k) + Laptop (100k) = 150k ₸ offers
  Bob:   Tablet (80k) + Headset (70k) = 150k ₸ wants

  Result: ✅ MATCH (150k ≈ 150k)
```

### **Temporary Exchange**

```
Equivalence Rule:
  (Item_A.value / Item_A.duration) ≈ (Item_B.value / Item_B.duration)

  aka: Daily_Rate_A ≈ Daily_Rate_B

Example:
  Alice: Bike (30k, 7 days) → daily rate = 30k/7 ≈ 4,286 ₸/day
  Bob:   Drill (21k, 5 days) → daily rate = 21k/5 ≈ 4,200 ₸/day

  Result: ✅ MATCH (4,286 ≈ 4,200, diff = 2%)
```

### **Mixed Exchange** (if needed)

```
Equivalence Rule:
  value_permanent / base_unit ≈ value_temporary / duration_days

Use Cases:
  - Pay money for item rental
  - Lend item for service
  - Deposit for equipment rental
```

---

## 🏷️ **Category System**

Both exchange types use **same 6 categories**, but with different **duration considerations**.

### **🕒 TEMPORARY EXCHANGE (Duration-Based, Return Policy)**

Items where **time of possession** is the equivalent value.

**Transport & Mobility**
- 🚴 Bicycles, scooters, e-bikes
- 🛹 Skateboard, hoverboards
- 🏍️ Mopeds, motorcycles
- Duration: 1-30 days typically

**Tools & Equipment**
- 🔧 Hand tools, power tools
- 🎥 Camera equipment, drones
- 🎤 Audio/video gear
- Duration: 1-14 days typically

**Sports & Recreation**
- ⛷️ Skis, snowboards, camping gear
- 🎾 Sports equipment, instruments
- 🎮 Consoles, VR headsets
- Duration: 1-30 days typically

**Clothing & Accessories**
- 👗 Formal wear, costumes
- 👜 Designer bags, jewelry (events)
- Duration: 1-7 days typically

**Digital & Services**
- 📱 Software licenses, subscriptions
- 🎓 Tutoring, consulting (hourly/daily)
- 💾 Cloud storage, API access
- Duration: 1-365 days or hourly

**Other Rentables**
- 📚 Books, games (1-7 days)
- 🛋️ Large furniture for events
- 🎪 Party/event equipment

---

### **💰 PERMANENT EXCHANGE (Value-Based, No Return)**

Items where **ownership** transfers permanently.

**Transportation**
- 🚗 Cars, motorcycles, trucks
- 🛴 Scooters (bought)
- ⚙️ Spare parts

**Real Estate**
- 🏠 Apartments, houses
- 🏡 Land, plots
- 🏢 Commercial space

**Electronics & Tech**
- 📱 Phones, tablets
- 💻 Laptops, desktops
- 🖥️ Monitors, peripherals
- 📺 TVs, speakers

**Furniture & Household**
- 🛋️ Sofa, bed, chairs
- 🪟 Kitchen appliances
- 🛁 Bathroom fixtures
- 🧻 Textiles, decor

**Valuables & Collections**
- 🖼️ Art, antiques
- 💍 Jewelry, watches
- 📖 Books, collectibles

**Finances & Digital**
- 💵 Cash, money
- 🪙 Cryptocurrency
- 📄 Securities, bonds
- 🎟️ Tokens, access rights

**Living Beings**
- 🐕 Pets (full responsibility transfer)
- 🌱 Plants (rare/valuable)

**Clothing & Personal**
- 👕 Everyday clothes
- 👠 Shoes, accessories

---

## 🔄 **Exchange Flow Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│              USER CREATES LISTINGS (2 TABS)                │
└─────────────────────────────────────────────────────────────┘

TAB 1: PERMANENT EXCHANGE (💰)
├─ Wants: What I want to GET (no return)
│  └─ Example: Phone 50k, Laptop 100k
└─ Offers: What I can GIVE (no return)
   └─ Example: Bike 50k, Keyboard 50k

TAB 2: TEMPORARY EXCHANGE (🕒)
├─ Wants: What I want to BORROW (return later)
│  └─ Example: Bike for 7 days (value 30k)
└─ Offers: What I can LEND (get back later)
   └─ Example: Drill for 3 days (value 21k)

                    ↓ SUBMIT

┌─────────────────────────────────────────────────────────────┐
│         DATABASE STORES (NORMALIZED)                        │
└─────────────────────────────────────────────────────────────┘

ListingItem records:
├─ item_type: 'want' | 'offer'
├─ exchange_type: 'permanent' | 'temporary'
├─ category: 'electronics', 'transport', etc.
├─ value_tenge: 30000-1000000 ₸
├─ duration_days: NULL (perm) | 1-365 (temp)
└─ description: optional details

                    ↓ PROCESS

┌─────────────────────────────────────────────────────────────┐
│        MATCHING ENGINE EVALUATES                            │
└─────────────────────────────────────────────────────────────┘

PERMANENT MATCHES:
├─ Find category intersections
├─ Sum values: my_wants.total ≈ partner.offers.total?
├─ Score: 1 - |diff| / max(values)
└─ If score >= 0.70 → MATCH!

TEMPORARY MATCHES:
├─ Find category intersections
├─ Calculate daily rates
├─ Rate_A = value_A / duration_A
├─ Rate_B = value_B / duration_B
├─ Score: 1 - |rate_diff| / max(rates)
└─ If score >= 0.70 → MATCH!

                    ↓ NOTIFY

┌─────────────────────────────────────────────────────────────┐
│          TELEGRAM NOTIFICATION SENT                         │
└─────────────────────────────────────────────────────────────┘

PERMANENT MATCH:
📦 You found a permanent exchange partner!
├─ Partner wants: Phone (50k) ← You can give!
├─ Partner offers: Bike (50k) ← You want!
└─ Score: 100%

TEMPORARY MATCH:
🔄 You found a rental exchange partner!
├─ Partner wants: Bike (30k for 7 days) ← You can lend!
├─ Partner offers: Drill (21k for 3 days) ← You want to borrow!
└─ Daily rate match: 85%
```

---

## 🧮 **Scoring Formula**

### **Permanent Exchange Scoring**

```python
def score_permanent_match(my_value, partner_value):
    if my_value == 0 or partner_value == 0:
        return 0.0

    diff_ratio = abs(my_value - partner_value) / max(my_value, partner_value)

    score = 1.0 - diff_ratio
    return max(0, min(score, 1.0))  # 0.0-1.0

# Examples:
# 50k vs 50k:     diff_ratio = 0,     score = 1.00 (perfect!)
# 50k vs 55k:     diff_ratio = 0.10,  score = 0.90 (great!)
# 50k vs 65k:     diff_ratio = 0.30,  score = 0.70 (acceptable)
# 50k vs 80k:     diff_ratio = 0.60,  score = 0.40 (no match)
```

### **Temporary Exchange Scoring**

```python
def score_temporary_match(my_value, my_duration, partner_value, partner_duration):
    if my_duration == 0 or partner_duration == 0:
        return 0.0

    my_rate = my_value / my_duration
    partner_rate = partner_value / partner_duration

    rate_diff = abs(my_rate - partner_rate) / max(my_rate, partner_rate)

    score = 1.0 - rate_diff
    return max(0, min(score, 1.0))  # 0.0-1.0

# Examples:
# A: 30k/7d=4286/d vs B: 30k/7d=4286/d        score = 1.00
# A: 30k/7d=4286/d vs B: 21k/5d=4200/d        score = 0.98
# A: 50k/10d=5000/d vs B: 30k/7d=4286/d       score = 0.86
# A: 50k/10d=5000/d vs B: 40k/20d=2000/d      score = 0.60
```

---

## 🎁 **Real-World Examples**

### **Example 1: Permanent Exchange (Perfect Match)**

```
ALICE'S PROFILE
└─ Wants:
   ├─ Tablet: 100k ₸
   └─ Keyboard: 50k ₸
   └─ TOTAL: 150k ₸

BOB'S PROFILE
└─ Offers:
   ├─ Laptop: 100k ₸
   └─ Mouse: 50k ₸
   └─ TOTAL: 150k ₸

RESULT:
✅ Match found! (150k = 150k)
   Alice gets: Laptop + Mouse
   Bob gets: Tablet + Keyboard
```

### **Example 2: Temporary Exchange (Good Match)**

```
ALICE'S PROFILE (Wants to BORROW)
└─ Bike for 7 days
   └─ Estimated value: 30,000 ₸
   └─ Daily rate: 30k/7 ≈ 4,286 ₸/day

BOB'S PROFILE (Wants to LEND)
└─ Power drill for 5 days
   └─ Estimated value: 21,000 ₸
   └─ Daily rate: 21k/5 ≈ 4,200 ₸/day

RESULT:
✅ Match! (4,286 ≈ 4,200, difference = 2%)
   Alice borrows: Drill (5 days)
   Bob borrows: Bike (7 days)
   When Alice returns drill, she still owes 2 days of bike use
   → Settlement: Alice adds 2 days OR small cash adjustment
```

### **Example 3: Multi-Category Match**

```
ALICE'S PERMANENT WANTS:
├─ Electronics: Phone (50k)
├─ Transport: Bike (30k)
└─ Furniture: Chair (20k)
└─ TOTAL: 100k ₸

BOB'S PERMANENT OFFERS:
├─ Electronics: Headset (50k)
├─ Transport: Scooter (30k)
└─ Furniture: Table (20k)
└─ TOTAL: 100k ₸

RESULT:
✅ Perfect multi-category match!
   ├─ Electronics match: 50k = 50k (100%)
   ├─ Transport match: 30k = 30k (100%)
   └─ Furniture match: 20k = 20k (100%)
```

### **Example 4: Temporary + Permanent Mixed**

```
ALICE'S PROFILE
├─ Wants PERMANENT: Camera (200k) → for ownership
└─ Wants TEMPORARY: Tripod for 2 weeks (value 5k)

BOB'S PROFILE
├─ Offers PERMANENT: Lens (50k)
└─ Offers TEMPORARY: Camera for 3 weeks (value 80k)

MATCHING:
❌ Permanent: 200k ≠ 50k (no match)
✅ Temporary: 5k for 14 days vs 80k for 21 days
   → Daily rates: 357 ₸/day vs 3,810 ₸/day (no match)

RESULT: ❌ No match found (different exchange types)
```

---

## 🔐 **Contract Semantics**

### **Permanent Exchange Contract**

```
AGREEMENT: Permanent Exchange

Parties:
- Alice (User A)
- Bob (User B)

Terms:
- Alice GIVES: [listed items] with total value 100,000 ₸
- Bob GIVES: [listed items] with total value 100,000 ₸

Conditions:
- Exchange is FINAL (no returns)
- Items must be in described condition
- Transfer happens in-person (location-based)
- No disputes after 7 days

Execution:
[Signature] [Date] [Location]
```

### **Temporary Exchange Contract**

```
AGREEMENT: Temporary Exchange (Rental)

Parties:
- Alice (Borrower)
- Bob (Lender)

Items:
- Bike (estimated value 30,000 ₸)
- Duration: 7 days
- Condition: Used, but functional

Terms:
- Alice BORROWS bike from [date] to [date]
- Bob BORROWS drill from [same date] to [same date + 3 days]
- Return condition: Same as given (normal wear acceptable)
- Damage/loss: Equivalent payment required

Return:
- Bike returned to: [location]
- On: [date]
- Inspected by: Both parties

Execution:
[Signature] [Date] [Location]
```

---

## 🎨 **UI/UX - Tab-Based System**

```
┌────────────────────────────────────────────────────────┐
│  [💰 Постоянный обмен]  |  [🕒 Временный обмен]      │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ХОЧ У (Wants)            │  МОГУ (Offers)           │
│                                                        │
│  🏭 ТЕХНИКА               │  🏭 ТЕХНИКА              │
│  ├─ Телефон: 50k          │  ├─ Смартфон: 50k       │
│  ├─ Цена: 50000 ₸         │  ├─ Цена: 50000 ₸       │
│  └─ Описание: iPhone       │  └─ Описание: Samsung   │
│                                                        │
│  [+ Добавить]            │  [+ Добавить]            │
│  ИТОГО: 50k ₸            │  ИТОГО: 50k ₸            │
│                                                        │
│  [✅ Сохранить]                                       │
│                                                        │
└────────────────────────────────────────────────────────┘

TEMPORARY TAB VARIANT:
├─ Название: Велосипед
├─ Цена: 30000 ₸
├─ СРОК: 7 дней          ← UNIQUE FIELD
└─ Описание: Mountain bike
```

---

## 📊 **Database Schema**

```sql
-- Core tables remain the same
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR UNIQUE,
  contact VARCHAR,
  locations ARRAY VARCHAR
);

CREATE TABLE listings (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  created_at TIMESTAMP
);

-- UPDATED: Add exchange_type and duration_days
CREATE TABLE listing_items (
  id SERIAL PRIMARY KEY,
  listing_id INTEGER REFERENCES listings(id),
  item_type VARCHAR,           -- 'want' | 'offer'
  exchange_type VARCHAR,       -- 'permanent' | 'temporary' ← NEW
  category VARCHAR,            -- 'electronics', 'transport', etc.
  item_name VARCHAR(100),
  value_tenge INTEGER,
  duration_days INTEGER,       -- NULL for permanent, 1-365 for temporary ← NEW
  description TEXT,
  created_at TIMESTAMP,

  INDEX (listing_id, exchange_type),  ← NEW INDEX
  INDEX (exchange_type, category)     ← NEW INDEX
);

CREATE TABLE matches (
  id SERIAL PRIMARY KEY,
  user_a_id INTEGER,
  user_b_id INTEGER,
  exchange_type VARCHAR,           -- 'permanent' | 'temporary' ← NEW
  matching_categories JSON,
  category_scores JSON,
  overall_score FLOAT,
  created_at TIMESTAMP
);
```

---

## 🚀 **Implementation Phases**

### **Phase 1: Database Layer** (10 min)
- [ ] Add `exchange_type` column to `listing_items`
- [ ] Add `duration_days` column to `listing_items`
- [ ] Create indexes

### **Phase 2: Backend Models & Schemas** (15 min)
- [ ] Add `ExchangeType` enum
- [ ] Update `ListingItem` model
- [ ] Update Pydantic schemas with validators

### **Phase 3: Frontend UI** (45 min)
- [ ] Create `ExchangeTypeForm.jsx` (tab wrapper)
- [ ] Update `CategoryListingsForm.jsx` (add duration field)
- [ ] Add CSS for tabs and temporary-specific UI

### **Phase 4: API Layer** (20 min)
- [ ] Create `/api/listings/by-exchange-types` endpoint
- [ ] Add data processing for both exchange types

### **Phase 5: Matching Engine** (30 min)
- [ ] Create `exchange_equivalence.py` (scoring logic)
- [ ] Update `CategoryMatchingEngine` to filter by exchange type
- [ ] Add dual-rate calculation for temporary exchanges

### **Phase 6: Testing** (20 min)
- [ ] Test permanent exchange matching
- [ ] Test temporary exchange matching
- [ ] Test rate calculations

**TOTAL: ~2.5 hours**

---

## ✅ **Validation Rules**

### **Permanent Exchange**
- ✅ `value_tenge` must be > 0
- ✅ `duration_days` must be NULL
- ✅ Category can be any of 6 categories
- ✅ Can swap any permanent items

### **Temporary Exchange**
- ✅ `value_tenge` must be > 0
- ✅ `duration_days` must be 1-365
- ✅ Category must support rentals (transport, tools, sports, etc.)
- ✅ Cannot rent permanent items (cars, real estate, etc.)

### **Mixed Validation**
- ❌ Cannot mix permanent & temporary in same match
- ✅ User can have both types in same listing
- ✅ Matching is separate for each type

---

## 🎯 **Success Metrics**

| Metric | Target | How to Measure |
|--------|--------|-----------------|
| Permanent match accuracy | >90% | Users confirm exchange |
| Temporary match accuracy | >85% | Daily rate diff < 5% |
| User satisfaction | >4.0/5 | Post-exchange survey |
| Match finding speed | <500ms | API response time |
| Exchange completion rate | >70% | Exchanges completed / found |

---

**Status: ✅ Complete Economic Model Ready**

This is a **unified, mathematically sound** model that handles both permanent ownership transfers and temporary time-based exchanges using a single equivalence framework.

Ready to implement! 🚀
