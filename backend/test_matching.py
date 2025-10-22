import pytest
from .test_data.fixtures import create_users, create_items
from .models import Item
from datetime import datetime

def test_filter_expired_items(session):
    users = create_users(session)
    items = create_items(session, users)
    now = datetime.utcnow()
    active_items = session.query(Item).filter(Item.expires_at > now, Item.active == True).all()
    assert all(i.expires_at > now and i.active for i in active_items)

def test_match_same_category_higher_score(session):
    # TODO: реализовать сравнение score для одной и разных категорий
    pass

def test_description_similarity(session):
    # TODO: реализовать проверку текстового сходства
    pass

def test_mutual_match_flow(session):
    # TODO: реализовать тест взаимных совпадений
    pass

def test_self_match_excluded(session):
    # TODO: реализовать тест исключения self-match
    pass

def test_matching_performance(session):
    # TODO: реализовать тест производительности
    pass
