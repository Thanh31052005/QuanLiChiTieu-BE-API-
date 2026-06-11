"""
Router: /auth
  POST /auth/register  – Đăng ký tài khoản mới
  POST /auth/login     – Đăng nhập, trả về JWT
  GET  /auth/me        – Lấy thông tin người dùng hiện tại
  PUT  /auth/me        – Cập nhật tên / email
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse, UpdateUserRequest
from app.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


# ── Đăng ký ──────────────────────────────────────────────────────────────────
@router.post("/register", response_model=UserResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.Email == body.email).first():
        raise HTTPException(status_code=400, detail="Email đã được sử dụng")

    user = User(
        UserId       = str(uuid.uuid4()),
        FullName     = body.full_name,
        Email        = body.email,
        PasswordHash = hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _map_user(user)


# ── Đăng nhập ────────────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.Email == body.email).first()
    if not user or not verify_password(body.password, user.PasswordHash):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")

    token = create_access_token({"sub": user.UserId})
    return TokenResponse(access_token=token, user=_map_user(user))


# ── Lấy thông tin cá nhân ────────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return _map_user(current_user)


# ── Cập nhật thông tin ───────────────────────────────────────────────────────
@router.put("/me", response_model=UserResponse)
def update_me(
    body: UpdateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.full_name:
        current_user.FullName = body.full_name
    if body.email:
        exists = db.query(User).filter(
            User.Email == body.email, User.UserId != current_user.UserId
        ).first()
        if exists:
            raise HTTPException(status_code=400, detail="Email đã được dùng bởi tài khoản khác")
        current_user.Email = body.email
    db.commit()
    db.refresh(current_user)
    return _map_user(current_user)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _map_user(u: User) -> UserResponse:
    return UserResponse(
        user_id    = u.UserId,
        full_name  = u.FullName,
        email      = u.Email,
        created_at = u.CreatedAt,
    )
