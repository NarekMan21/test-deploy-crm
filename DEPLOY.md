# Инструкция по деплою

## Быстрый старт

### Локальный запуск с Docker Compose

1. **Клонируйте репозиторий и перейдите в директорию проекта**

2. **Создайте файлы окружения** (опционально, можно использовать значения по умолчанию):
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

3. **Настройте переменные окружения** в `backend/.env`:
```env
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=sqlite+aiosqlite:///./data/furniture_crm.db
PORT=8000
CORS_ORIGINS=http://localhost:3000,http://frontend:3000
```

4. **Запустите приложение**:
```bash
docker-compose up -d
```

5. **Приложение будет доступно:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Остановка приложения
```bash
docker-compose down
```

### Просмотр логов
```bash
# Все логи
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Production деплой

### Подготовка к production

1. **Установите переменные окружения для production:**

Создайте файл `.env` в корне проекта:
```env
# Backend
SECRET_KEY=<strong-random-secret-key>
DATABASE_URL=sqlite+aiosqlite:///./data/furniture_crm.db
BACKEND_PORT=8000
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Frontend
FRONTEND_PORT=3000
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api
NEXT_PUBLIC_API_SERVER_URL=https://api.yourdomain.com
```

**ВАЖНО:** Используйте сильный секретный ключ для `SECRET_KEY`. Можно сгенерировать:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. **Запустите production сборку:**
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

3. **Проверьте статус сервисов:**
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Обновление приложения

1. **Получите последние изменения:**
```bash
git pull
```

2. **Пересоберите и перезапустите:**
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Резервное копирование базы данных

```bash
# Создать бэкап
docker-compose -f docker-compose.prod.yml exec backend cp /app/data/furniture_crm.db /app/uploads/backup_$(date +%Y%m%d_%H%M%S).db

# Восстановить из бэкапа
docker-compose -f docker-compose.prod.yml exec backend cp /app/uploads/backup_YYYYMMDD_HHMMSS.db /app/data/furniture_crm.db
```

## Деплой на виртуальный сервер

### Подготовка сервера

1. **Установите Docker и Docker Compose:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **Склонируйте проект на сервер:**
```bash
git clone <your-repo-url> /opt/crmpy
cd /opt/crmpy
```

3. **Настройте переменные окружения:**
```bash
cp backend/.env.example backend/.env
nano backend/.env  # Отредактируйте файл
```

4. **Запустите приложение:**
```bash
docker-compose up -d --build
```

### Настройка Nginx (рекомендуется)

Пример конфигурации Nginx для проксирования:

```nginx
# /etc/nginx/sites-available/crmpy
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Uploads
    location /uploads {
        proxy_pass http://localhost:8000;
    }
}
```

Активируйте конфигурацию:
```bash
sudo ln -s /etc/nginx/sites-available/crmpy /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Настройка SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

## Деплой в облако

### Yandex Cloud / Kubernetes

Проект включает файлы для деплоя в Kubernetes:
- `k8s-deployment.yaml` - основные deployment'ы
- `k8s-secret.yaml` - пример секретов
- `k8s-pvc.yaml` - persistent volume claims

Подробные инструкции смотрите в `DEPLOYMENT_YANDEX_CLOUD.md`

### Другие облачные провайдеры

Проект можно развернуть на:
- **DigitalOcean App Platform**
- **Heroku** (с минимальными изменениями)
- **Railway**
- **Render**
- **Fly.io**

## Мониторинг и логи

### Просмотр логов

```bash
# Docker Compose
docker-compose logs -f

# Kubernetes
kubectl logs -f deployment/backend
kubectl logs -f deployment/frontend
```

### Health checks

Backend автоматически проверяет здоровье через `/health` endpoint:
```bash
curl http://localhost:8000/health
```

### Мониторинг ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Kubernetes
kubectl top pods
```

## Устранение проблем

### Проблема: Контейнеры не запускаются

1. Проверьте логи:
```bash
docker-compose logs
```

2. Проверьте порты:
```bash
netstat -tulpn | grep :8000
netstat -tulpn | grep :3000
```

3. Проверьте конфигурацию:
```bash
docker-compose config
```

### Проблема: База данных не создается

1. Проверьте права доступа:
```bash
docker-compose exec backend ls -la /app/data
```

2. Запустите инициализацию вручную:
```bash
docker-compose exec backend python init_db.py
```

### Проблема: Фронтенд не может подключиться к бэкенду

1. Проверьте переменную окружения `NEXT_PUBLIC_API_URL`
2. Убедитесь, что CORS настроен правильно в backend
3. Проверьте, что оба контейнера в одной сети

### Проблема: Загрузка файлов не работает

1. Проверьте права на директорию uploads:
```bash
docker-compose exec backend ls -la /app/uploads
```

2. Проверьте, что volume правильно подключен в docker-compose.yml

## Безопасность в production

1. **Измените SECRET_KEY** - используйте сильный случайный ключ
2. **Настройте CORS** - разрешите только нужные домены
3. **Используйте HTTPS** - настройте SSL/TLS сертификаты
4. **Ограничьте доступ** - используйте firewall для закрытия ненужных портов
5. **Регулярные обновления** - обновляйте зависимости и Docker образы
6. **Резервное копирование** - настройте автоматическое резервное копирование БД
7. **Мониторинг** - настройте мониторинг ошибок и производительности

## Дополнительные ресурсы

- [Docker документация](https://docs.docker.com/)
- [Docker Compose документация](https://docs.docker.com/compose/)
- [FastAPI документация](https://fastapi.tiangolo.com/)
- [Next.js документация](https://nextjs.org/docs)

