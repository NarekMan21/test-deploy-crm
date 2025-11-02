#!/bin/bash

# Скрипт развертывания CRMpy на облачной VM
echo "🚀 Начинаем развертывание CRMpy на облачной VM..."

# Установка Docker если не установлен
if ! command -v docker &> /dev/null; then
    echo "📦 Устанавливаем Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker $USER
fi

# Установка Docker Compose если не установлен
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Устанавливаем Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Загрузка Docker образов
echo "📦 Загружаем Docker образы..."
docker load < crm-backend.tar
docker load < crm-frontend.tar

# Создание директорий
echo "📁 Создаем необходимые директории..."
mkdir -p backend/uploads

# Запуск приложения
echo "🚀 Запускаем приложение..."
docker-compose -f docker-compose-vm.yml up -d

# Ожидание запуска
echo "⏳ Ждем запуска приложения..."
sleep 30

# Проверка статуса
echo "📊 Проверяем статус..."
docker-compose -f docker-compose-vm.yml ps

echo "✅ Развертывание завершено!"
echo ""
echo "🌐 Приложение доступно по адресу:"
echo "   Frontend: http://176.108.253.113:3000"
echo "   API: http://176.108.253.113:8080"
echo ""
echo "🔑 Тестовые аккаунты:"
echo "   Admin: admin1 / nimda"
echo "   Логистика: logist / logist"
echo "   Рабочий: work / work"