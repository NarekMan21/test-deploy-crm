#!/bin/bash

# Ручная установка CRMpy на VM Cloud.ru
# Выполните эти команды по порядку в консоли VM

echo "=== РУЧНАЯ УСТАНОВКА CRMPY НА VM ==="
echo ""

echo "1. Установка Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

echo "2. Установка Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo "3. Создание docker-compose-vm.yml..."
cat > docker-compose-vm.yml << 'EOF'
version: '3.8'

services:
  backend:
    image: crmpy1-backend:latest
    ports:
      - "8080:8080"
    environment:
      - SECRET_KEY=your-super-secret-key-change-this-in-production
      - DATABASE_URL=sqlite:///./furniture_crm.db
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/furniture_crm.db:/app/furniture_crm.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: crmpy1-frontend:latest
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8080
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
EOF

echo "4. Создание deploy-vm.sh..."
cat > deploy-vm.sh << 'EOF'
#!/bin/bash
echo "📦 Загружаем Docker образы..."
docker load < crm-backend.tar
docker load < crm-frontend.tar

echo "📁 Создаем директории..."
mkdir -p backend/uploads

echo "🚀 Запускаем приложение..."
docker-compose -f docker-compose-vm.yml up -d

echo "⏳ Ждем запуска..."
sleep 30

echo "📊 Статус:"
docker-compose -f docker-compose-vm.yml ps

echo "✅ Готово!"
echo "🌐 Frontend: http://176.108.253.113:3000"
echo "🔑 Admin: admin1/nimda"
EOF

echo "5. Сделайте скрипт исполняемым..."
chmod +x deploy-vm.sh

echo ""
echo "=== ДАЛЕЕ ЗАГРУЗИТЕ ФАЙЛЫ ==="
echo "Теперь загрузите на VM файлы:"
echo "- crm-backend.tar"
echo "- crm-frontend.tar"
echo ""
echo "Затем выполните: ./deploy-vm.sh"