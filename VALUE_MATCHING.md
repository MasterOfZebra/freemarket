# FreeMarket API - Value Range Matching

## Overview

FreeMarket now supports value range matching for more precise item exchanges. This document outlines the data model, matching algorithms, and API endpoints.

---

## Data Model

Items now include value ranges for better matching:

```json
{
  "user_id": 1,
  "kind": 1,
  "category": "electronics",
  "title": "Laptop",
  "description": "Gaming laptop",
  "wants": ["phone"],
  "offers": ["laptop"],
  "value_min": 500,
  "value_max": 1000,
  "lease_term": "P1M",
  "is_money": false
}
```

---

## Matching Algorithm

### Scoring Formula

```
score = α * text_similarity + β * tag_similarity + γ * value_overlap + δ * trust_score
```

- **text_similarity**: Cosine similarity of Sentence-BERT embeddings.
- **tag_similarity**: Intersection of wants/offers tags.
- **value_overlap**: Overlap of value ranges.
- **trust_score**: User trust score with decay.

### Multi-Level Search

The system returns results based on confidence levels:

1. **High Confidence** (score ≥ 0.8): Up to 10 results.
2. **Medium Confidence** (score ≥ 0.6): Up to 20 results.
3. **Extended Search** (score ≥ 0.4): Up to 30 results.

---

## API Endpoints

### Get Optimal Matches

```
GET /matches/{item_id}/optimal
```

Response:
```json
[
  {
    "item_a": 1,
    "item_b": 2,
    "score": 0.85,
    "reason": "high_confidence",
    "reasons": {
      "text_similarity": 0.9,
      "tag_similarity": 0.8,
      "value_overlap": 0.7,
      "category_weights": {"text": 0.5, "attributes": 0.5}
    },
    "status": "new"
  }
]
```

---

## A/B Testing

Users are automatically split into groups with different matching thresholds:

- **Control**: score ≥ 0.5, top_k = 5
- **Variant A**: score ≥ 0.6, top_k = 3 (stricter)
- **Variant B**: score ≥ 0.4, top_k = 7 (looser)

---

## Graph-Based Exchanges

For multi-party exchanges, NetworkX is used to find cycles in the graph of potential deals.

---

## Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

### New Packages

- `sentence-transformers`: For text embeddings.
- `lightgbm`: For learn-to-rank.
- `networkx`: For graph algorithms.
- `redis`: For queues and caching.

---

## Worker Automation

1. **User creates an item** (`POST /items/`).
2. **FastAPI saves** the item to the database and queues a task in Redis.
3. **Background worker** processes the task:
   - Finds all matching active items.
   - Calculates scores for each pair.
   - Checks reciprocity (existing matches).
   - Creates new matches or updates status to "matched."
4. **Notifications** are sent to both users on mutual matches.

---

## Database Schema

```sql
CREATE TABLE mutual_matches (
  id BIGSERIAL PRIMARY KEY,
  item_a BIGINT REFERENCES items(id),
  item_b BIGINT REFERENCES items(id),
  matched_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE (LEAST(item_a, item_b), GREATEST(item_a, item_b))
);
```

---

## Running the Worker

```bash
python worker.py
```

The worker will automatically process tasks from the Redis queue.
