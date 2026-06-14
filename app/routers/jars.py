"""
Router: /jars
  GET    /jars               – Tất cả hũ của user hiện tại (kèm spent_amount)
  GET    /jars/{jar_id}      – Chi tiết hũ
  POST   /jars               – Tạo hũ mới
  PUT    /jars/{jar_id}      – Cập nhật hũ (chỉ Owner/Co-owner)
  DELETE /jars/{jar_id}      – Xoá hũ (chỉ Owner)

  GET    /jars/{jar_id}/members           – DS thành viên
  POST   /jars/{jar_id}/members           – Thêm thành viên
  PUT    /jars/{jar_id}/members/{user_id} – Đổi vai trò
  DELETE /jars/{jar_id}/members/{user_id} – Xoá thành viên
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Jar, JarMember, Transaction, User
from app.schemas import (
    JarResponse, CreateJarRequest, UpdateJarRequest,
    JarMemberResponse, AddMemberRequest, UpdateMemberRoleRequest, UserResponse,
)
from app.security import get_current_user


router = APIRouter(prefix="/jars", tags=["Jars"])


# ── Helpers ───────────────────────────────────────────────────────────────────
def _spent(jar_id: str, db: Session) -> float:
    """Tổng chi tiêu trong hũ (Expense)."""
    result = db.query(func.sum(Transaction.Amount)).filter(
        Transaction.JarId == jar_id,
        Transaction.TransactionType == False,  # noqa: E712 (Expense)
    ).scalar()
    return float(result or 0)


def _income(jar_id: str, db: Session) -> float:
    result = db.query(func.sum(Transaction.Amount)).filter(
        Transaction.JarId == jar_id,
        Transaction.TransactionType == True,
    ).scalar()
    return float(result or 0)


def _map_jar(jar: Jar, db: Session) -> JarResponse:
    spent   = _spent(jar.JarId, db)
    income  = _income(jar.JarId, db)
    balance = income - spent
    budget  = float(jar.Budget or 0)
    remaining = budget - spent
    pct     = (spent / budget) if budget > 0 else 0.0
    return JarResponse(
        jar_id             = jar.JarId,
        jar_name           = jar.JarName,
        description        = jar.Description,
        budget             = budget,
        jar_type           = jar.JarType,
        created_by_user_id = jar.CreatedByUserId,
        created_at         = jar.CreatedAt,
        spent_amount       = spent,
        income_amount      = income,
        balance            = balance,
        remaining          = remaining,
        usage_percent      = min(pct, 1.0),
    )


def _assert_member(jar_id: str, user_id: str, db: Session, roles=("Owner", "Co-owner", "Member")):
    m = db.query(JarMember).filter(
        JarMember.JarId == jar_id, JarMember.UserId == user_id
    ).first()
    if not m or m.Role not in roles:
        raise HTTPException(403, "Bạn không có quyền thực hiện thao tác này")
    return m


# ── Jar CRUD ──────────────────────────────────────────────────────────────────
@router.get("", response_model=List[JarResponse])
def list_jars(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Lấy tất cả hũ user là thành viên
    jar_ids = [m.JarId for m in db.query(JarMember).filter(JarMember.UserId == current_user.UserId).all()]
    jars = db.query(Jar).filter(Jar.JarId.in_(jar_ids)).all()
    return [_map_jar(j, db) for j in jars]


@router.get("/{jar_id}", response_model=JarResponse)
def get_jar(jar_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(jar_id, current_user.UserId, db)
    jar = db.query(Jar).filter(Jar.JarId == jar_id).first()
    if not jar:
        raise HTTPException(404, "Hũ không tồn tại")
    return _map_jar(jar, db)


@router.post("", response_model=JarResponse, status_code=201)
def create_jar(body: CreateJarRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    jar_id = str(uuid.uuid4())
    jar = Jar(
        JarId           = jar_id,
        JarName         = body.jar_name,
        Description     = body.description,
        Budget          = body.budget,
        JarType         = body.jar_type,
        CreatedByUserId = current_user.UserId,
    )
    db.add(jar)

    # Tự động thêm người tạo là Owner
    member = JarMember(JarId=jar_id, UserId=current_user.UserId, Role="Owner")
    db.add(member)

    db.commit()
    db.refresh(jar)
    return _map_jar(jar, db)


@router.put("/{jar_id}", response_model=JarResponse)
def update_jar(jar_id: str, body: UpdateJarRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(jar_id, current_user.UserId, db, roles=("Owner", "Co-owner"))
    jar = db.query(Jar).filter(Jar.JarId == jar_id).first()
    if not jar:
        raise HTTPException(404, "Hũ không tồn tại")
    if body.jar_name   is not None: jar.JarName     = body.jar_name
    if body.description is not None: jar.Description = body.description
    if body.budget     is not None: jar.Budget      = body.budget
    if body.jar_type   is not None: jar.JarType     = body.jar_type
    db.commit()
    db.refresh(jar)
    return _map_jar(jar, db)


@router.delete("/{jar_id}", status_code=204)
def delete_jar(jar_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(jar_id, current_user.UserId, db, roles=("Owner",))
    jar = db.query(Jar).filter(Jar.JarId == jar_id).first()
    if not jar:
        raise HTTPException(404, "Hũ không tồn tại")
    db.delete(jar)
    db.commit()


# ── Members ───────────────────────────────────────────────────────────────────
def _map_member(m: JarMember) -> JarMemberResponse:
    u = m.user
    return JarMemberResponse(
        jar_id    = m.JarId,
        user_id   = m.UserId,
        role      = m.Role,
        joined_at = m.JoinedAt,
        user      = UserResponse(user_id=u.UserId, full_name=u.FullName,
                                 email=u.Email, created_at=u.CreatedAt) if u else None,
    )


@router.get("/{jar_id}/members", response_model=List[JarMemberResponse])
def list_members(jar_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(jar_id, current_user.UserId, db)
    members = db.query(JarMember).filter(JarMember.JarId == jar_id).all()
    return [_map_member(m) for m in members]


@router.post("/{jar_id}/members", response_model=JarMemberResponse, status_code=201)
def add_member(jar_id: str, body: AddMemberRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(jar_id, current_user.UserId, db, roles=("Owner", "Co-owner"))
    if not db.query(User).filter(User.UserId == body.user_id).first():
        raise HTTPException(404, "Người dùng không tồn tại")
    existing = db.query(JarMember).filter(JarMember.JarId == jar_id, JarMember.UserId == body.user_id).first()
    if existing:
        raise HTTPException(400, "Người dùng đã là thành viên của hũ này")
    m = JarMember(JarId=jar_id, UserId=body.user_id, Role=body.role)
    db.add(m)
    db.commit()
    db.refresh(m)
    return _map_member(m)


@router.put("/{jar_id}/members/{user_id}", response_model=JarMemberResponse)
def update_member_role(jar_id: str, user_id: str, body: UpdateMemberRoleRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(jar_id, current_user.UserId, db, roles=("Owner",))
    m = db.query(JarMember).filter(JarMember.JarId == jar_id, JarMember.UserId == user_id).first()
    if not m:
        raise HTTPException(404, "Thành viên không tồn tại")
    m.Role = body.role
    db.commit()
    db.refresh(m)
    return _map_member(m)


@router.delete("/{jar_id}/members/{user_id}", status_code=204)
def remove_member(jar_id: str, user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(jar_id, current_user.UserId, db, roles=("Owner", "Co-owner"))
    m = db.query(JarMember).filter(JarMember.JarId == jar_id, JarMember.UserId == user_id).first()
    if not m:
        raise HTTPException(404, "Thành viên không tồn tại")
    db.delete(m)
    db.commit()
