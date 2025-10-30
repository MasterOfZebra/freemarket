# 🎨 UI/UX Design Specification - Two Exchange Tabs

**Design System:** Material Design 3
**Version:** 1.0
**Date:** January 15, 2025
**Status:** ✅ Ready for Implementation

---

## 📋 **Core Design Concept**

Two **completely separate tools** (tabs), each with:
- ✅ Own database (permanent items vs temporary items)
- ✅ Own matching logic (value-based vs duration-based)
- ✅ Own notification flow
- ✅ Own wants/offers pairs
- ❌ No mixing between tabs

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│        TOOL 1: PERMANENT EXCHANGE                         │
│        💰 "Постоянный обмен"                              │
│        (Value-based, ownership transfer)                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│        vs                                                   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│        TOOL 2: TEMPORARY EXCHANGE                         │
│        🕒 "Временный обмен"                               │
│        (Duration-based, return policy)                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 **Visual Layout**

### **Main Navigation Bar**

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  FreeMarket    [Home] [Profile] [Cabinet]     [Menu]        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### **Tab Switcher (Below Navigation)**

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  📦 Мои объявления                                           │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  [💰 Постоянный обмен]  |  [🕒 Временный обмен]       ││
│  │  ═══════════════════════════════════════════════════════││
│  │                                                          ││
│  │  Active tab indicator (underline animation)             ││
│  │                                                          ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 💰 **TAB 1: PERMANENT EXCHANGE (Постоянный обмен)**

### **Purpose**
- Swap **ownership** of items permanently
- Equivalence via **monetary value** (₸)
- No return policy
- Suitable categories: Electronics, Vehicles, Real Estate, Money, etc.

### **Layout Structure**

```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║  💰 ПОСТОЯННЫЙ ОБМЕН (Permanent Exchange)                ║
║  ═══════════════════════════════════════════════════════  ║
║                                                            ║
║  "Обмен собственностью на постоянной основе"            ║
║  "Exchange ownership permanently"                        ║
║                                                            ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  ┌─────────────────────────┬─────────────────────────┐   ║
║  │  ❌ ХОЧ У (Wants)       │  ✅ МОГУ (Offers)      │   ║
║  │  (Хочу получить)        │  (Могу предложить)     │   ║
║  │═════════════════════════╪═════════════════════════│   ║
║  │                         │                         │   ║
║  │ 🏭 ТЕХНИКА              │ 🏭 ТЕХНИКА             │   ║
║  │ ┌───────────────────┐   │ ┌───────────────────┐  │   ║
║  │ │Предмет  │Цена  ₸ │   │ │Предмет  │Цена  ₸ │  │   ║
║  │ ├─────────┼─────────┤   │ ├─────────┼─────────┤  │   ║
║  │ │Телефон  │50000   │   │ │Ноутбук  │100000 │  │   ║
║  │ │Монитор  │30000   │   │ │Мышка    │10000  │  │   ║
║  │ ├─────────┴─────────┤   │ ├─────────┴─────────┤  │   ║
║  │ │[+ Добавить]      │   │ │[+ Добавить]      │  │   ║
║  │ │Итого: 80,000 ₸   │   │ │Итого: 110,000 ₸  │  │   ║
║  │ └───────────────────┘   │ └───────────────────┘  │   ║
║  │                         │                         │   ║
║  │ 💰 ДЕНЬГИ               │ 💰 ДЕНЬГИ              │   ║
║  │ ┌───────────────────┐   │ ┌───────────────────┐  │   ║
║  │ │Помощь с аренда   │   │ │Может помочь с    │  │   ║
║  │ │100,000 ₸         │   │ │ремонтом, 80k ₸  │  │   ║
║  │ ├─────────────────┬─┤   │ ├──────────────────┤  │   ║
║  │ │[+ Добавить]    │ │   │ │[+ Добавить]     │  │   ║
║  │ │Итого: 100k ₸   │ │   │ │Итого: 80k ₸     │  │   ║
║  │ └───────────────────┘   │ └───────────────────┘  │   ║
║  │                         │                         │   ║
║  │ 🛋️ МЕБЕЛЬ               │ 🛋️ МЕБЕЛЬ             │   ║
║  │ ┌───────────────────┐   │ ┌───────────────────┐  │   ║
║  │ │Стол (офисный)    │   │ │Шкаф (гардероб)  │  │   ║
║  │ │20,000 ₸         │   │ │35,000 ₸        │  │   ║
║  │ ├──────────────────┤   │ ├──────────────────┤  │   ║
║  │ │[+ Добавить]     │   │ │[+ Добавить]     │  │   ║
║  │ │Итого: 20k ₸     │   │ │Итого: 35k ₸     │  │   ║
║  │ └───────────────────┘   │ └───────────────────┘  │   ║
║  │                         │                         │   ║
║  └─────────────────────────┴─────────────────────────┘   ║
║                                                            ║
║  ┌──────────────────────────────────────────────────────┐ ║
║  │ ИТОГОВАЯ СТАТИСТИКА                                 │ ║
║  ├──────────────────────────────────────────────────────┤ ║
║  │ Хочу получить:  200,000 ₸  |  Могу дать: 225,000 ₸ │ ║
║  │                                                       │ ║
║  │ Баланс: ✅ Переплачу на 25,000 ₸                   │ ║
║  │ (Я могу добавить что-то ещё в wants)               │ ║
║  └──────────────────────────────────────────────────────┘ ║
║                                                            ║
║  ┌──────────────────────────────────────────────────────┐ ║
║  │ [🔍 Найти совпадения]  [💾 Сохранить как черновик] │ ║
║  └──────────────────────────────────────────────────────┘ ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### **Category Section Details (Expandable)**

```
┌─────────────────────────────────────────┐
│ 🏭 ТЕХНИКА (Electronics)               │
├─────────────────────────────────────────┤
│                                         │
│ Таблица предметов:                      │
│                                         │
│ ┌──────────┬──────────┬──────────┐     │
│ │ Предмет  │ Цена ₸  │ Действие │     │
│ ├──────────┼──────────┼──────────┤     │
│ │ Телефон  │ 50,000  │   [✕]    │     │
│ ├──────────┼──────────┼──────────┤     │
│ │ Монитор  │ 30,000  │   [✕]    │     │
│ ├──────────┼──────────┼──────────┤     │
│ │ [новая]  │   -     │   [✕]    │     │
│ └──────────┴──────────┴──────────┘     │
│                                         │
│ Footer:                                 │
│ [+ Добавить]    Итого: 80,000 ₸      │
│ [Свернуть ▲]                           │
└─────────────────────────────────────────┘
```

### **Item Input Form (Modal or Inline)**

```
┌────────────────────────────────────────────┐
│ ➕ Добавить предмет в ТЕХНИКА             │
├────────────────────────────────────────────┤
│                                            │
│ Предмет:                                   │
│ ┌──────────────────────────────────────┐  │
│ │ [Введите название]                   │  │
│ └──────────────────────────────────────┘  │
│                                            │
│ Цена (в тенге):                           │
│ ┌──────────────────────────────────────┐  │
│ │ [50000]                    ₸        │  │
│ └──────────────────────────────────────┘  │
│                                            │
│ Описание (опционально):                    │
│ ┌──────────────────────────────────────┐  │
│ │ [Описание состояния, модели, и.т.д] │  │
│ └──────────────────────────────────────┘  │
│                                            │
│ [Отмена]  [✅ Добавить]                  │
│                                            │
└────────────────────────────────────────────┘
```

---

## 🕒 **TAB 2: TEMPORARY EXCHANGE (Временный обмен)**

### **Purpose**
- **Borrow/Lend** items with return deadline
- Equivalence via **daily rate** (₸/day)
- Return policy enforced
- Suitable categories: Transport, Tools, Sports, Digital Services, etc.

### **Layout Structure**

```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║  🕒 ВРЕМЕННЫЙ ОБМЕН (Temporary Exchange)                 ║
║  ═══════════════════════════════════════════════════════  ║
║                                                            ║
║  "Обмен с возвратом в определённый срок"               ║
║  "Exchange with return by deadline"                     ║
║                                                            ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  ┌─────────────────────────┬─────────────────────────┐   ║
║  │  ❌ ХОЧУ ВЗЯТЬ (Wants)  │  ✅ МОГУ ДАТЬ (Offers) │   ║
║  │  (Хочу одолжить)        │  (Могу одолжить)       │   ║
║  │═════════════════════════╪═════════════════════════│   ║
║  │                         │                         │   ║
║  │ 🚗 ТРАНСПОРТ            │ 🚗 ТРАНСПОРТ           │   ║
║  │ ┌──────────────────────┐│ ┌──────────────────────┐│   ║
║  │ │Пред │Цена ₸│Срок дн││Пред │Цена ₸│Срок дн ││   ║
║  │ ├─────┼──────┼────────┤│├─────┼──────┼────────┤│   ║
║  │ │Вело │30000 │ 7     │││Дрель│21000 │ 5     ││   ║
║  │ │     │      │ дней  │││     │      │ дней  ││   ║
║  │ │     │      │/4286  │││     │      │/4200  ││   ║
║  │ │     │      │₸/день │││     │      │₸/день ││   ║
║  │ ├─────┴──────┴────────┤│├─────┴──────┴────────┤│   ║
║  │ │[+ Добавить]        ││[+ Добавить]         ││   ║
║  │ │Итого: 30k₸ на 7дн  ││Итого: 21k₸ на 5дн   ││   ║
║  │ │Ставка: 4286/день   ││Ставка: 4200/день    ││   ║
║  │ └──────────────────────┘│└──────────────────────┘│   ║
║  │                         │                         │   ║
║  │ 🔧 ИНСТРУМЕНТЫ          │ 🔧 ИНСТРУМЕНТЫ        │   ║
║  │ ┌──────────────────────┐│ ┌──────────────────────┐│   ║
║  │ │Лестница│10k │3 дня  │││Стремянка│8k │2 дня ││   ║
║  │ │        │   │/3333   │││         │  │/4000  ││   ║
║  │ │        │   │₸/день  │││         │  │₸/день ││   ║
║  │ ├────────┴───┴────────┤│├────────┴──┴────────┤│   ║
║  │ │[+ Добавить]        ││[+ Добавить]        ││   ║
║  │ │Итого: 10k₸ на 3дн  ││Итого: 8k₸ на 2дн   ││   ║
║  │ │Ставка: 3333/день   ││Ставка: 4000/день   ││   ║
║  │ └──────────────────────┘│└──────────────────────┘│   ║
║  │                         │                         │   ║
║  │ 🎮 РАЗВЛЕЧЕНИЯ          │ 🎮 РАЗВЛЕЧЕНИЯ        │   ║
║  │ ┌──────────────────────┐│ ┌──────────────────────┐│   ║
║  │ │PlayStation│25k │7дн │││Консоль  │25k│7 дня ││   ║
║  │ │           │   │/357 │││Switch   │   │/3571 ││   ║
║  │ └──────────┴──┴─────┘│└──────────┴──┴──────┘│   ║
║  │ [+ Добавить]        │[+ Добавить]        │   ║
║  │ Итого: 25k₸ на 7дн  │Итого: 25k₸ на 7дн  │   ║
║  │ Ставка: 3571/день   │Ставка: 3571/день   │   ║
║  └─────────────────────────┴─────────────────────────┘   ║
║                                                            ║
║  ┌──────────────────────────────────────────────────────┐ ║
║  │ ИТОГОВАЯ СТАТИСТИКА                                 │ ║
║  ├──────────────────────────────────────────────────────┤ ║
║  │ Хочу взять:                    Могу дать:           │ ║
║  │  • Велосипед 7 дней            • Дрель 5 дней      │ ║
║  │  • Лестница 3 дня              • Стремянка 2 дня   │ ║
║  │  • PlayStation 7 дней          • Switch 7 дней     │ ║
║  │  ━━━━━━━━━━━━━━━━━━━━          ━━━━━━━━━━━━━━━━  │ ║
║  │  ИТОГО: 17 дней на 65k₸       ИТОГО: 14 дней на   │ ║
║  │  Ставка: 3,823 ₸/день          54k₸, Ставка:     │ ║
║  │                                  3,857 ₸/день      │ ║
║  │                                                       │ ║
║  │ СООТВЕТСТВИЕ: ✅ Хорошо!                            │ ║
║  │ Дневные ставки совпадают (разница: 0.9%)          │ ║
║  │ Общее время: можно договориться о дополн. дне    │ ║
║  └──────────────────────────────────────────────────────┘ ║
║                                                            ║
║  ┌──────────────────────────────────────────────────────┐ ║
║  │ [🔍 Найти совпадения]  [💾 Сохранить как черновик] │ ║
║  └──────────────────────────────────────────────────────┘ ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### **Temporary Item Input Form**

```
┌────────────────────────────────────────────┐
│ ➕ Добавить предмет в ТРАНСПОРТ            │
├────────────────────────────────────────────┤
│                                            │
│ Предмет:                                   │
│ ┌──────────────────────────────────────┐  │
│ │ [Введите название]                   │  │
│ └──────────────────────────────────────┘  │
│                                            │
│ Ценность (в тенге):                       │
│ ┌──────────────────────────────────────┐  │
│ │ [30000]                    ₸        │  │
│ └──────────────────────────────────────┘  │
│                                            │
│ Срок (в днях): ← UNIQUE FOR TEMPORARY    │
│ ┌──────────────────────────────────────┐  │
│ │ [7]                      дней       │  │
│ └──────────────────────────────────────┘  │
│                                            │
│ Дневная ставка (автоматически):           │
│ ┌──────────────────────────────────────┐  │
│ │ 30000 ₸ / 7 дней = 4,286 ₸/день    │  │
│ │ (для расчета совпадений)             │  │
│ └──────────────────────────────────────┘  │
│                                            │
│ Описание (опционально):                    │
│ ┌──────────────────────────────────────┐  │
│ │ [Состояние, модель, условия возврата]│  │
│ └──────────────────────────────────────┘  │
│                                            │
│ [Отмена]  [✅ Добавить]                  │
│                                            │
└────────────────────────────────────────────┘
```

---

## 🎨 **Key UI Components Comparison**

### **Permanent Tab Specifics**

| Component | Display | Logic |
|-----------|---------|-------|
| **Price Input** | ₸ (Tenge symbol) | Raw monetary value |
| **Duration** | ❌ Not shown | NULL in database |
| **Summary Calc** | Sum of values | Total wants ≈ Total offers |
| **Match Logic** | Value equivalence | Within ±15% |
| **Notification** | "Permanent match found" | "Exchange ownership" |

### **Temporary Tab Specifics**

| Component | Display | Logic |
|-----------|---------|-------|
| **Price Input** | ₸ (Tenge symbol) | Estimated value |
| **Duration** | 📅 Days (1-365) | Rental period |
| **Daily Rate** | ₸/day (auto-calc) | value / duration |
| **Summary Calc** | Total value + total days | Rate comparison |
| **Match Logic** | Daily rate equivalence | Within ±15% |
| **Notification** | "Rental match found" | "Borrow & return" |

---

## 🎯 **Color Scheme & Branding**

### **Permanent Exchange Tab**
```
Primary Color:    #27AE60 (Green - trust, ownership, stability)
Secondary Color:  #2ECC71 (Light green - growth)
Text:            #2C3E50 (Dark blue-gray)
Background:      #E8F5E9 (Very light green)
Accent:          💰 (Money emoji)
```

### **Temporary Exchange Tab**
```
Primary Color:    #FF9800 (Orange - time, urgency, rental)
Secondary Color:  #FFB74D (Light orange - warmth)
Text:            #2C3E50 (Dark blue-gray)
Background:      #FFF3E0 (Very light orange)
Accent:          🕒 (Clock emoji)
```

### **Shared Elements**
```
Success:         #27AE60 (Green checkmarks)
Error:           #E74C3C (Red warnings)
Border:          #BDC3C7 (Light gray)
Shadow:          rgba(0, 0, 0, 0.1)
```

---

## 📱 **Responsive Design**

### **Desktop (1200px+)**
```
Two-column layout active
Side-by-side wants/offers
Full category expansion
All statistics visible
```

### **Tablet (768px-1199px)**
```
Still two columns but narrower
Can stack horizontally if needed
Statistics below
Collapsible categories
```

### **Mobile (< 768px)**
```
Single column layout
Wants above Offers
Stack vertically
Full-width cards
Collapse by default
Show summary only
```

---

## 🔄 **User Flow - Permanent Exchange Tab**

```
1. User clicks "💰 Постоянный обмен" tab
   ↓
2. Sees categories: ТЕХНИКА, ДЕНЬГИ, МЕБЕЛЬ, etc.
   ↓
3. Fills LEFT side (ХОЧУ):
   - Category: ТЕХНИКА
   - Item: Телефон
   - Price: 50000 ₸
   - Description: iPhone 12 Pro
   ↓
4. Fills RIGHT side (МОГУ):
   - Category: ТЕХНИКА
   - Item: Ноутбук
   - Price: 100000 ₸
   - Description: MacBook
   ↓
5. Sees summary: "Переплачу на 50k ₸" (I pay 50k extra)
   ↓
6. Can add more items to balance or click "Найти совпадения"
   ↓
7. System finds partners in database with inverse wants/offers
   ↓
8. Gets Telegram notification with filtered match
```

---

## 🔄 **User Flow - Temporary Exchange Tab**

```
1. User clicks "🕒 Временный обмен" tab
   ↓
2. Sees categories: ТРАНСПОРТ, ИНСТРУМЕНТЫ, СПОРТ, etc.
   ↓
3. Fills LEFT side (ХОЧУ ВЗЯТЬ):
   - Category: ТРАНСПОРТ
   - Item: Велосипед
   - Value: 30000 ₸
   - Duration: 7 дней
   - Daily rate: 4,286 ₸/день (auto-calculated)
   ↓
4. Fills RIGHT side (МОГУ ДАТЬ):
   - Category: ТРАНСПОРТ
   - Item: Дрель
   - Value: 21000 ₸
   - Duration: 5 дней
   - Daily rate: 4,200 ₸/день (auto-calculated)
   ↓
5. Sees summary:
   "Дневные ставки совпадают! (4286 vs 4200, разница 0.9%)"
   ↓
6. Can add more rental items or click "Найти совпадения"
   ↓
7. System finds partners with matching daily rates
   ↓
8. Gets Telegram notification:
   "Rental match found! Bike for 7 days ← Drill for 5 days"
   "Return by: [date]"
```

---

## 📤 **Data Submission Format**

### **Permanent Exchange Submission**
```json
{
  "user_id": 1,
  "exchange_type": "permanent",
  "wants": {
    "electronics": [
      {
        "item_name": "Телефон",
        "value_tenge": 50000,
        "description": "iPhone 12",
        "exchange_type": "permanent"
      }
    ],
    "furniture": [...]
  },
  "offers": {...},
  "locations": ["Алматы"]
}
```

### **Temporary Exchange Submission**
```json
{
  "user_id": 1,
  "exchange_type": "temporary",
  "wants": {
    "transport": [
      {
        "item_name": "Велосипед",
        "value_tenge": 30000,
        "duration_days": 7,
        "description": "Mountain bike",
        "exchange_type": "temporary",
        "daily_rate": 4286
      }
    ]
  },
  "offers": {...},
  "locations": ["Алматы"]
}
```

---

## ✨ **Key UI/UX Features**

### **Both Tabs Share**
- ✅ Two-column layout (Wants | Offers)
- ✅ Category-based sections
- ✅ Add/Remove items easily
- ✅ Real-time summary calculation
- ✅ Beautiful gradient backgrounds
- ✅ Material Design 3 compliance
- ✅ Emoji indicators for each exchange type
- ✅ Responsive design (mobile-first)

### **Permanent Tab Unique**
- 💰 Green color scheme (trust, stability)
- 💵 Simple value-based inputs
- 📊 Balance calculation (who pays extra)
- ✅ Final ownership transfer semantics

### **Temporary Tab Unique**
- 🕒 Orange color scheme (time, urgency)
- 📅 Duration inputs with daily rate auto-calc
- 📈 Daily rate matching visualization
- 🔄 Return policy indication

---

## 🎬 **Animation & Transitions**

### **Tab Switching**
```
Duration: 300ms (Material Design standard)
Easing: cubic-bezier(0.4, 0, 0.2, 1) (Material ease)
Effect: Fade + slide
```

### **Category Expand/Collapse**
```
Duration: 200ms
Effect: Smooth height animation
Icon: Rotate arrow indicator
```

### **Item Addition**
```
Duration: 300ms
Effect: Fade in + slide from bottom
Sound: Subtle notification tone (optional)
```

---

## 🔐 **Validation & Error Handling**

### **Permanent Tab Validation**
- ✅ `value_tenge` > 0
- ✅ `item_name` not empty
- ✅ At least one want
- ✅ At least one offer
- ❌ `duration_days` must be NULL

### **Temporary Tab Validation**
- ✅ `value_tenge` > 0
- ✅ `duration_days` between 1-365
- ✅ `item_name` not empty
- ✅ At least one want
- ✅ At least one offer
- ❌ `duration_days` must be filled

### **Error Messages** (Toast/Snackbar)
```
Example: "❌ Цена должна быть больше 0!"
Position: Bottom-right
Duration: 5 seconds
Action: [✕ Dismiss] or auto-hide
```

---

## ✅ **Accessibility**

- ♿ WCAG 2.1 Level AA compliance
- 🔤 Readable font sizes (16px minimum)
- 🎯 Large touch targets (44px minimum)
- 🌈 Color-blind friendly (not relying on color alone)
- ⌨️ Full keyboard navigation
- 📢 Screen reader support (ARIA labels)
- 🌙 Dark mode ready

---

## 📐 **Typography**

```
Heading (Tab Title):  Open Sans Bold 24px  (2C3E50)
Section Title:        Open Sans 600 18px   (2C3E50)
Label:               Open Sans 500 14px   (555555)
Input Text:          Open Sans 400 14px   (333333)
Helper Text:         Open Sans 400 12px   (999999)
```

---

## 🎯 **Success Metrics**

| Metric | Target | How to Measure |
|--------|--------|-----------------|
| Tab switching time | <100ms | Performance monitoring |
| Form completion time | <3 min | User session tracking |
| Permanent match found | >80% | Users report matches |
| Temporary match found | >75% | Daily rate similarity |
| Mobile usability | 4.5/5 | User feedback survey |
| Task success rate | >95% | Form submission rate |

---

**Status: ✅ UI/UX Design Complete & Ready for Development**

This design provides:
- ✅ Clear separation between exchange types
- ✅ Intuitive, Material Design 3 compliant interface
- ✅ Appropriate inputs for each exchange type
- ✅ Real-time calculations and feedback
- ✅ Responsive and accessible
- ✅ Beautiful, modern aesthetics

Ready to implement in React! 🚀
