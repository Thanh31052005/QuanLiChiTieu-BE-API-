"""
Entry point – FastAPI application
Quản Lý Chi Tiêu API v1.0
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database import get_db, engine
from app.routers import auth, categories, jars, transactions, dashboard

# ── Tạo thư mục upload nếu chưa có ──────────────────────────────────────────
os.makedirs("static/uploads/receipts", exist_ok=True)

# ── Khởi tạo app ─────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "Quản Lý Chi Tiêu API",
    description = "Backend REST API cho ứng dụng Quản Lý Chi Tiêu (Flutter)",
    version     = "1.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

# ── CORS – cho phép Flutter gọi API ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],   # Thay bằng domain cụ thể khi deploy production
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Static files (ảnh hóa đơn) ───────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(jars.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)

# ── Kiểm tra DB khi startup ───────────────────────────────────────────────────
@app.on_event("startup")
def check_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[DB OK] Connected to ManageMoneyDB successfully!")
    except Exception as e:
        print(f"[DB ERROR] Connection failed: {e}")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "online", "app": "Quản Lý Chi Tiêu API", "version": "1.0.0"}