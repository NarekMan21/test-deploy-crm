from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import create_tables
from routers import auth, orders
import uvicorn
import os
import urllib.parse
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class CustomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        # Декодируем URL-кодированные пути
        decoded_path = urllib.parse.unquote(path)
        return await super().get_response(decoded_path, scope)

from contextlib import asynccontextmanager
from init_db import init_users

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("[main] Application startup...")
    try:
        await create_tables()
        print("[main] Tables created/verified")
        # Initialize database with default users
        await init_users()
        print("[main] Database initialization completed")
    except Exception as e:
        print(f"[main] ERROR during startup: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        # Не падаем, чтобы приложение могло запуститься даже если БД не готова
    yield
    # Shutdown (if needed)
    print("[main] Application shutdown")

app = FastAPI(title="CRM Furniture", version="1.0.0", lifespan=lifespan)

# CORS middleware для фронтенда
# Получаем разрешенные origins из переменной окружения или используем значения по умолчанию
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://frontend:3000,https://crmpy-frontend.onrender.com"
).split(",")

# Добавляем все возможные origins для Render
cors_origins.extend([
    "https://crmpy-frontend.onrender.com",
    "http://localhost:3000",
    "http://frontend:3000"
])

# Удаляем дубликаты
cors_origins = list(set([origin.strip() for origin in cors_origins if origin.strip()]))

print(f"[main] CORS origins configured: {cors_origins}")

# Добавляем логирование всех запросов для отладки
@app.middleware("http")
async def log_requests(request, call_next):
    import time
    start_time = time.time()
    print(f"[main] Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"[main] Request processed: {request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files with custom handler for URL decoding
# Используем persistent disk для uploads, если он доступен
upload_dir = os.getenv("UPLOAD_DIR", "uploads")
if os.path.exists("/app/data"):
    upload_dir = "/app/data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", CustomStaticFiles(directory=upload_dir), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])

@app.get("/")
async def root():
    return {"message": "CRM Furniture API", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)