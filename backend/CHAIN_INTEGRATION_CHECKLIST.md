# ✅ Chain Matching Integration Checklist

## Phase 1: Code Integration Verification

### Module Creation
- [x] **backend/chain_matching.py** - Core module created
  - [x] `create_unilateral_edge()` - Edge creation
  - [x] `get_all_unilateral_edges()` - Edge retrieval
  - [x] `ChainGraph` class - Graph construction
  - [x] `_calculate_similarity()` - Similarity scoring
  - [x] `create_exchange_chain()` - Chain creation
  - [x] `save_exchange_chain_to_db()` - Database persistence
  - [x] `discover_and_create_chains()` - Main orchestration

### API Integration
- [x] **backend/api/endpoints/exchange_chains.py** - New endpoint module
  - [x] `GET /api/chains/discover` - Trigger discovery
  - [x] `GET /api/chains/all` - List all chains
  - [x] `GET /api/chains/user/{user_id}` - User's chains
  - [x] `POST /api/chains/{chain_id}/accept` - Accept chain
  - [x] `POST /api/chains/{chain_id}/decline` - Decline chain
- [x] **backend/api/router.py** - Include exchange_chains router
- [x] **backend/api/endpoints/__init__.py** - Export exchange_chains

### Database Layer Integration
- [x] **backend/crud.py** - Chain CRUD operations
  - [x] `get_exchange_chains()` - Retrieve chains with filtering
  - [x] `get_user_chains()` - Get user's specific chains
  - [x] `accept_exchange_chain()` - Accept participation
  - [x] `decline_exchange_chain()` - Decline participation

### Matching Pipeline Integration
- [x] **backend/matching.py** - Main pipeline orchestration
  - [x] `run_full_matching_pipeline()` - Combined bilateral + chain matching

### Documentation
- [x] **backend/CHAIN_MATCHING_ARCHITECTURE.md** - Complete architecture
- [x] **DEVELOPMENT.md** - Updated with chain scenarios

---

## Phase 2: Database Verification

### ExchangeChain Model
```python
class ExchangeChain(Base):
    __tablename__ = "exchange_chains"
    
    id = Column(Integer, primary_key=True, index=True)
    participants = Column(JSON, nullable=False)  # [user_id_1, user_id_2, ...]
    items = Column(JSON, nullable=False)         # {user_id: item_id, ...}
    total_score = Column(Float, nullable=False)
    status = Column(String, default="proposed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
```

**Status:** ✅ Already exists in `backend/models.py`

### Verify Table Structure
```sql
-- Check if table exists
SELECT * FROM exchange_chains LIMIT 0;

-- Check participants and items are JSON
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'exchange_chains';
```

---

## Phase 3: Import Verification

### Run Quick Structure Test
```bash
cd C:\Users\user\Desktop\FreeMarket
python backend/quick_test.py
```

Expected output:
```
✅ Config module
✅ Models module
✅ Schemas module
✅ CRUD module
✅ Matching module
✅ API router
✅ Health endpoint
✅ Market listings endpoint
✅ FastAPI app (X routes)
✅ Utils modules
```

### Test Specific Imports
```python
# Test chain_matching module
from backend.chain_matching import discover_and_create_chains, ChainGraph

# Test exchange_chains endpoint
from backend.api.endpoints import exchange_chains

# Test crud chain operations
from backend.crud import (
    get_exchange_chains,
    get_user_chains,
    accept_exchange_chain,
    decline_exchange_chain
)
```

---

## Phase 4: Functional Testing

### Test 1: Edge Creation
```python
from backend.chain_matching import create_unilateral_edge
from backend.database import SessionLocal

db = SessionLocal()

# Get two items
item_a = db.query(Item).filter(Item.kind == 2).first()  # want
item_b = db.query(Item).filter(Item.kind == 1).first()  # offer

# Create edge
edge = create_unilateral_edge(db, item_a, item_b, 0.75)
print(edge)  # Should print: {from_user, to_user, score, ...}
```

### Test 2: Graph Construction
```python
from backend.chain_matching import get_all_unilateral_edges, ChainGraph

edges = get_all_unilateral_edges(db)
print(f"Found {len(edges)} edges")

graph = ChainGraph(edges)
print(f"Graph has {len(graph.graph)} nodes")
```

### Test 3: Cycle Detection
```python
cycles = graph.find_cycles(min_length=3, max_length=10)
print(f"Found {len(cycles)} cycles")

if cycles:
    for i, cycle in enumerate(cycles):
        users = [edge["from_user"] for edge in cycle]
        print(f"Cycle {i}: {users}")
```

### Test 4: Chain Creation & Saving
```python
from backend.chain_matching import discover_and_create_chains

chains_created = discover_and_create_chains(db)
print(f"Created {chains_created} chains")

# Verify in DB
from backend.crud import get_exchange_chains
chains, total = get_exchange_chains(db, status="proposed")
print(f"Total chains in DB: {total}")
```

---

## Phase 5: API Endpoint Testing

### Test 5a: Discover Chains
```bash
curl -X POST http://localhost:8000/api/chains/discover

# Expected:
{
    "success": true,
    "chains_created": 3,
    "message": "Обнаружено 3 новых цепочек обмена"
}
```

### Test 5b: List All Chains
```bash
curl -X GET http://localhost:8000/api/chains/all

# Expected:
{
    "chains": [...],
    "total": 5,
    "skip": 0,
    "limit": 20
}
```

### Test 5c: Get User's Chains
```bash
curl -X GET http://localhost:8000/api/chains/user/1

# Expected:
{
    "user_id": 1,
    "chains": [...],
    "count": 2
}
```

### Test 5d: Accept Chain
```bash
curl -X POST "http://localhost:8000/api/chains/1/accept?user_id=1"

# Expected:
{
    "success": true,
    "chain_id": 1,
    "user_id": 1,
    "message": "Вы приняли участие в цепочке обмена"
}
```

### Test 5e: Decline Chain
```bash
curl -X POST "http://localhost:8000/api/chains/2/decline?user_id=2"

# Expected:
{
    "success": true,
    "chain_id": 2,
    "user_id": 2,
    "message": "Вы отклонили участие в цепочке обмена"
}
```

---

## Phase 6: Integration with Existing Matching

### Full Pipeline Test
```python
from backend.matching import run_full_matching_pipeline

# Run both bilateral + chain matching
run_full_matching_pipeline(db)

# Should see logs:
# === Starting full matching pipeline ===
# Phase 1: Bilateral matching for all users
# Phase 1: Bilateral matching complete
# Phase 2: Discovering exchange chains
# Phase 2: Created X exchange chains
# === Full matching pipeline complete ===
```

---

## Phase 7: Swagger Documentation

### Verify API Docs
```
http://localhost:8000/docs
```

Should show:
- ✅ `/api/chains/discover` (POST)
- ✅ `/api/chains/all` (GET)
- ✅ `/api/chains/user/{user_id}` (GET)
- ✅ `/api/chains/{chain_id}/accept` (POST)
- ✅ `/api/chains/{chain_id}/decline` (POST)

---

## Phase 8: Data Validation

### Check Notifications
```python
from backend.models import Notification

# Find chain notifications
notifications = db.query(Notification).filter(
    Notification.payload.contains("exchange_chain")
).all()

print(f"Found {len(notifications)} chain notifications")

for notif in notifications:
    print(f"User {notif.user_id}: {notif.payload}")
```

---

## Phase 9: Performance Baseline

### Measure Discovery Time
```python
import time

start = time.time()
chains_created = discover_and_create_chains(db)
elapsed = time.time() - start

print(f"Discovery took {elapsed:.2f}s, created {chains_created} chains")

# Acceptable times:
# < 1s: Excellent
# 1-5s: Good
# 5-10s: OK
# > 10s: Needs optimization
```

### Check Query Performance
```python
# Enable PostgreSQL logging to see queries
# Look for N+1 issues, missing indexes
```

---

## Phase 10: Final Verification

### Checklist
- [ ] All modules import without errors
- [ ] ExchangeChain table exists and is accessible
- [ ] Edge creation works (unit test)
- [ ] Graph construction works (unit test)
- [ ] Cycle detection finds valid cycles
- [ ] Chains are created and saved to DB
- [ ] CRUD operations work (get, accept, decline)
- [ ] API endpoints respond correctly
- [ ] Notifications are created for chain participants
- [ ] Full pipeline runs without errors
- [ ] Swagger docs show all new endpoints
- [ ] Performance is acceptable (< 10s)

---

## Common Issues & Fixes

### Issue 1: "No module named 'backend.chain_matching'"
**Fix:** Ensure file exists: `backend/chain_matching.py`

### Issue 2: ExchangeChain table not found
**Fix:** Run migrations or init_db.py to create table

### Issue 3: DFS finds no cycles
**Fix:** Check if items have high enough similarity scores (threshold 0.3)

### Issue 4: Notifications not created
**Fix:** Verify NotificationCreate is properly imported in chain_matching.py

### Issue 5: Slow discovery performance
**Fix:** Reduce threshold (fewer edges), reduce max_length, add database indexes

---

## Next Steps After Integration

1. **Testing:** Run all test scenarios from DEVELOPMENT.md
2. **Monitoring:** Add logging to track chain discovery patterns
3. **Optimization:** Profile performance with real data
4. **Frontend:** Display chains in UI
5. **Deployment:** Test on staging environment
6. **Documentation:** Update user guide with chain feature
7. **Analytics:** Track chain acceptance rates
