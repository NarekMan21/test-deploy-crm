from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import create_tables
from routers import auth, orders
import uvicorn
import os
import urllib.parse

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
    await create_tables()
    # Initialize database with default users
    await init_users()
    yield
    # Shutdown (if needed)

app = FastAPI(title="CRM Furniture", version="1.0.0", lifespan=lifespan)

# CORS middleware для фронтенда
# Получаем разрешенные origins из переменной окружения или используем значения по умолчанию
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://frontend:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files with custom handler for URL decoding
app.mount("/uploads", CustomStaticFiles(directory="uploads"), name="uploads")

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