#!/bin/bash
# Полный скрипт развёртывания FreeMarket на сервере
# Использование: bash scripts/deploy/full_deployment.sh
# Запускается на production сервере

set -e  # Выход при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Конфигурация
PROJECT_DIR="/opt/freemarket"
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="/backup/freemarket"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Функции для логирования
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# Проверка прав root/sudo
check_permissions() {
    if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
        log_error "Требуются права sudo. Запустите скрипт с sudo или убедитесь, что текущий пользователь в группе docker."
        exit 1
    fi
}

# Этап 1: Подготовка сервера
stage1_prepare_server() {
    log_step "Этап 1: Подготовка сервера"

    log_info "1.1 Обновление системы..."
    sudo apt update && sudo apt upgrade -y

    log_info "1.2 Проверка установки Docker..."
    if ! command -v docker &> /dev/null; then
        log_warn "Docker не установлен. Устанавливаю Docker..."

        # Удаление старых версий (если есть)
        sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

        # Установка зависимостей
        sudo apt-get install -y \
            ca-certificates \
            curl \
            gnupg \
            lsb-release

        # Добавление официального GPG ключа Docker
        sudo mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

        # Добавление репозитория Docker
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

        # Установка Docker Engine
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

        log_info "Docker установлен успешно"
    else
        log_info "Docker уже установлен: $(docker --version)"
    fi

    log_info "1.3 Настройка Docker..."
    # Добавление текущего пользователя в группу docker (если еще не добавлен)
    if ! groups | grep -q docker; then
        sudo usermod -aG docker $USER
        log_warn "Пользователь добавлен в группу docker. Требуется перелогиниться или выполнить: newgrp docker"
    fi

    # Настройка автозапуска Docker
    sudo systemctl enable docker
    sudo systemctl start docker

    log_info "1.4 Установка дополнительных утилит..."
    sudo apt-get install -y git curl wget vim ufw || true

    log_info "1.5 Настройка файрвола..."
    # Разрешение SSH
    sudo ufw allow 22/tcp || true

    # Разрешение HTTP/HTTPS
    sudo ufw allow 80/tcp || true
    sudo ufw allow 443/tcp || true

    # Включение файрвола (если еще не включен)
    echo "y" | sudo ufw --force enable || true
    sudo ufw status

    log_info "✓ Этап 1 завершён"
}

# Этап 2: Клонирование проекта
stage2_clone_project() {
    log_step "Этап 2: Клонирование проекта"

    log_info "2.1 Создание директории проекта..."
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown $USER:$USER "$PROJECT_DIR"
    cd "$PROJECT_DIR" || exit 1

    log_info "2.2 Проверка наличия проекта..."
    if [ ! -d ".git" ]; then
        log_warn "Git репозиторий не найден. Инициализируйте репозиторий или скопируйте файлы проекта в $PROJECT_DIR"
        log_info "Для копирования через SCP используйте:"
        log_info "  scp -r /path/to/FreeMarket/* user@server:$PROJECT_DIR/"
    else
        log_info "Git репозиторий найден"
    fi

    log_info "2.3 Проверка структуры проекта..."
    required_files=("docker-compose.prod.yml" "docker/Dockerfile.backend" "docker/Dockerfile.frontend" "docker/Dockerfile.bot" "config/freemarket.nginx")
    missing_files=()

    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done

    if [ ${#missing_files[@]} -gt 0 ]; then
        log_error "Отсутствуют обязательные файлы:"
        for file in "${missing_files[@]}"; do
            log_error "  - $file"
        done
        exit 1
    fi

    log_info "✓ Этап 2 завершён"
}

# Этап 3: Настройка окружения
stage3_setup_environment() {
    log_step "Этап 3: Настройка окружения"

    cd "$PROJECT_DIR" || exit 1

    log_info "3.1 Проверка .env файла..."
    if [ ! -f .env ]; then
        log_warn ".env файл не найден. Создаю шаблон из .env.example..."

        if [ -f .env.example ]; then
            cp .env.example .env
            log_info "Файл .env создан из шаблона. ВАЖНО: Отредактируйте .env и установите реальные значения!"
            log_info "  nano .env"
        else
            log_error ".env.example не найден. Создайте .env вручную."
            exit 1
        fi
    else
        log_info ".env файл уже существует"
    fi

    # Установка безопасных прав доступа
    chmod 600 .env

    log_warn "ВАЖНО: Убедитесь, что в .env установлены реальные значения:"
    log_warn "  - DB_PASSWORD"
    log_warn "  - TELEGRAM_BOT_TOKEN"

    log_info "✓ Этап 3 завершён"
}

# Этап 4: Проверка конфигурации Docker
stage4_verify_docker_config() {
    log_step "Этап 4: Проверка конфигурации Docker"

    cd "$PROJECT_DIR" || exit 1

    log_info "4.1 Проверка docker-compose.prod.yml..."
    if docker compose -f "$COMPOSE_FILE" config > /dev/null 2>&1; then
        log_info "✓ docker-compose.prod.yml валиден"
    else
        log_error "docker-compose.prod.yml содержит ошибки!"
        docker compose -f "$COMPOSE_FILE" config
        exit 1
    fi

    log_info "4.2 Проверка Dockerfile'ов..."
    dockerfiles=("docker/Dockerfile.backend" "docker/Dockerfile.frontend" "docker/Dockerfile.bot")
    for dockerfile in "${dockerfiles[@]}"; do
        if [ -f "$dockerfile" ]; then
            log_info "✓ $dockerfile найден"
        else
            log_error "$dockerfile не найден!"
            exit 1
        fi
    done

    log_info "4.3 Проверка конфигурации Nginx..."
    if [ -f "config/freemarket.nginx" ]; then
        log_info "✓ config/freemarket.nginx найден"
    else
        log_error "config/freemarket.nginx не найден!"
        exit 1
    fi

    log_info "✓ Этап 4 завершён"
}

# Этап 5: Сборка Docker образов
stage5_build_images() {
    log_step "Этап 5: Сборка Docker образов"

    cd "$PROJECT_DIR" || exit 1

    log_info "5.1 Сборка всех образов (это может занять несколько минут)..."
    docker compose -f "$COMPOSE_FILE" build --no-cache

    if [ $? -ne 0 ]; then
        log_error "Ошибка при сборке образов!"
        exit 1
    fi

    log_info "5.2 Проверка созданных образов..."
    docker images | grep freemarket || log_warn "Образы freemarket не найдены в выводе docker images"

    log_info "✓ Этап 5 завершён"
}

# Этап 6: Запуск сервисов
stage6_start_services() {
    log_step "Этап 6: Запуск сервисов"

    cd "$PROJECT_DIR" || exit 1

    log_info "6.1 Запуск контейнеров в фоновом режиме..."
    docker compose -f "$COMPOSE_FILE" up -d

    if [ $? -ne 0 ]; then
        log_error "Ошибка при запуске контейнеров!"
        exit 1
    fi

    log_info "6.2 Ожидание готовности сервисов (макс. 60 секунд)..."
    for i in {1..12}; do
        sleep 5
        log_info "  Проверка готовности... попытка $i/12"

        # Проверка статуса контейнеров
        unhealthy=$(docker compose -f "$COMPOSE_FILE" ps | grep -c "unhealthy" || true)
        if [ "$unhealthy" -eq 0 ]; then
            log_info "Все контейнеры готовы"
            break
        fi
    done

    log_info "6.3 Проверка статуса контейнеров..."
    docker compose -f "$COMPOSE_FILE" ps

    log_info "✓ Этап 6 завершён"
}

# Этап 7: Применение миграций базы данных
stage7_apply_migrations() {
    log_step "Этап 7: Применение миграций базы данных"

    cd "$PROJECT_DIR" || exit 1

    log_info "7.1 Ожидание готовности PostgreSQL..."
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U assistadmin_pg > /dev/null 2>&1; then
            log_info "PostgreSQL готов"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
        log_info "  Ожидание PostgreSQL... попытка $attempt/$max_attempts"
    done

    if [ $attempt -eq $max_attempts ]; then
        log_error "PostgreSQL не готов после $max_attempts попыток!"
        exit 1
    fi

    log_info "7.2 Применение миграций Alembic..."
    docker compose -f "$COMPOSE_FILE" exec -T backend alembic upgrade head

    if [ $? -ne 0 ]; then
        log_warn "Предупреждение: Миграции могли уже быть применены или произошла ошибка"
    else
        log_info "✓ Миграции применены успешно"
    fi

    log_info "7.3 Проверка подключения к базе данных..."
    docker compose -f "$COMPOSE_FILE" exec -T backend python -c "
from backend.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version()'))
        print('✓ Подключение к базе данных успешно')
        print(result.fetchone()[0])
except Exception as e:
    print(f'✗ Ошибка подключения: {e}')
    exit(1)
" || log_warn "Не удалось проверить подключение к БД"

    log_info "✓ Этап 7 завершён"
}

# Этап 8: Проверка работоспособности
stage8_verify_health() {
    log_step "Этап 8: Проверка работоспособности"

    log_info "8.1 Health check backend..."
    sleep 5  # Дать время на запуск
    backend_health=$(curl -s http://localhost:8000/health || echo "")
    if echo "$backend_health" | grep -q "healthy\|ok\|status"; then
        log_info "✓ Backend health check пройден: $backend_health"
    else
        log_warn "Backend health check не прошёл. Ответ: $backend_health"
    fi

    log_info "8.2 Проверка frontend..."
    frontend_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ || echo "000")
    if [ "$frontend_response" = "200" ] || [ "$frontend_response" = "302" ]; then
        log_info "✓ Frontend доступен (HTTP $frontend_response)"
    else
        log_warn "Frontend недоступен (HTTP $frontend_response)"
    fi

    log_info "8.3 Проверка API через Nginx..."
    api_health=$(curl -s http://localhost/api/health || echo "")
    if echo "$api_health" | grep -q "healthy\|ok\|status"; then
        log_info "✓ API через Nginx работает: $api_health"
    else
        log_warn "API через Nginx не отвечает. Ответ: $api_health"
    fi

    log_info "8.4 Проверка статуса всех контейнеров..."
    docker compose -f "$COMPOSE_FILE" ps

    log_info "✓ Этап 8 завершён"
}

# Этап 9: Настройка автозапуска и мониторинга
stage9_setup_autostart() {
    log_step "Этап 9: Настройка автозапуска и мониторинга"

    log_info "9.1 Проверка настроек автозапуска в docker-compose..."
    restart_policy=$(docker compose -f "$COMPOSE_FILE" config | grep -c "restart:" || echo "0")
    if [ "$restart_policy" -gt 0 ]; then
        log_info "✓ Политика перезапуска настроена в docker-compose.prod.yml"
    else
        log_warn "Политика перезапуска не найдена в docker-compose.prod.yml"
    fi

    log_info "9.2 Создание systemd service (опционально)..."
    if [ ! -f /etc/systemd/system/freemarket.service ]; then
        log_info "Создаю systemd service..."
        sudo tee /etc/systemd/system/freemarket.service > /dev/null << EOF
[Unit]
Description=FreeMarket Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/docker compose -f $COMPOSE_FILE up -d
ExecStop=/usr/bin/docker compose -f $COMPOSE_FILE down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
        sudo systemctl daemon-reload
        sudo systemctl enable freemarket.service
        log_info "✓ Systemd service создан и включён"
    else
        log_info "Systemd service уже существует"
    fi

    log_info "✓ Этап 9 завершён"
}

# Этап 10: Резервное копирование и обслуживание
stage10_setup_backup() {
    log_step "Этап 10: Резервное копирование и обслуживание"

    cd "$PROJECT_DIR" || exit 1

    log_info "10.1 Создание директории для бэкапов..."
    sudo mkdir -p "$BACKUP_DIR"
    sudo chown $USER:$USER "$BACKUP_DIR"

    log_info "10.2 Создание скрипта резервного копирования..."
    cat > scripts/backup_db.sh << 'BACKUP_SCRIPT'
#!/bin/bash
# Скрипт резервного копирования базы данных FreeMarket

set -e

PROJECT_DIR="/opt/freemarket"
BACKUP_DIR="/backup/freemarket"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
COMPOSE_FILE="docker-compose.prod.yml"

cd "$PROJECT_DIR"

# Создание бэкапа PostgreSQL
echo "Создание бэкапа базы данных..."
docker compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U assistadmin_pg assistance_kz > "$BACKUP_DIR/backup_${TIMESTAMP}.sql"

# Сжатие бэкапа
gzip "$BACKUP_DIR/backup_${TIMESTAMP}.sql"

# Удаление старых бэкапов (старше 7 дней)
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete

echo "✓ Бэкап создан: $BACKUP_DIR/backup_${TIMESTAMP}.sql.gz"
BACKUP_SCRIPT

    chmod +x scripts/backup_db.sh
    log_info "✓ Скрипт резервного копирования создан: scripts/backup_db.sh"

    log_info "10.3 Просмотр использования ресурсов..."
    log_info "Используйте 'docker stats' для мониторинга в реальном времени"

    log_info "✓ Этап 10 завершён"
}

# Главная функция
main() {
    echo ""
    echo "=========================================="
    echo "  FreeMarket - Полное развёртывание"
    echo "=========================================="
    echo ""

    check_permissions

    # Выполнение всех этапов
    stage1_prepare_server
    stage2_clone_project
    stage3_setup_environment
    stage4_verify_docker_config
    stage5_build_images
    stage6_start_services
    stage7_apply_migrations
    stage8_verify_health
    stage9_setup_autostart
    stage10_setup_backup

    # Финальная проверка
    log_step "Финальная проверка"

    log_info "Проверка статуса всех контейнеров..."
    docker compose -f "$COMPOSE_FILE" ps

    log_info "Проверка health endpoints..."
    curl -s http://localhost/api/health || log_warn "API health check не прошёл"
    curl -s http://localhost/health || log_warn "Health check не прошёл"

    log_info "Проверка доступности frontend..."
    curl -I http://localhost 2>&1 | head -1 || log_warn "Frontend недоступен"

    log_info "Проверка логов на ошибки..."
    docker compose -f "$COMPOSE_FILE" logs --tail=50 | grep -i error || log_info "Критических ошибок не найдено"

    echo ""
    echo "=========================================="
    log_info "✓ Развёртывание завершено успешно!"
    echo "=========================================="
    echo ""
    echo "Быстрые команды:"
    echo "  Просмотр логов:    docker compose -f $COMPOSE_FILE logs -f"
    echo "  Перезапуск:        docker compose -f $COMPOSE_FILE restart"
    echo "  Остановка:         docker compose -f $COMPOSE_FILE down"
    echo "  Бэкап БД:          bash scripts/backup_db.sh"
    echo "  Статус:            docker compose -f $COMPOSE_FILE ps"
    echo ""
}

# Запуск главной функции
main

