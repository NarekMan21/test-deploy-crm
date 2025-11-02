# Быстрый старт

## Локальный запуск

### Вариант 1: С Docker (рекомендуется)

```bash
# 1. Запустить приложение
docker-compose up -d --build

# 2. Проверить статус
docker-compose ps

# 3. Просмотр логов
docker-compose logs -f

# Приложение будет доступно:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Вариант 2: Без Docker

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
python main.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Использование Makefile

Если у вас установлен `make`:

```bash
make build      # Собрать образы
make up         # Запустить приложение
make logs       # Показать логи
make down       # Остановить приложение
make test       # Запустить тесты
make clean      # Очистить все
```

## Тестовые аккаунты

После инициализации БД доступны:
- **Админ**: `admin1` / `nimda`
- **Логистика**: `logist` / `logist`
- **Мастерская**: `work` / `work`

## Подробная документация

- `README.md` - Полная документация проекта
- `DEPLOY.md` - Инструкции по деплою
- `AUDIT_REPORT.md` - Отчет об аудите и исправлениях

