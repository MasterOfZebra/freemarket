"""
Contextual bandit learning stubs: UCB1 and Thompson Sampling.
State is stored in Redis as simple counters for demo/prototyping.
"""
from typing import Dict, Tuple
from backend.ml import embeddings
from backend.database import redis_client
import math

# Keys namespace
NAMESPACE = "ab_bandit"


def _key(k: str) -> str:
    return f"{NAMESPACE}:{k}"


def _safe_hget(key: str, field: str, default: str = "0") -> str:
    """Safely get hash field value from Redis, handling awaitables."""
    try:
        result = redis_client.hget(key, field)
        # If result is awaitable, we're in sync context so try to get result
        if hasattr(result, '__await__'):
            # Try to get the result if it's a Future-like object
            if hasattr(result, 'result'):
                import asyncio
                return str(asyncio.run(result) if asyncio.iscoroutine(result) else default)
            else:
                return default
        # If result is bytes, decode it
        if isinstance(result, bytes):
            return result.decode('utf-8') or default
        # If result is string or None
        return str(result or default)
    except Exception:
        return default


class UCB1:
    """Simple UCB1 bandit for choosing arms (configs).
    Stores wins and trials in Redis using hash maps.
    """

    def __init__(self, arms: Tuple[str, ...]):
        self.arms = list(arms)
        # Initialize counts as strings
        for arm in self.arms:
            redis_client.hset(_key("trials"), arm, "0")
            redis_client.hset(_key("wins"), arm, "0")

    def select(self) -> str:
        # Safely get hash values and convert to integers
        trials = {a: int(_safe_hget(_key("trials"), a, "0")) for a in self.arms}
        wins = {a: int(_safe_hget(_key("wins"), a, "0")) for a in self.arms}
        total_trials = sum(trials.values())
        if total_trials == 0:
            return self.arms[0]
        ucb_scores = {}
        for a in self.arms:
            n = trials[a]
            mean = wins[a] / n if n > 0 else 0
            bonus = math.sqrt((2 * math.log(total_trials)) / n) if n > 0 else float('inf')
            ucb_scores[a] = mean + bonus
        return max(ucb_scores.items(), key=lambda x: x[1])[0]

    def update(self, arm: str, reward: float):
        redis_client.hincrby(_key("trials"), arm, 1)
        if reward > 0:
            redis_client.hincrby(_key("wins"), arm, int(reward))


class ThompsonBeta:
    """Thompson Sampling for binary rewards using Beta priors.
    Stores alpha/beta in Redis.
    """

    def __init__(self, arms: Tuple[str, ...]):
        self.arms = list(arms)
        for arm in self.arms:
            redis_client.hset(_key("alpha"), arm, "1")
            redis_client.hset(_key("beta"), arm, "1")

    def select(self) -> str:
        from random import betavariate
        samples = {}
        for a in self.arms:
            alpha = int(_safe_hget(_key("alpha"), a, "1"))
            beta = int(_safe_hget(_key("beta"), a, "1"))
            samples[a] = betavariate(alpha, beta)
        return max(samples.items(), key=lambda x: x[1])[0]

    def update(self, arm: str, reward: int):
        # reward: 1 for success, 0 for fail
        if reward:
            redis_client.hincrby(_key("alpha"), arm, 1)
        else:
            redis_client.hincrby(_key("beta"), arm, 1)
