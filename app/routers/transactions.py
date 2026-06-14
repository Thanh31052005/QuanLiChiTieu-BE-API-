"""
Router: /transactions
  GET    /transactions                  – DS giao dịch của user (lọc jar/tháng/loại)
  GET    /transactions/{id}             – Chi tiết
  POST   /transactions                  – Tạo giao dịch mới
  PUT    /transactions/{id}             – Cập nhật
  DELETE /transactions/{id}             – Xoá
  POST   /transactions/{id}/upload      – Upload ảnh hóa đơn (receipt)
  GET    /transactions/summary/monthly  – Thống kê theo tháng
"""
import os
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.database import get_db
from app.models import Transaction, Jar, JarMember, Category, User
from app.schemas import (
    TransactionResponse, CreateTransactionRequest,
    UpdateTransactionRequest, MonthlySummary,
)
from app.security import get_current_user
from app.config import UPLOAD_DIR, BASE_URL

router = APIRouter(prefix="/transactions", tags=["Transactions"])


# ── Helpers ───────────────────────────────────────────────────────────────────
def _map(t: Transaction) -> TransactionResponse:
    return TransactionResponse(
        transaction_id    = t.TransactionId,
        jar_id            = t.JarId,
        user_id           = t.UserId,
        category_id       = t.CategoryId,
        amount            = float(t.Amount),
        description       = t.Description,
        receipt_image_url = t.ReceiptImageUrl,
        transaction_type  = bool(t.TransactionType),
        transaction_date  = t.TransactionDate,
        category_name     = t.category.CategoryName if t.category else None,
        jar_name          = t.jar.JarName          if t.jar      else None,
        full_name         = t.user.FullName        if t.user     else None,
    )


def _assert_jar_access(jar_id: str, user_id: str, db: Session):
    if not db.query(JarMember).filter(
        JarMember.JarId == jar_id, JarMember.UserId == user_id
    ).first():
        raise HTTPException(403, "Bạn không có quyền truy cập hũ này")


# ── Danh sách giao dịch ───────────────────────────────────────────────────────
@router.get("", response_model=List[TransactionResponse])
def list_transactions(
    jar_id:           Optional[str]  = None,
    transaction_type: Optional[bool] = None,   # True=Thu, False=Chi
    month:            Optional[int]  = Query(None, ge=1, le=12),
    year:             Optional[int]  = Query(None, ge=2000),
    limit:            int            = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Lấy danh sách jar_id mà user là thành viên
    accessible_jar_ids = [
        m.JarId for m in db.query(JarMember).filter(JarMember.UserId == current_user.UserId).all()
    ]

    q = db.query(Transaction).filter(Transaction.JarId.in_(accessible_jar_ids))

    if jar_id:
        _assert_jar_access(jar_id, current_user.UserId, db)
        q = q.filter(Transaction.JarId == jar_id)
    if transaction_type is not None:
        q = q.filter(Transaction.TransactionType == transaction_type)
    if month:
        q = q.filter(extract("month", Transaction.TransactionDate) == month)
    if year:
        q = q.filter(extract("year",  Transaction.TransactionDate) == year)

    txs = q.order_by(Transaction.TransactionDate.desc()).limit(limit).all()
    return [_map(t) for t in txs]


# ── Chi tiết ──────────────────────────────────────────────────────────────────
@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    t = db.query(Transaction).filter(Transaction.TransactionId == transaction_id).first()
    if not t:
        raise HTTPException(404, "Giao dịch không tồn tại")
    _assert_jar_access(t.JarId, current_user.UserId, db)
    return _map(t)


# ── Tạo mới ───────────────────────────────────────────────────────────────────
@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(
    body: CreateTransactionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_jar_access(body.jar_id, current_user.UserId, db)
    if not db.query(Category).filter(Category.CategoryId == body.category_id).first():
        raise HTTPException(404, "Danh mục không tồn tại")

    t = Transaction(
        TransactionId   = str(uuid.uuid4()),
        JarId           = body.jar_id,
        UserId          = current_user.UserId,
        CategoryId      = body.category_id,
        Amount          = body.amount,
        Description     = body.description,
        TransactionType = body.transaction_type,
        TransactionDate = body.transaction_date or datetime.utcnow(),
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return _map(t)


# ── Cập nhật ─────────────────────────────────────────────────────────────────
@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: str,
    body: UpdateTransactionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    t = db.query(Transaction).filter(Transaction.TransactionId == transaction_id).first()
    if not t:
        raise HTTPException(404, "Giao dịch không tồn tại")
    if t.UserId != current_user.UserId:
        raise HTTPException(403, "Bạn không thể chỉnh sửa giao dịch của người khác")

    if body.category_id      is not None: t.CategoryId      = body.category_id
    if body.amount            is not None: t.Amount          = body.amount
    if body.description       is not None: t.Description     = body.description
    if body.transaction_type  is not None: t.TransactionType = body.transaction_type
    if body.transaction_date  is not None: t.TransactionDate = body.transaction_date

    db.commit()
    db.refresh(t)
    return _map(t)


# ── Xoá ──────────────────────────────────────────────────────────────────────
@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    t = db.query(Transaction).filter(Transaction.TransactionId == transaction_id).first()
    if not t:
        raise HTTPException(404, "Giao dịch không tồn tại")
    if t.UserId != current_user.UserId:
        raise HTTPException(403, "Bạn không thể xoá giao dịch của người khác")
    db.delete(t)
    db.commit()


# ── Upload ảnh hóa đơn ────────────────────────────────────────────────────────
@router.post("/{transaction_id}/upload", response_model=TransactionResponse)
async def upload_receipt(
    transaction_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    t = db.query(Transaction).filter(Transaction.TransactionId == transaction_id).first()
    if not t:
        raise HTTPException(404, "Giao dịch không tồn tại")
    if t.UserId != current_user.UserId:
        raise HTTPException(403, "Không có quyền upload ảnh cho giao dịch này")

    # Chỉ chấp nhận ảnh
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(400, "Chỉ chấp nhận file ảnh JPG/PNG/WebP")

    ext      = file.filename.split(".")[-1]
    filename = f"{transaction_id}.{ext}"
    path     = os.path.join(UPLOAD_DIR, filename)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    contents = await file.read()
    with open(path, "wb") as f:
        f.write(contents)

    t.ReceiptImageUrl = f"{BASE_URL}/static/uploads/receipts/{filename}"
    db.commit()
    db.refresh(t)
    return _map(t)


# ── Thống kê theo tháng ──────────────────────────────────────────────────────
@router.get("/summary/monthly", response_model=List[MonthlySummary])
def monthly_summary(
    year: int = Query(..., ge=2000),
    jar_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    accessible_jar_ids = [
        m.JarId for m in db.query(JarMember).filter(JarMember.UserId == current_user.UserId).all()
    ]
    q = db.query(
        extract("month", Transaction.TransactionDate).label("month"),
        Transaction.TransactionType,
        func.sum(Transaction.Amount).label("total"),
    ).filter(
        Transaction.JarId.in_(accessible_jar_ids),
        extract("year", Transaction.TransactionDate) == year,
    )
    if jar_id:
        q = q.filter(Transaction.JarId == jar_id)

    rows = q.group_by(
        extract("month", Transaction.TransactionDate),
        Transaction.TransactionType,
    ).all()

    data: dict[int, dict] = {}
    for row in rows:
        m = int(row.month)
        if m not in data:
            data[m] = {"income": 0.0, "expense": 0.0}
        if row.TransactionType:
            data[m]["income"] += float(row.total or 0)
        else:
            data[m]["expense"] += float(row.total or 0)

    result = []
    for m in range(1, 13):
        inc = data.get(m, {}).get("income", 0.0)
        exp = data.get(m, {}).get("expense", 0.0)
        result.append(MonthlySummary(month=m, year=year, total_income=inc, total_expense=exp, net=inc - exp))
    return result
