#!/bin/bash

echo "🔥 Полная пересборка FreeMarket..."

# Остановить и удалить всё
echo "🛑 Останавливаем сервисы..."
docker compose down -v --remove-orphans

# Очистить систему
echo "🧹 Очищаем Docker..."
docker system prune -af --volumes
docker builder prune -af

# Пересобрать без кэша
echo "🔨 Пересобираем образы..."
docker compose build --no-cache

# Запустить
echo "🚀 Запускаем сервисы..."
docker compose up -d

# Проверить статус
echo "📊 Статус сервисов:"
docker compose ps

echo "✅ Пересборка завершена!"
echo "🌐 Проверьте http://localhost"
