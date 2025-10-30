#!/bin/bash
# Быстрые команды для управления FreeMarket
# Использование: source scripts/quick_commands.sh
# или: bash scripts/quick_commands.sh <command>

PROJECT_DIR="/opt/freemarket"
COMPOSE_FILE="docker-compose.prod.yml"

cd "$PROJECT_DIR" || exit 1

case "$1" in
    "start")
        echo "🚀 Запуск всех сервисов..."
        docker compose -f "$COMPOSE_FILE" up -d
        ;;
    "stop")
        echo "🛑 Остановка всех сервисов..."
        docker compose -f "$COMPOSE_FILE" down
        ;;
    "restart")
        echo "🔄 Перезапуск всех сервисов..."
        docker compose -f "$COMPOSE_FILE" restart
        ;;
    "logs")
        echo "📋 Просмотр логов..."
        docker compose -f "$COMPOSE_FILE" logs -f "${2:-}"
        ;;
    "status")
        echo "📊 Статус контейнеров..."
        docker compose -f "$COMPOSE_FILE" ps
        ;;
    "health")
        echo "💚 Проверка здоровья сервисов..."
        echo "Backend: $(curl -s http://localhost:8000/health || echo 'недоступен')"
        echo "API через Nginx: $(curl -s http://localhost/api/health || echo 'недоступен')"
        echo "Frontend: $(curl -s -o /dev/null -w '%{http_code}' http://localhost/ || echo 'недоступен')"
        ;;
    "update")
        echo "🔄 Обновление кода и переразвёртывание..."
        git pull
        docker compose -f "$COMPOSE_FILE" build --no-cache
        docker compose -f "$COMPOSE_FILE" up -d
        docker compose -f "$COMPOSE_FILE" exec -T backend alembic upgrade head
        echo "✓ Обновление завершено"
        ;;
    "backup")
        echo "💾 Создание бэкапа..."
        bash scripts/backup_db.sh
        ;;
    "shell-backend")
        echo "🐚 Подключение к контейнеру backend..."
        docker compose -f "$COMPOSE_FILE" exec backend bash
        ;;
    "shell-postgres")
        echo "🐚 Подключение к контейнеру postgres..."
        docker compose -f "$COMPOSE_FILE" exec postgres psql -U assistadmin_pg -d assistance_kz
        ;;
    "clean")
        echo "🧹 Очистка неиспользуемых ресурсов Docker..."
        docker system prune -a --volumes
        ;;
    *)
        echo "FreeMarket - Быстрые команды"
        echo ""
        echo "Использование: bash scripts/quick_commands.sh <command>"
        echo ""
        echo "Команды:"
        echo "  start         - Запуск всех сервисов"
        echo "  stop          - Остановка всех сервисов"
        echo "  restart       - Перезапуск всех сервисов"
        echo "  logs [service] - Просмотр логов (опционально указать сервис)"
        echo "  status        - Статус контейнеров"
        echo "  health        - Проверка здоровья сервисов"
        echo "  update        - Обновление кода и переразвёртывание"
        echo "  backup        - Создание бэкапа БД"
        echo "  shell-backend - Подключение к контейнеру backend"
        echo "  shell-postgres - Подключение к контейнеру postgres"
        echo "  clean         - Очистка неиспользуемых ресурсов Docker"
        echo ""
        echo "Примеры:"
        echo "  bash scripts/quick_commands.sh start"
        echo "  bash scripts/quick_commands.sh logs backend"
        echo "  bash scripts/quick_commands.sh update"
        ;;
esac

