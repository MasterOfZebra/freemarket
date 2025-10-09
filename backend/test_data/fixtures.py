# Фикстуры для тестирования matching engine
from backend.models import User, Item
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

def create_users(session: Session):
    users = [
        User(username="user_A", trust_score=0.9),
        User(username="user_B", trust_score=0.8),
        User(username="user_C", trust_score=0.7),
    ]
    session.add_all(users)
    session.commit()
    return users

def create_items(session: Session, users):
    now = datetime.utcnow()
    items = [
        Item(user_id=users[0].id, category="Электроника", title="iPhone", offers=["айфон"], wants=["книга"], active=True, expires_at=now + timedelta(days=10)),
        Item(user_id=users[1].id, category="Книги", title="Роман", offers=["роман"], wants=["айфон"], active=True, expires_at=now + timedelta(days=10)),
        Item(user_id=users[2].id, category="Инструменты", title="Шуруповёрт", offers=["шуруповёрт"], wants=["роман"], active=True, expires_at=now + timedelta(days=10)),
        # Истёкший предмет
        Item(user_id=users[0].id, category="Книги", title="Старая книга", offers=["книга"], wants=["шуруповёрт"], active=True, expires_at=now - timedelta(days=1)),
    ]
    session.add_all(items)
    session.commit()
    return items
