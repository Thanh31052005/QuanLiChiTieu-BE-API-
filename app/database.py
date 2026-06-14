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

# Sửa lỗi lưu tiếng Việt bị biến thành dấu chấm hỏi (Unicode) cho pyodbc
from sqlalchemy import event
@event.listens_for(engine, "connect")
def _set_unicode(dbapi_connection, connection_record):
    import pyodbc
    if isinstance(dbapi_connection, pyodbc.Connection):
        dbapi_connection.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
        dbapi_connection.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
        dbapi_connection.setencoding(encoding='utf-8')

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency: tạo và đóng session theo từng request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
