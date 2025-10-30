#!/bin/bash
# Скрипт резервного копирования базы данных FreeMarket
# Использование: bash scripts/backup_db.sh

set -e

PROJECT_DIR="/opt/freemarket"
BACKUP_DIR="/backup/freemarket"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
COMPOSE_FILE="docker-compose.prod.yml"

# Создание директории для бэкапов, если её нет
mkdir -p "$BACKUP_DIR"

cd "$PROJECT_DIR"

echo "Создание бэкапа базы данных..."
docker compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U assistadmin_pg assistance_kz > "$BACKUP_DIR/backup_${TIMESTAMP}.sql"

# Сжатие бэкапа
echo "Сжатие бэкапа..."
gzip "$BACKUP_DIR/backup_${TIMESTAMP}.sql"

# Удаление старых бэкапов (старше 7 дней)
echo "Очистка старых бэкапов (старше 7 дней)..."
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete

echo "✓ Бэкап создан: $BACKUP_DIR/backup_${TIMESTAMP}.sql.gz"
echo "  Размер: $(du -h "$BACKUP_DIR/backup_${TIMESTAMP}.sql.gz" | cut -f1)"

