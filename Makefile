.PHONY: help build up down logs restart clean test

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Собрать Docker образы
	docker-compose build

up: ## Запустить приложение
	docker-compose up -d

down: ## Остановить приложение
	docker-compose down

logs: ## Показать логи
	docker-compose logs -f

restart: ## Перезапустить приложение
	docker-compose restart

clean: ## Очистить контейнеры, образы и volumes
	docker-compose down -v
	docker system prune -f

test: ## Запустить тесты
	cd backend && python -m pytest -v

init-db: ## Инициализировать базу данных
	docker-compose exec backend python init_db.py

backup-db: ## Создать резервную копию БД
	docker-compose exec backend cp /app/data/furniture_crm.db /app/uploads/backup_$$(date +%Y%m%d_%H%M%S).db

prod-build: ## Собрать production образы
	docker-compose -f docker-compose.prod.yml build

prod-up: ## Запустить production
	docker-compose -f docker-compose.prod.yml up -d

prod-down: ## Остановить production
	docker-compose -f docker-compose.prod.yml down

prod-logs: ## Показать production логи
	docker-compose -f docker-compose.prod.yml logs -f

