"""
Router: /dashboard
  GET /dashboard  – Tổng quan tài chính: số dư, thu/chi tháng này, ds hũ, giao dịch gần đây
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Jar, JarMember, Transaction, User
from app.schemas import DashboardResponse, JarResponse, TransactionResponse
from app.security import get_current_user
from app.routers.jars import _map_jar
from app.routers.transactions import _map

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    month, year = now.month, now.year

    # Jar IDs mà user là thành viên
    jar_ids = [m.JarId for m in db.query(JarMember).filter(JarMember.UserId == current_user.UserId).all()]

    # Thu nhập tháng này
    income = db.query(func.sum(Transaction.Amount)).filter(
        Transaction.JarId.in_(jar_ids),
        Transaction.TransactionType == True,                   # noqa: E712
        extract("month", Transaction.TransactionDate) == month,
        extract("year",  Transaction.TransactionDate) == year,
    ).scalar() or 0.0

    # Chi tiêu tháng này
    expense = db.query(func.sum(Transaction.Amount)).filter(
        Transaction.JarId.in_(jar_ids),
        Transaction.TransactionType == False,                  # noqa: E712
        extract("month", Transaction.TransactionDate) == month,
        extract("year",  Transaction.TransactionDate) == year,
    ).scalar() or 0.0

    income  = float(income)
    expense = float(expense)
    balance = income - expense
    saving_rate = round((balance / income * 100), 2) if income > 0 else 0.0

    # DS hũ
    jars = [_map_jar(j, db) for j in db.query(Jar).filter(Jar.JarId.in_(jar_ids)).all()]

    # 10 giao dịch gần nhất
    recent_txs = db.query(Transaction).filter(
        Transaction.JarId.in_(jar_ids)
    ).order_by(Transaction.TransactionDate.desc()).limit(10).all()

    return DashboardResponse(
        total_balance        = balance,
        total_income         = income,
        total_expense        = expense,
        saving_rate          = saving_rate,
        jars                 = jars,
        recent_transactions  = [_map(t) for t in recent_txs],
    )
