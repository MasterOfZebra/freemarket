# 🔗 Exchange Chain Matching Architecture

## Overview

The Exchange Chain Matching system extends FreeMarket's bilateral (2-way) matching with support for multi-way exchanges (3+ participants). This enables complex trading scenarios where chains of exchanges create mutual satisfaction.

## 🏗️ System Architecture

### Layer 1: Data Models

**Existing Tables Used:**
- `users` - Participants
- `items` - Offers and Wants (with `kind` field: 1=offer, 2=want)
- `matches` - Bilateral matches
- `exchange_chains` - Multi-way exchange records (already defined in models.py)

**Data Flow:**
```
Users create Items
    ↓
Items are matched (bilateral or unilateral)
    ↓
Matching system discovers chains
    ↓
ExchangeChain records created
    ↓
Notifications sent to participants
```

### Layer 2: Chain Matching Pipeline

```
┌─────────────────────────────────────────────────────────┐
│  DISCOVER_AND_CREATE_CHAINS() - Main Orchestration     │
│                                                          │
│  1. get_all_unilateral_edges()                         │
│     ├─ Query all active wants + offers                 │
│     ├─ Calculate similarity scores                      │
│     └─ Return edges with score > threshold (0.3)       │
│                                                          │
│  2. ChainGraph(edges)                                  │
│     ├─ Build adjacency list from edges                 │
│     └─ Create directed graph: user → user              │
│                                                          │
│  3. find_cycles(min_len=3, max_len=10)                │
│     ├─ DFS for each start node                         │
│     ├─ Find all closed loops                           │
│     └─ Deduplicate cycles                              │
│                                                          │
│  4. For each cycle:                                     │
│     ├─ create_exchange_chain()                         │
│     ├─ save_exchange_chain_to_db()                     │
│     └─ create_chain_notifications()                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Layer 3: Module Structure

```
backend/
├── chain_matching.py          # Core chain discovery algorithm
│   ├── create_unilateral_edge()
│   ├── get_all_unilateral_edges()
│   ├── ChainGraph class
│   │   ├── find_cycles()
│   │   └── _dfs_cycle()
│   ├── create_exchange_chain()
│   ├── save_exchange_chain_to_db()
│   └── discover_and_create_chains()
│
├── matching.py                # Integration point
│   ├── find_matches() [EXISTING]
│   └── run_full_matching_pipeline() [NEW]
│
├── crud.py                    # Database operations
│   ├── get_exchange_chains()
│   ├── get_user_chains()
│   ├── accept_exchange_chain()
│   └── decline_exchange_chain()
│
└── api/endpoints/
    └── exchange_chains.py     # REST API
        ├── GET /api/chains/discover
        ├── GET /api/chains/all
        ├── GET /api/chains/user/{user_id}
        ├── POST /api/chains/{chain_id}/accept
        └── POST /api/chains/{chain_id}/decline
```

## 🔄 Algorithm: Cycle Detection Using DFS

### Input:
- Directed graph where edges are: User A wants → User B offers

### Process:
```python
for each user in graph:
    run DFS from that user
        find paths that return to starting user
        filter cycles by length (3-10)
        validate no duplicate participants
        calculate average score of path
```

### Example Flow:

**Data:**
```
Alice: want "велосипед", offer "книга"
Bob:   want "ноутбук", offer "велосипед"
Carol: want "книга", offer "ноутбук"
```

**Edges Created:**
```
Edge 1: Alice.want → Bob.offer (score: 0.85)
Edge 2: Bob.want → Carol.offer (score: 0.80)
Edge 3: Carol.want → Alice.offer (score: 0.90)
```

**Graph:**
```
Alice → Bob → Carol → Alice (cycle detected!)
```

**Chain Created:**
```
ExchangeChain {
    id: 1
    participants: [1, 2, 3]  # Alice, Bob, Carol
    items: {
        1: 10,  # Alice's велосипед (item_id)
        2: 20,  # Bob's ноутбук
        3: 30   # Carol's книга
    }
    total_score: (0.85 + 0.80 + 0.90) / 3 = 0.85
    status: "proposed"
}
```

## 📊 Database Schema

### ExchangeChain Table
```sql
id (PK)
participants (JSON array: [user_id_1, user_id_2, ...])
items (JSON object: {user_id: item_id, ...})
total_score (float: 0.0-1.0)
status (enum: proposed, matched, rejected, completed)
created_at (timestamp)
completed_at (timestamp)
```

### Example Record:
```json
{
    "id": 42,
    "participants": [101, 102, 103],
    "items": {
        "101": 500,
        "102": 501,
        "103": 502
    },
    "total_score": 0.85,
    "status": "proposed",
    "created_at": "2025-01-15T10:30:00Z",
    "completed_at": null
}
```

## 🔌 Integration Points

### 1. Matching Pipeline Integration

**Before (only bilateral):**
```python
def find_matches(db, user_id):
    # Find 2-way matches only
```

**After (bilateral + chains):**
```python
def run_full_matching_pipeline(db, user_id):
    # Phase 1: Bilateral matching
    find_matches(db, user_id)
    
    # Phase 2: Chain discovery
    discover_and_create_chains(db)
```

### 2. Trigger Points

Chain discovery can be triggered:
- **Manual**: `POST /api/chains/discover`
- **Scheduled**: Via background task (cron job)
- **Automatic**: After new item creation (future enhancement)

### 3. Notification Integration

When chain is discovered, for each participant:
```json
{
    "type": "exchange_chain",
    "chain_id": 42,
    "chain_length": 3,
    "chain_score": 0.85,
    "giver": {
        "user_id": 101,
        "username": "alice",
        "contact": {"telegram": "@alice"}
    },
    "receiver": {
        "user_id": 103,
        "username": "carol",
        "contact": {"telegram": "@carol"}
    },
    "message": "Вы участник 3-сторонней цепочки обмена!"
}
```

## 🎯 API Endpoints

### Discover Chains
```
POST /api/chains/discover
Response:
{
    "success": true,
    "chains_created": 3,
    "message": "Обнаружено 3 новых цепочек обмена"
}
```

### List All Chains
```
GET /api/chains/all?status=proposed&skip=0&limit=20
Response:
{
    "chains": [...],
    "total": 15,
    "skip": 0,
    "limit": 20
}
```

### Get User's Chains
```
GET /api/chains/user/101?status=proposed
Response:
{
    "user_id": 101,
    "chains": [...],
    "count": 3
}
```

### Accept Chain
```
POST /api/chains/42/accept?user_id=101
Response:
{
    "success": true,
    "chain_id": 42,
    "user_id": 101,
    "message": "Вы приняли участие в цепочке обмена"
}
```

### Decline Chain
```
POST /api/chains/42/decline?user_id=101
Response:
{
    "success": true,
    "chain_id": 42,
    "user_id": 101,
    "message": "Вы отклонили участие в цепочке обмена"
}
```

## 📈 Performance Considerations

### Complexity Analysis

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Edge creation | O(n×m) | n=wants, m=offers |
| Graph building | O(e) | e=number of edges |
| DFS cycle detection | O(V+E) | V=users, E=edges |
| **Total for discovery** | **O(n×m + V+E)** | Manageable for <10k users |

### Optimization Tips

1. **Threshold filtering** (default 0.3): Removes low-quality edges early
2. **Max cycle length** (default 10): Limits DFS depth
3. **Batching**: Run discovery periodically, not per-user
4. **Caching**: Store frequently accessed chains in Redis

### Scalability (Future)

- PostgreSQL GIN indexes on participants array
- Materialized view for user_chains
- Async task queue (Celery) for chain discovery
- Graph database (Neo4j) for complex queries

## 🚀 Future Enhancements

### 1. Longer Chains
- Currently supports 3-10 participants
- Could extend to handle arbitrary-length chains
- Performance trade-offs to consider

### 2. Weighted Chains
- Prioritize chains by average score
- Consider temporal factors (expiry dates)
- Factor in user reputation

### 3. Smart Notifications
- Telegram/Email integration
- Real-time updates as chain status changes
- Option to negotiate chain terms

### 4. Chain Execution
- Track delivery of items in chain
- Dispute resolution
- Rating/feedback after completion

### 5. Analytics
- Chain formation patterns
- Success rate metrics
- User engagement tracking

## 🧪 Testing Scenarios

### Test Case 1: Simple 3-Way Chain
```
Input:
  A: want "X", offer "Y"
  B: want "Y", offer "Z"
  C: want "Z", offer "X"

Expected: Chain created with score ≈ 0.8+
```

### Test Case 2: Broken Chain (missing link)
```
Input:
  A: want "X", offer "Y"
  B: want "Y", offer "Z"
  C: want "W", offer "X"  # Wants "W", not "Z"

Expected: No chain created (disconnected)
```

### Test Case 3: 4-Way Chain
```
Input:
  A: want "W", offer "X"
  B: want "X", offer "Y"
  C: want "Y", offer "Z"
  D: want "Z", offer "W"

Expected: 4-way chain created
```

## 📚 Related Files

- `backend/models.py` - ExchangeChain model definition
- `backend/schemas.py` - Pydantic schemas
- `DEVELOPMENT.md` - User flow documentation
- `backend/matching.py` - Main matching algorithms
- `backend/crud.py` - Database operations
