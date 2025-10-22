"""
Compute user vectors from history of accepted matches.
This is a lightweight in-memory/resdis-backed implementation to start with.
"""
from typing import List, Optional
from backend.database import redis_client
from backend.ml.embeddings import get_embedding
import numpy as np
import json

USER_VECTOR_TTL = 24 * 3600


def _safe_get(key: str) -> Optional[str]:
    """Safely get value from Redis, handling awaitables."""
    try:
        result = redis_client.get(key)
        # If result is awaitable, we can't resolve it in sync context
        if hasattr(result, '__await__'):
            # Return None or fallback for awaitable results in sync context
            return None
        # If result is bytes, decode it
        if isinstance(result, bytes):
            return result.decode('utf-8')
        # If result is string or None
        return str(result) if result else None
    except Exception:
        return None


def build_user_vector(user_id: int, item_texts: List[str]):
    """Aggregate embeddings of accepted items into a user vector and store in Redis."""
    if not item_texts:
        return None
    embs = [np.array(get_embedding(t)) for t in item_texts]
    vec = np.mean(embs, axis=0).tolist()
    key = f"user_vec:{user_id}"
    redis_client.setex(key, USER_VECTOR_TTL, json.dumps(vec))
    return vec


def get_user_vector(user_id: int):
    key = f"user_vec:{user_id}"
    cached = _safe_get(key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            return None
    return None


def user_item_similarity(user_id: int, item_text: str) -> float:
    u = get_user_vector(user_id)
    if not u:
        return 0.0
    ui = np.array(u)
    it = np.array(get_embedding(item_text))
    denom = (np.linalg.norm(ui) * np.linalg.norm(it))
    if denom == 0:
        return 0.0
    return float(np.dot(ui, it) / denom)
