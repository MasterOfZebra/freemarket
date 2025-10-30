from sqlalchemy.orm import Session
from backend.models import Item, Match, User
from backend.crud import create_match, create_notification
from backend.schemas import NotificationCreate
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging
from typing import Any, List, Optional, Sequence, cast
try:
    from sentence_transformers import SentenceTransformer as ImportedSentenceTransformer
except Exception:  # Fallback stub for type-checking/runtime without package
    class SentenceTransformer:  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass
        def encode(self, text: str) -> List[float]:  # type: ignore
            return [0.0] * 384
try:
    import lightgbm as lgb
except Exception:
    class _DummyModel:
        def predict(self, features: Any) -> List[float]:
            try:
                arr = np.array(features)
                vals = np.clip(arr.mean(axis=1), 0, 1).tolist()
                return vals
            except Exception:
                return [0.5]
    class _DummyLGB:
        def Dataset(self, X: Any, label: Any = None) -> Any:
            return {"X": X, "label": label}
        def train(self, params: Any, data: Any, num_boost_round: int = 10, valid_sets: Any = None, early_stopping_rounds: Optional[int] = None) -> Any:
            return _DummyModel()
    lgb = _DummyLGB()  # type: ignore
from sklearn.model_selection import train_test_split
import networkx as nx
from collections import defaultdict
from datetime import datetime, timedelta
from backend.database import redis_client  # Import Redis client
import json

# Set up logging
logger = logging.getLogger(__name__)

# Global vectorizer
vectorizer = TfidfVectorizer(stop_words='english')

# Use shared embeddings helper (handles model loading and Redis TTL)

# Category-specific weights for scoring
CATEGORY_WEIGHTS = {
    'electronics': {'text': 0.4, 'attributes': 0.6},  # More weight on attributes for tech
    'services': {'text': 0.7, 'attributes': 0.3},     # More weight on text for services
    'default': {'text': 0.5, 'attributes': 0.5}       # Balanced for others
}

# Placeholder for learn-to-rank model (would be trained on user interaction data)
ltr_model = None

# A/B testing configurations
AB_TEST_CONFIGS = {
    'control': {'score_threshold': 0.5, 'top_k': 5},
    'variant_a': {'score_threshold': 0.6, 'top_k': 3},  # Stricter matching
    'variant_b': {'score_threshold': 0.4, 'top_k': 7}   # Looser matching
}

# Multi-level matching configuration
MATCHING_LEVELS = [
    {"min_score": 0.8, "max_results": 10, "reason": "high_confidence"},
    {"min_score": 0.6, "max_results": 20, "reason": "medium_confidence"},
    {"min_score": 0.4, "max_results": 30, "reason": "expanded_search"}
]

def find_matches(db: Session, user_id: int):
    """Find matches for user's items"""
    user_items = db.query(Item).filter(Item.user_id == user_id, Item.active == True).all()

    for item in user_items:
        # Find potential matches
        candidates = find_candidates(db, item)

        # Score candidates
        scored_matches = score_candidates(item, candidates)

        # Create matches and notifications
        for match_data in scored_matches[:5]:  # Top 5 matches
            # Create match record
            match = create_match(db, match_data)

            # Create notification
            partner_item = db.query(Item).filter(Item.id == match_data.item_b).first()
            if partner_item:
                partner_user = db.query(User).filter(User.id == partner_item.user_id).first()
            else:
                continue

            if partner_user:
                notification_payload = {
                    "match_id": match.id,
                    "partner_name": partner_user.username or f"User {partner_user.id}",
                    "category": item.category,
                    "description": item.description or item.title,
                    "contact": partner_user.contact,
                    "rating": partner_user.trust_score,
                    "rating_count": len(partner_user.ratings_received)
                }

                create_notification(db, NotificationCreate(
                    user_id=int(partner_user.id if isinstance(partner_user.id, int) else partner_user.id.value),
                    payload=notification_payload
                ))

def find_candidates(db: Session, item: Item):
    """Find candidate items for matching"""
    # Get the item owner's locations
    item_user = db.query(User).filter(User.id == item.user_id).first()
    if not item_user or not item_user.locations:
        return []

    # Find candidates in same category, opposite kind
    candidates = db.query(Item).filter(
        Item.category == item.category,  # Same category
        Item.user_id != item.user_id,    # Not own item
        Item.active == True,
        Item.kind != item.kind          # Opposite kind (offer vs want)
    ).all()

    # Filter by location overlap: at least one location must match
    matched_candidates = []
    for candidate in candidates:
        candidate_user = db.query(User).filter(User.id == candidate.user_id).first()

        # Check if there's at least one location overlap
        if candidate_user and candidate_user.locations:
            if any(loc in item_user.locations for loc in candidate_user.locations):
                matched_candidates.append(candidate)

    return matched_candidates

def score_candidates(item: Item, candidates):
    """Score candidates using text similarity"""
    if not candidates:
        return []

    # Prepare texts
    texts = [item.description or item.title or ""] + \
            [(c.description or c.title or "") for c in candidates]

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
        # Convert sparse matrix to dense arrays for cosine similarity
        tfidf_dense = tfidf_matrix.todense()
        similarities = cosine_similarity(tfidf_dense[0:1], tfidf_dense[1:])[0] if tfidf_dense.shape[0] > 1 else np.array([0.0])
    except:
        # Fallback if not enough text
        similarities = [0.5] * len(candidates)

    # Create match data
    matches = []
    for i, candidate in enumerate(candidates):
        score = float(similarities[i]) if i < len(similarities) else 0.0

        # Adjust score based on trust
        candidate_user = candidate.user
        trust_bonus = min(candidate_user.trust_score * 0.1, 0.2)  # Max 0.2 bonus

        # Get location bonus: 0.1 bonus for matching locations
        item_user = db.query(User).filter(User.id == item.user_id).first()
        location_bonus = 0.0
        if item_user and item_user.locations and candidate_user.locations:
            matching_locations = set(item_user.locations) & set(candidate_user.locations)
            if matching_locations:
                location_bonus = 0.1  # Bonus for location overlap

        # Get category-specific weights
        cat_key = str(getattr(item, 'category', 'default') or 'default').lower()
        weights = CATEGORY_WEIGHTS.get(cat_key, CATEGORY_WEIGHTS['default'])

        # Calculate final score with category-specific weighting + bonuses
        final_score = score * weights['text'] + trust_bonus * weights['attributes'] + location_bonus

        matches.append({
            "item_a": item.id,
            "item_b": candidate.id,
            "score": final_score,
            "computed_by": "tfidf_similarity"
        })

    # Sort by score descending
    matches.sort(key=lambda x: x["score"], reverse=True)

    return matches

def score_pair(item_a, item_b):
    """Calculate the score for a pair of items using dynamic learn-to-rank model or fallback.

    Key change: use cross offers/wants semantic similarity:
      - A.offers vs B.wants
      - B.offers vs A.wants
    """
    # Get category weights (for fallback)
    category = str(getattr(item_a, 'category', 'default') or 'default').lower()
    weights = CATEGORY_WEIGHTS.get(category, CATEGORY_WEIGHTS['default'])

    # Build offers/wants text blobs
    offers_a_txt = " ".join(list(getattr(item_a, 'offers', None) or []))
    wants_a_txt = " ".join(list(getattr(item_a, 'wants', None) or []))
    offers_b_txt = " ".join(list(getattr(item_b, 'offers', None) or []))
    wants_b_txt = " ".join(list(getattr(item_b, 'wants', None) or []))

    # Compute cross-directional similarities
    def safe_cos_sim(txt1: str, txt2: str) -> float:
        if not txt1 or not txt2:
            return 0.0
        try:
            v1 = np.asarray(get_embedding(txt1), dtype=np.float32).reshape(1, -1)
            v2 = np.asarray(get_embedding(txt2), dtype=np.float32).reshape(1, -1)
            return float(cosine_similarity(v1, v2)[0][0])
        except Exception as e:
            logger.debug(f"safe_cos_sim error: {e}")
            return 0.0

    score_ab = safe_cos_sim(offers_a_txt, wants_b_txt)  # A offers -> B wants
    score_ba = safe_cos_sim(offers_b_txt, wants_a_txt)  # B offers -> A wants
    text_similarity = max(score_ab, score_ba)

    # Debug prints to surface during tests
    try:
        print(f">>> SCORE_AB={score_ab:.3f} SCORE_BA={score_ba:.3f} FINAL={text_similarity:.3f}")
        logger.debug(
            "score_pair cross-texts: offers_a='%s' wants_a='%s' offers_b='%s' wants_b='%s'",
            offers_a_txt, wants_a_txt, offers_b_txt, wants_b_txt,
        )
    except Exception:
        pass

    # Tag similarity (wants/offers) by exact token overlap as an additional signal
    wants_a = set(list(getattr(item_a, 'wants', None) or []))
    offers_b = set(list(getattr(item_b, 'offers', None) or []))
    wants_offers_sim = len(wants_a & offers_b) / max(len(wants_a | offers_b), 1)

    offers_a = set(list(getattr(item_a, 'offers', None) or []))
    wants_b = set(list(getattr(item_b, 'wants', None) or []))
    offers_wants_sim = len(offers_a & wants_b) / max(len(offers_a | wants_b), 1)

    tag_similarity = (wants_offers_sim + offers_wants_sim) / 2

    # Value overlap
    value_overlap_score = value_overlap(
        item_a.value_min, item_a.value_max,
        item_b.value_min, item_b.value_max
    )

    # Value density (inverse of range width, higher density = more precise value)
    def calc_density(min_val, max_val):
        if min_val is not None and max_val is not None and max_val > min_val:
            return 1.0 / (max_val - min_val)
        return 0.0  # No range or invalid

    density_a = calc_density(item_a.value_min, item_a.value_max)
    density_b = calc_density(item_b.value_min, item_b.value_max)
    value_density = (density_a + density_b) / 2  # Average density

    # Trust difference
    trust_a = item_a.user.trust_score if item_a.user else 0.5
    trust_b = item_b.user.trust_score if item_b.user else 0.5
    trust_diff = abs(trust_a - trust_b)

    # Category code for model
    category_map = {'electronics': 0, 'services': 1, 'default': 2}
    category_code = category_map.get(category, 2)

    # Use learn-to-rank model if trained
    if ltr_model is not None:
        features = np.array([[text_similarity, tag_similarity, value_overlap_score, trust_diff, category_code, value_density]])
        prediction = ltr_model.predict(features)
        # Convert to numpy array if it's a sparse matrix
        # Convert prediction to a numpy array if it's not already
        prediction = np.asarray(prediction).flatten()
        score = float(prediction[0])
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
    else:
        # Fallback to weighted combination
        score = (weights['text'] * text_similarity +
                 weights['attributes'] * tag_similarity +
                 0.2 * value_overlap_score)

    return score, text_similarity, tag_similarity, value_overlap_score

def match_for_item(db: Session, item_id: int, top_k: int = 5):
    """Find top-k matches for a given item."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return []

    # Get A/B test config
    user_id_val = int(getattr(item, 'user_id', 0) or 0)
    ab_config = get_ab_test_config(user_id_val)
    threshold = ab_config['score_threshold']
    top_k = ab_config['top_k']

    candidates = find_candidates(db, item)
    scored_matches = []
    skipped_filters = []

    for candidate in candidates:
        # Check additional filters
        if not check_additional_filters(item, candidate):
            skipped_filters.append({
                "candidate_id": candidate.id,
                "reason": "failed_additional_filters"
            })
            continue

        score, text_sim, tag_sim, val_overlap = score_pair(item, candidate)
        if score > threshold:  # Use A/B test threshold
            scored_matches.append({
                "item_a": item.id,
                "item_b": candidate.id,
                "score": score,
                "reasons": {
                    "text_similarity": text_sim,
                    "tag_similarity": tag_sim,
                    "value_overlap": val_overlap,
                    "category_weights": CATEGORY_WEIGHTS.get(str(getattr(item, 'category', 'default') or 'default').lower(), CATEGORY_WEIGHTS['default']),
                    "ab_test_config": ab_config
                },
                "explanation": generate_match_explanation(text_sim, tag_sim, val_overlap, score),
                "status": "new"
            })
        else:
            skipped_filters.append({
                "candidate_id": candidate.id,
                "reason": "score_below_threshold",
                "score": score
            })

    # Log skipped filters for debugging
    if skipped_filters:
        logger.info(f"Skipped {len(skipped_filters)} candidates for item {item_id}: {skipped_filters}")

    # Apply multi-level matching
    final_matches = apply_multi_level_matching(scored_matches)

    return final_matches[:top_k]

def check_additional_filters(item_a, item_b):
    """Check additional filters for matching."""
    # Example: Check if locations match (if location is available)
    if hasattr(item_a, 'location') and hasattr(item_b, 'location'):
        if item_a.location and item_b.location and item_a.location != item_b.location:
            return False

    # Add more filters as needed
    return True


def train_ltr_model(sample_data):
    """Train a learn-to-rank model for dynamic scoring weights."""
    global ltr_model
    # Features: text_sim, tag_sim, value_overlap, trust_diff, category_code, value_density
    # Category mapping for encoding
    category_map = {'electronics': 0, 'services': 1, 'default': 2}
    sample_data['category_code'] = sample_data['category'].map(category_map).fillna(2)

    X = sample_data[['text_sim', 'tag_sim', 'value_overlap', 'trust_diff', 'category_code', 'value_density']]
    y = sample_data['score']  # Target score for regression

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    train_data = lgb.Dataset(X_train, label=y_train)
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9
    }
    ltr_model = lgb.train(params, train_data, num_boost_round=100, valid_sets=[train_data])

def personalized_score(item_a, item_b, user_trust_a, user_trust_b):
    """Get personalized score using learn-to-rank."""
    if ltr_model is None:
        # Fallback to basic score
        return score_pair(item_a, item_b)[0]

    score, text_sim, tag_sim, _ = score_pair(item_a, item_b)
    trust_diff = abs(user_trust_a - user_trust_b)

    features = np.array([[text_sim, tag_sim, trust_diff]])
    prediction = ltr_model.predict(features)
    # If prediction is a numpy array or list, just index the first element
    if isinstance(prediction, (np.ndarray, list)):
        personalized_score = prediction[0]
    else:
        # Fallback: try to convert to numpy array and get the first element
        personalized_score = np.array(prediction).item(0)

    return personalized_score

def build_exchange_graph(db: Session):
    """Build a graph of potential exchanges."""
    items = db.query(Item).filter(Item.active == True).all()
    G = nx.DiGraph()

    for item in items:
        user_id = int(getattr(item, 'user_id', 0) or 0)
        offers = set(list(getattr(item, 'offers', None) or []))
        wants = set(list(getattr(item, 'wants', None) or []))

        # Add edges: user -> wanted items
        for want in wants:
            # Find items that offer what this user wants
            matching_items = []
            for i in items:
                other_uid = int(getattr(i, 'user_id', 0) or 0)
                if other_uid == user_id:
                    continue
                i_offers = set(list(getattr(i, 'offers', None) or []))
                if want in i_offers:
                    matching_items.append(i)
            for match_item in matching_items:
                G.add_edge(user_id, int(getattr(match_item, 'user_id', 0) or 0),
                          item_id=item.id, match_item_id=match_item.id,
                          weight=score_pair(item, match_item)[0])

    return G

def find_exchange_cycles(G, max_cycle_length=3):
    """Find cycles in the exchange graph representing multi-party exchanges."""
    cycles = []
    for cycle in nx.simple_cycles(G, length_bound=max_cycle_length):
        if len(cycle) >= 3:  # At least 3 parties
            # Calculate cycle score (product of edge weights)
            cycle_score = 1.0
            for i in range(len(cycle)):
                u, v = cycle[i], cycle[(i+1) % len(cycle)]
                if G.has_edge(u, v):
                    cycle_score *= G[u][v]['weight']

            cycles.append({
                'cycle': cycle,
                'score': cycle_score,
                'items': [G[u][v]['item_id'] for u, v in zip(cycle, cycle[1:] + [cycle[0]])]
            })

    # Sort by score descending
    cycles.sort(key=lambda x: x['score'], reverse=True)
    return cycles[:5]  # Top 5 cycles

def find_max_weight_matching(G):
    """Find maximum weight matching for multi-party exchanges."""
    # Use NetworkX max_weight_matching for general graphs
    matching_set = nx.max_weight_matching(G, weight='weight')

    # Extract matched edges with weights
    matched_exchanges = []
    for u, v in matching_set:
        a, b = (u, v) if u < v else (v, u)
        if G.has_edge(a, b):
            weight = G[a][b].get('weight', 0.0)
            item_id = G[a][b].get('item_id')
            matched_exchanges.append({'users': [a, b], 'weight': weight, 'item_id': item_id})

    # Sort by weight
    matched_exchanges.sort(key=lambda x: x['weight'], reverse=True)
    return matched_exchanges[:10]  # Top 10 matches

def apply_trust_decay(db: Session):
    """Apply trust decay for older listings."""
    # Decay trust score by 5% per month for inactive users
    cutoff_date = datetime.utcnow() - timedelta(days=30)

    db.query(User).filter(
        User.last_active_at < cutoff_date
    ).update({
        "trust_score": User.trust_score * 0.95
    })
    db.commit()

def value_overlap(a_min, a_max, b_min, b_max):
    """Calculate overlap between two ranges as fraction of first range.

    Returns intersection_length / first_range_length.
    - Returns 1.0 for identical ranges, including identical zero-length ranges.
    - Returns 0.0 if no overlap or if inputs are invalid.
    """
    # Validate inputs
    if any(v is None for v in (a_min, a_max, b_min, b_max)):
        return 0.0

    # Normalize ordering
    if a_min > a_max:
        a_min, a_max = a_max, a_min
    if b_min > b_max:
        b_min, b_max = b_max, b_min

    # Compute intersection length
    left = max(a_min, b_min)
    right = min(a_max, b_max)
    inter = max(0.0, right - left)

    # Special case: identical zero-length ranges
    if a_min == a_max == b_min == b_max:
        return 1.0

    # Ensure no overlap returns 0.0
    if inter == 0.0:
        return 0.0

    # First range length
    range_a = max(0.0, a_max - a_min)
    if range_a == 0.0:
        return 0.0

    return float(inter / range_a)

def apply_multi_level_matching(scored_matches):
    """Apply multi-level matching to get optimal number of results."""
    result = []

    for level in MATCHING_LEVELS:
        level_matches = [m for m in scored_matches if m['score'] >= level['min_score']]
        level_matches.sort(key=lambda x: x["score"], reverse=True)

        for match in level_matches[:level['max_results']]:
            if match not in result:  # Avoid duplicates
                match['reason'] = level['reason']
                result.append(match)

        if len(result) >= 10:  # Stop if we have enough results
            break

    return result

def generate_match_explanation(text_sim, tag_sim, val_overlap, total_score):
    """Generate human-readable explanation for a match."""
    explanations = []

    if text_sim > 0.7:
        explanations.append(f"текстовое сходство {text_sim:.0%}")
    elif text_sim > 0.5:
        explanations.append(f"похожее описание {text_sim:.0%}")

    if tag_sim > 0.8:
        explanations.append(f"идеальное совпадение тегов {tag_sim:.0%}")
    elif tag_sim > 0.5:
        explanations.append(f"хорошее совпадение тегов {tag_sim:.0%}")

    if val_overlap > 0.8:
        explanations.append(f"ценности совпадают {val_overlap:.0%}")
    elif val_overlap > 0.5:
        explanations.append(f"ценности близки {val_overlap:.0%}")

    if explanations:
        return f"Совпадение на {total_score:.0%} из-за: " + ", ".join(explanations)
    else:
        return f"Общее совпадение {total_score:.0%}"

# ============================================================================
# CHAIN MATCHING INTEGRATION
# ============================================================================

def run_full_matching_pipeline(db: Session, user_id: Optional[int] = None):
    """
    Run complete matching pipeline:
    1. Standard bilateral matching (existing)
    2. Chain discovery (new feature)

    This function orchestrates both matching strategies to provide users
    with maximum exchange opportunities.

    Args:
        db: Database session
        user_id: Optional - if provided, only match this user's items
                 if None, match all users
    """

    logger.info("=== Starting full matching pipeline ===")

    try:
        # Phase 1: Standard bilateral matching
        if user_id:
            logger.info(f"Phase 1: Bilateral matching for user {user_id}")
            find_matches(db, user_id)
        else:
            logger.info("Phase 1: Bilateral matching for all users")
            all_users = db.query(User).filter(User.id > 0).all()
            for user in all_users:
                try:
                    find_matches(db, user.id)
                except Exception as e:
                    logger.error(f"Error matching user {user.id}: {e}")

        logger.info("Phase 1: Bilateral matching complete")

        # Phase 2: Chain discovery
        logger.info("Phase 2: Discovering exchange chains")
        try:
            from backend.chain_matching import discover_and_create_chains
            chains_created = discover_and_create_chains(db)
            logger.info(f"Phase 2: Created {chains_created} exchange chains")
        except Exception as e:
            logger.error(f"Error in chain discovery: {e}")

        logger.info("=== Full matching pipeline complete ===")

    except Exception as e:
        logger.error(f"Error in full matching pipeline: {e}")
        raise
