# 📍 Locations Feature - Quick Reference

## 🚀 Quick Start

### Create User with Locations
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "contact": {"telegram": "@alice"},
    "locations": ["Алматы", "Астана"]
  }'
```

### Update User Locations
```bash
curl -X PUT http://localhost:8000/api/users/1/locations \
  -G \
  --data-urlencode "locations=Алматы" \
  --data-urlencode "locations=Шымкент"
```

### Get User Profile
```bash
curl http://localhost:8000/api/users/1
```

---

## 📍 Valid Locations

```
1. Алматы
2. Астана
3. Шымкент
```

---

## 🎯 How Matching Works

### Rule: Users must share at least ONE location

```
Alice: ["Алматы", "Астана"]
Bob:   ["Астана", "Шымкент"]
Common: ["Астана"] ✅

→ Match possible!
```

### Score Bonus

```
Base score: 0.5 (text similarity)
Location match bonus: +0.1
Final: 0.6 ✅
```

---

## 🧪 Test Cases

### ✅ Same City
```
Alice: ["Алматы"]
Bob: ["Алматы"]
Result: Match ✅
```

### ✅ Multiple Cities with Overlap
```
Alice: ["Алматы", "Астана"]
Bob: ["Астана", "Шымкент"]
Common: Астана
Result: Match ✅
```

### ❌ No Common City
```
Alice: ["Алматы"]
Bob: ["Шымкент"]
Result: No match ❌
```

---

## 📊 Database

### Add locations to existing users
```sql
ALTER TABLE users ADD COLUMN locations TEXT[] DEFAULT ARRAY['Алматы'];
```

### Query users by location
```sql
SELECT * FROM users WHERE 'Алматы' = ANY(locations);
```

---

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/users/` | Create user with locations |
| GET | `/api/users/{id}` | Get user profile |
| GET | `/api/users/username/{name}` | Get by username |
| PUT | `/api/users/{id}/locations` | Update locations |

---

## ✅ Validation

- Min locations: 1
- Max locations: 3
- Valid cities only
- No duplicates

---

## 🔄 Integration

### In find_candidates()
- Filters candidates by location overlap
- Only returns users in common cities

### In score_candidates()
- Adds +0.1 location bonus
- Prioritizes local exchanges

### In chain matching
- Chains only created between users in common cities
- Ensures all participants can physically exchange

---

## 📝 Code Changes

### Models
- Added `locations: ARRAY(String)` to User

### CRUD
- `update_user_locations()` - Update user's cities
- Validates locations on create/update

### Matching
- `find_candidates()` - Filters by location
- `score_candidates()` - Adds location bonus
- `get_all_unilateral_edges()` - Chain filtering by location

### API
- New `/api/users/` endpoints
- PUT `/api/users/{id}/locations` - Update locations

---

## 🎓 Concepts

### Location Overlap
```python
user_a_locs = {"Алматы", "Астана"}
user_b_locs = {"Астана"}

overlap = user_a_locs & user_b_locs  # {"Астана"}
if overlap:
    can_match = True
```

### Multi-City Users
- Users can be active in multiple cities
- Matches happen in ANY common city
- Example: Alice (Almaty + Astana) can match with Bob (Astana only) in Astana

---

## 🚨 Common Issues

### Issue: "No matching users"
**Cause:** Users in different cities
**Fix:** Update locations to have overlap

### Issue: "Invalid location"
**Cause:** City not in [Алматы, Астана, Шымкент]
**Fix:** Use valid city names

### Issue: Migration errors
**Cause:** locations column missing
**Fix:** Run migration to add column

---

## 📚 Full Documentation

See `backend/LOCATIONS_FEATURE.md` for:
- Complete API docs
- All test scenarios
- Migration path
- Performance analysis
- Integration points
