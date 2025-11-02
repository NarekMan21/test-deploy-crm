# Документация по развертыванию CRMpy в Яндекс.Облаке

## Обзор проекта

CRMpy - это веб-приложение для управления заказами мебельной компании, реализованное с использованием следующих технологий:
- Бэкенд: FastAPI на Python с SQLAlchemy для работы с базой данных
- Фронтенд: Next.js на React
- База данных: SQLite
- Контейнеризация: Docker и Docker Compose

## Архитектура развертывания

Проект использует многоконтейнерную архитектуру с тремя основными сервисами:

1. **Backend Service** (FastAPI):
   - Бэкенд приложение на Python
   - Обрабатывает API запросы
   - Работает с SQLite базой данных
   - Порт: 8080

2. **Frontend Service** (Next.js):
   - Фронтенд приложение на React
   - Серверная обработка и рендеринг
   - Порт: 3000
   - Связывается с бэкендом через http://backend:8080

3. **Database Service** (SQLite):
   - Контейнер для хранения данных SQLite
   - Использует volume для персистентности
   - Предоставляет данные для бэкенда

### Диаграмма архитектуры

```mermaid
graph TD
    A[Frontend (Next.js)] -->|HTTP/3000| B(Backend (FastAPI))
    B -->|SQLite| C(Database Container)
    A -->|API Calls| B
    B -->|File Uploads| D[Uploads Volume]
    C -->|Data Access| B
    D -->|Persistent Storage| C
```

## Инструкции по сборке образов

### Сборка бэкенда
```bash
# Перейти в директорию бэкенда
cd backend

# Собрать Docker образ
docker build -t crmpy-backend .
```

### Сборка фронтенда
```bash
# Перейти в директорию фронтенда
cd frontend

# Собрать Docker образ
docker build -t crmpy-frontend .
```

### Сборка всех образов через Docker Compose
```bash
# Из корневой директории проекта
docker-compose build
```

## Инструкции по загрузке в реестр Яндекс.Облака

### 1. Регистрация в реестре
```bash
# Авторизация в Yandex Container Registry
yc container registry login

# Или через Docker
docker login cr.yandex
```

### 2. Тегирование образов
```bash
# Тегирование бэкенда
docker tag crmpy-backend cr.yandex/crpid123456789/backend:latest

# Тегирование фронтенда  
docker tag crmpy-frontend cr.yandex/crpid123456789/frontend:latest
```

### 3. Загрузка образов в реестр
```bash
# Загрузка бэкенда
docker push cr.yandex/crpid123456789/backend:latest

# Загрузка фронтенда
docker push cr.yandex/crpid123456789/frontend:latest
```

## Настройка кластера Kubernetes

### 1. Создание кластера
```bash
# Создание managed Kubernetes кластера
yc managed-kubernetes cluster create \
  --name crmpy-cluster \
  --network-id <network-id> \
  --service-account-id <service-account-id> \
  --node-service-account-id <node-service-account-id> \
  --zone ru-central1-a \
  --public-ip
```

### 2. Настройка доступа к кластеру
```bash
# Получение конфигурации kubectl
yc managed-kubernetes cluster get-credentials --name crmpy-cluster

# Проверка подключения
kubectl get nodes
```

### 3. Создание namespace
```bash
kubectl create namespace crmpy
```

## Переменные окружения

### Бэкенд переменные:
```env
DATABASE_URL=sqlite+aiosqlite:///./furniture_crm.db
SECRET_KEY=your-secret-key-here
```

### Фронтенд переменные:
```env
NEXT_PUBLIC_API_URL=http://backend:8080
```

## Volumes для персистентности

### Database Volume
- Имя: `db_data`
- Назначение: Хранение базы данных SQLite
- Тип: Local volume
- Путь внутри контейнера: `/app/furniture_crm.db`

### Uploads Volume
- Имя: `uploads`
- Назначение: Хранение загруженных файлов
- Тип: Bind mount или PersistentVolume
- Путь внутри контейнера: `/app/uploads`

## Конфигурационные файлы Kubernetes

### Deployment для бэкенда
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deployment
  namespace: crmpy
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: cr.yandex/crpid123456789/backend:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          value: sqlite+aiosqlite:///./furniture_crm.db
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: crmpy-secrets
              key: secret-key
        volumeMounts:
        - name: db-data
          mountPath: /app/furniture_crm.db
        - name: uploads
          mountPath: /app/uploads
      volumes:
      - name: db-data
        persistentVolumeClaim:
          claimName: db-pvc
      - name: uploads
        persistentVolumeClaim:
          claimName: uploads-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: crmpy
spec:
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

### Deployment для фронтенда
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-deployment
  namespace: crmpy
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: cr.yandex/crpid123456789/frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: NEXT_PUBLIC_API_URL
          value: http://backend-service:8080
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: crmpy
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 3000
  type: LoadBalancer
```

### Persistent Volume Claims
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: db-pvc
  namespace: crmpy
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: uploads-pvc
  namespace: crmpy
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
```

## Развертывание приложения

### 1. Создание секретов
```bash
kubectl create secret generic crmpy-secrets \
  --namespace crmpy \
  --from-literal=secret-key=your-super-secret-key-here
```

### 2. Применение конфигураций
```bash
# Создание PVC
kubectl apply -f pvc.yaml

# Создание сервисов
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml

# Проверка состояния
kubectl get pods -n crmpy
kubectl get svc -n crmpy
```

## Проверка работоспособности

### 1. Проверка состояния подов
```bash
kubectl get pods -n crmpy
```

### 2. Проверка логов
```bash
kubectl logs -l app=backend -n crmpy
kubectl logs -l app=frontend -n crmpy
```

### 3. Проверка API
```bash
# Проверка доступности API
curl http://<frontend-service-ip>:80/health
```

## Мониторинг и логирование

### Настройка метрик
```bash
# Установка Prometheus
kubectl apply -f prometheus.yaml

# Установка Grafana
kubectl apply -f grafana.yaml
```

### Логирование
```bash
# Настройка Fluentd для сбора логов
kubectl apply -f fluentd.yaml
```

## Резервное копирование

### Бэкап базы данных
```bash
# Создание резервной копии базы данных
kubectl exec -it <backend-pod> -- cp /app/furniture_crm.db /backup/furniture_crm_$(date +%Y%m%d_%H%M%S).db
```

### Автоматизация бэкапов
```bash
# CronJob для автоматического бэкапа
kubectl apply -f backup-cronjob.yaml
```

## Масштабирование

### Горизонтальное масштабирование
```bash
# Масштабирование бэкенда
kubectl scale deployment backend-deployment --replicas=3 -n crmpy

# Масштабирование фронтенда
kubectl scale deployment frontend-deployment --replicas=3 -n crmpy
```

## Безопасность

### RBAC настройки
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: crmpy
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: crmpy
subjects:
- kind: User
  name: crmpy-admin
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: read-pods
  apiGroup: rbac.authorization.k8s.io
```

## Рекомендации по эксплуатации

1. **Регулярное резервное копирование** базы данных и загруженных файлов
2. **Мониторинг производительности** через Prometheus и Grafana
3. **Контроль использования ресурсов** через Kubernetes Resource Quotas
4. **Обновление образов** через CI/CD pipeline
5. **Логирование и аудит** действий пользователей