from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DB_SERVER, DB_NAME, DB_DRIVER, DB_USER, DB_PASSWORD

# ── Tạo connection string theo cấu hình ─────────────────────────────────────
if DB_USER and DB_PASSWORD:
    # SQL Server Authentication
    conn_str = (
        f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}"
        f"?driver={DB_DRIVER.replace(' ', '+')}"
        f"&TrustServerCertificate=yes" # <-- THÊM DÒNG NÀY VÀO ĐÂY
    )
else:
    # Windows Authentication (Trusted Connection)
    conn_str = (
        f"mssql+pyodbc://{DB_SERVER}/{DB_NAME}"
        f"?driver={DB_DRIVER.replace(' ', '+')}"
        f"&Trusted_Connection=yes"
        f"&TrustServerCertificate=yes" # <-- VÀ THÊM VÀO ĐÂY NỮA
    )

engine = create_engine(conn_str, fast_executemany=True, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency: tạo và đóng session theo từng request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
