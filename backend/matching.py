from sqlalchemy.orm import Session
from .models import Item, Match, User
from .crud import create_match, create_notification
from .schemas import NotificationCreate
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

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
    # Simple rule-based filtering
    candidates = db.query(Item).filter(
        Item.category == item.category,  # Same category
        Item.user_id != item.user_id,    # Not own item
        Item.active == True,
        Item.kind != item.kind          # Opposite kind (offer vs want)
    ).all()

    return candidates

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

        final_score = score + trust_bonus

        matches.append({
            "item_a": item.id,
            "item_b": candidate.id,
            "score": final_score,
            "computed_by": "tfidf_similarity"
        })

    # Sort by score descending
    matches.sort(key=lambda x: x["score"], reverse=True)

    return matches
