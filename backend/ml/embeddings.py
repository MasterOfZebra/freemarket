"""
Embeddings helper with Redis caching (synchronous).
No async/await usage to match sync stack.
"""
import numpy as np
import logging
from backend.database import redis_client

logger = logging.getLogger(__name__)

EMBED_DIM = 768
EMBED_TTL = 3600

try:
    from sentence_transformers import SentenceTransformer
    _MODEL = SentenceTransformer('all-MiniLM-L6-v2')
except Exception:
    _MODEL = None
    logger.info("sentence-transformers unavailable, using deterministic fallback")


def _cache_key(text: str) -> str:
    return f"emb:bin:v1:{hash(text) % 1_000_000_007}"


def _fallback_embedding(text: str) -> np.ndarray:
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    return rng.random(EMBED_DIM, dtype=np.float32)


def get_embedding(text: str) -> np.ndarray:
    """Return embedding as np.ndarray[float32], cached in Redis as raw bytes."""
    key = _cache_key(text)
    try:
        cached = redis_client.get(key)
        if isinstance(cached, (bytes, bytearray)):
            try:
                arr = np.frombuffer(cached, dtype=np.float32)
                if arr.size == EMBED_DIM:
                    return arr
            except Exception:
                pass
    except Exception as e:
        logger.debug(f"redis get failed: {e}")

    if _MODEL is not None:
        try:
            emb = np.asarray(_MODEL.encode(text), dtype=np.float32)
        except Exception as e:
            logger.debug(f"model encode failed, using fallback: {e}")
            emb = _fallback_embedding(text)
    else:
        emb = _fallback_embedding(text)

    try:
        redis_client.setex(key, EMBED_TTL, emb.tobytes())
    except Exception as e:
        logger.debug(f"redis setex failed: {e}")

    return emb


def external_get_embedding(text: str) -> np.ndarray:
    return get_embedding(text)
