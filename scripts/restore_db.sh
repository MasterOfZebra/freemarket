#!/bin/bash
# Скрипт восстановления базы данных FreeMarket из бэкапа
# Использование: bash scripts/restore_db.sh <backup_file.sql.gz>
# Пример: bash scripts/restore_db.sh /backup/freemarket/backup_20250101_120000.sql.gz

set -e

if [ -z "$1" ]; then
    echo "Ошибка: Укажите путь к файлу бэкапа"
    echo "Использование: bash scripts/restore_db.sh <backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"
PROJECT_DIR="/opt/freemarket"
COMPOSE_FILE="docker-compose.prod.yml"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Ошибка: Файл бэкапа не найден: $BACKUP_FILE"
    exit 1
fi

cd "$PROJECT_DIR"

echo "⚠ ВНИМАНИЕ: Восстановление базы данных удалит все текущие данные!"
read -p "Продолжить? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Восстановление отменено"
    exit 0
fi

echo "Распаковка бэкапа..."
TEMP_SQL=$(mktemp)
gunzip -c "$BACKUP_FILE" > "$TEMP_SQL"

echo "Восстановление базы данных..."
docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U assistadmin_pg -d assistance_kz < "$TEMP_SQL"

rm "$TEMP_SQL"

echo "✓ База данных восстановлена из: $BACKUP_FILE"

