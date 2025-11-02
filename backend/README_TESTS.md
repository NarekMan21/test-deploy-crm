# Инструкция по запуску тестов

## Предварительные требования

1. Убедитесь, что Python 3.10+ установлен
2. Активируйте виртуальное окружение (если используете)

## Установка зависимостей

```powershell
# В директории backend
cd backend

# Установите зависимости
pip install -r requirements.txt
```

Или если вы в корневой директории проекта:
```powershell
pip install -r backend\requirements.txt
```

## Запуск тестов

### Все тесты:
```powershell
# Из директории backend
python -m pytest

# Или из корневой директории
python -m pytest backend/
```

### Конкретный файл с тестами:
```powershell
# Тесты аутентификации
python -m pytest test_auth.py -v

# Тесты заказов
python -m pytest test_orders.py -v
```

### Конкретный тест:
```powershell
python -m pytest test_auth.py::test_login_success -v
```

### С подробным выводом:
```powershell
python -m pytest -v
```

### С покрытием кода (если установлен pytest-cov):
```powershell
python -m pytest --cov=. --cov-report=html
```

## Важно!

**НЕ запускайте тестовые файлы напрямую!**

❌ **Неправильно:**
```powershell
.\test_auth.py
python test_auth.py
```

✅ **Правильно:**
```powershell
python -m pytest test_auth.py
```

## Устранение проблем

### Ошибка: ModuleNotFoundError

Если видите ошибку типа `ModuleNotFoundError: No module named 'sqlalchemy'`, убедитесь что:
1. Зависимости установлены: `pip install -r requirements.txt`
2. Используется правильное виртуальное окружение (если используется)

### Ошибка: ImportError при импорте main

Убедитесь, что вы запускаете тесты из директории `backend`, или используйте полный путь:
```powershell
python -m pytest backend/test_auth.py -v
```

## Структура тестов

- `test_auth.py` - тесты аутентификации (6 тестов)
  - Проверка здоровья API
  - Успешный вход
  - Неуспешный вход
  - Валидация входных данных
  - Проверка токенов
  
- `test_orders.py` - тесты управления заказами (6 тестов)
  - Создание заказа
  - Получение списка заказов
  - Валидация данных
  - Проверка прав доступа

