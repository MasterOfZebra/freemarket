import sqlite3

# Подключаемся к базе данных
conn = sqlite3.connect('exchange.db')
cursor = conn.cursor()

# Получаем список всех таблиц
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Таблицы в базе данных:")
for table in tables:
    print(f"- {table[0]}")

# Если есть таблицы, проверим структуру таблицы users
if tables:
    print("\nСтруктура таблицы users:")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

conn.close()
