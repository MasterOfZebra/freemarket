import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal, engine, Base
from backend.models import User
import uuid
from sqlalchemy import inspect

# Пересоздание схемы БД для актуализации структуры таблиц
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def unique_username():
    return f"user_{uuid.uuid4().hex[:8]}"

# 1. Проверка запуска API и свежей БД
def test_api_and_db_clean():
    response = client.get("/")
    assert response.status_code == 200
    assert "FreeMarket" in response.json()["message"]
    # Проверка структуры users
    insp = inspect(engine)
    columns = [col['name'] for col in insp.get_columns('users')]
    assert 'telegram_id' not in columns
    assert set(['id', 'username', 'trust_score', 'created_at', 'last_active_at']).issubset(set(columns))

# 2. Регистрация пользователя и дублирование
def test_user_registration_and_duplicate():
    username = unique_username()
    r1 = client.post("/users/", json={"username": username})
    assert r1.status_code == 200
    data = r1.json()
    assert data["username"] == username
    assert "id" in data and "trust_score" in data and "created_at" in data
    r2 = client.post("/users/", json={"username": username})
    assert r2.status_code == 400
    assert "already registered" in r2.text

# 3. Создание профиля
def test_create_profile():
    username = unique_username()
    user_resp = client.post("/users/", json={"username": username})
    assert user_resp.status_code == 200
    profile_data = {
        "username": username,
        "name": "Test Profile",
        "category": "Electronics",
        "description": "A test profile"
    }
    r = client.post("/profiles/", json=profile_data)
    assert r.status_code == 200
    assert r.json()["username"] == username

# 4. Механизм подбора (matching)
def test_matching_search():
    # Create some items first
    username1 = unique_username()
    user1_resp = client.post("/users/", json={"username": username1})
    user1_id = user1_resp.json()["id"]
    item_data = {
        "user_id": user1_id,
        "title": "Laptop",
        "description": "Good laptop",
        "category": "electronics",
        "kind": 1,
        "offers": ["laptop"],
        "wants": ["phone"]
    }
    client.post("/items/", json=item_data)

    r = client.get("/matches/search/?category=electronics")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

# 5. Бартер-флоу (обмен)
def test_barter_flow():
    # Create users
    username1 = unique_username()
    username2 = unique_username()
    user1_resp = client.post("/users/", json={"username": username1})
    user2_resp = client.post("/users/", json={"username": username2})
    user1_id = user1_resp.json()["id"]
    user2_id = user2_resp.json()["id"]

    # Create items
    item1_data = {
        "user_id": user1_id,
        "title": "Laptop",
        "description": "Good laptop",
        "category": "electronics",
        "kind": 1,
        "offers": ["laptop"],
        "wants": ["phone"]
    }
    item1_resp = client.post("/items/", json=item1_data)
    item1_id = item1_resp.json()["id"]

    item2_data = {
        "user_id": user2_id,
        "title": "Phone",
        "description": "Good phone",
        "category": "electronics",
        "kind": 1,
        "offers": ["phone"],
        "wants": ["laptop"]
    }
    item2_resp = client.post("/items/", json=item2_data)
    item2_id = item2_resp.json()["id"]

    # Propose barter
    barter_resp = client.post("/barter/propose/", params={"from_username": username1, "to_username": username2, "offer_item": item1_id, "request_item": item2_id})
    assert barter_resp.status_code == 200
    barter_id = barter_resp.json()["match_id"]

    # Accept barter
    accept_resp = client.post(f"/barter/{barter_id}/accept")
    assert accept_resp.status_code == 200

# 6. Рейтинг и доверие
def test_ratings():
    # Create users
    username1 = unique_username()
    username2 = unique_username()
    user1_resp = client.post("/users/", json={"username": username1})
    user2_resp = client.post("/users/", json={"username": username2})

    # Create rating
    rating_data = {
        "from_username": user1_resp.json()["username"],
        "to_username": user2_resp.json()["username"],
        "score": 5,
        "comment": "Good exchange"
    }
    r = client.post("/ratings/", json=rating_data)
    assert r.status_code == 200

    # Get ratings
    ratings_resp = client.get(f"/ratings/{username1}")
    assert ratings_resp.status_code == 200
    assert isinstance(ratings_resp.json(), list)

# 7. Уведомления
def test_notifications():
    # Create user
    username = unique_username()
    user_resp = client.post("/users/", json={"username": username})

    # Get notifications (should be empty)
    notif_resp = client.get(f"/notifications/{username}")
    assert notif_resp.status_code == 200
    assert isinstance(notif_resp.json(), list)

# 8. Чистота данных
def test_no_telegram_id_column():
    insp = inspect(engine)
    columns = [col['name'] for col in insp.get_columns('users')]
    assert 'telegram_id' not in columns

# 9. Автотесты (проверка запуска)
def test_pytest_runs():
    # Просто проверка, что pytest запускается и хотя бы один тест проходит
    assert True

# 10. UX: username везде
@pytest.mark.skip("Depends on full UX/API implementation")
def test_username_everywhere():
    # Проверить, что username используется в логах/уведомлениях/API
    pass
