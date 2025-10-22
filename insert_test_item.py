import sqlite3
from datetime import datetime

conn = sqlite3.connect('exchange.db')
cur = conn.cursor()
cur.execute(
    "INSERT INTO items (user_id, title, description, category, kind, offers, wants, active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    (
        1,
        "Test Item",
        "Test description",
        "test_category",
        1,
        "['offer1', 'offer2']",
        "['want1', 'want2']",
        1,
        datetime.now().isoformat(" ")
    )
)
conn.commit()
conn.close()
print("Test item inserted.")
