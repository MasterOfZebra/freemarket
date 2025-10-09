"""
Vector matching engine stub. Intended to be swapped with Qdrant/Faiss implementations.
Provides an index/write/search API, with a brute-force fallback for small datasets.
"""
from typing import List, Dict, Any, Optional
from ..database import redis_client
import numpy as np
import json

INDEX_KEY = "vec_index_v1"


def _safe_hgetall(key: str) -> Dict[str, str]:
    """Safely get all hash fields from Redis, handling awaitables."""
    try:
        result = redis_client.hgetall(key)
        # If result is awaitable, we can't resolve it in sync context
        if hasattr(result, '__await__'):
            # Return empty dict for awaitable results in sync context
            return {}
        # If result is a dict with bytes values, decode them
        if isinstance(result, dict):
            decoded_result = {}
            for k, v in result.items():
                key_str = k.decode('utf-8') if isinstance(k, bytes) else str(k)
                val_str = v.decode('utf-8') if isinstance(v, bytes) else str(v)
                decoded_result[key_str] = val_str
            return decoded_result
        # If result is not a dict, return empty dict
        return {}
    except Exception:
        return {}


def index_vectors(vectors: Dict[str, List[float]]):
    """Index vectors in Redis as a simple hash for demo.
    vectors: {id: vector}
    """
    redis_client.hset(INDEX_KEY, mapping={k: json.dumps(v) for k, v in vectors.items()})


def search_vector(query: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
    """Brute-force search over indexed vectors in Redis. Returns list of {id, score}.
    Replace with ANN store for production.
    """
    all_items = _safe_hgetall(INDEX_KEY)
    if not all_items:
        return []
    q = np.array(query)
    results = []
    for k, v in all_items.items():
        try:
            vec = np.array(json.loads(v))
            denom = np.linalg.norm(q) * np.linalg.norm(vec)
            sim = float(np.dot(q, vec) / denom) if denom > 0 else 0.0
            results.append({"id": k, "score": sim})
        except Exception:
            continue
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
