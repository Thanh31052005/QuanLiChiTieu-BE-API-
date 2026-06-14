"""
Pydantic Schemas – Request / Response bodies cho tất cả routers
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ═══════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════
class RegisterRequest(BaseModel):
    full_name: str  = Field(..., min_length=2,  max_length=100)
    email:     EmailStr
    password:  str  = Field(..., min_length=6,  max_length=128)


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserResponse


# ═══════════════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════════════
class UserResponse(BaseModel):
    user_id:    str
    full_name:  str
    email:      str
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email:     Optional[EmailStr] = None


# ═══════════════════════════════════════════════════════════════════
# CATEGORIES
# ═══════════════════════════════════════════════════════════════════
class CategoryResponse(BaseModel):
    category_id:   int
    category_name: str
    category_type: bool   # True = Thu (Income), False = Chi (Expense)
    icon_url:      Optional[str]

    class Config:
        from_attributes = True


class CreateCategoryRequest(BaseModel):
    category_name: str  = Field(..., min_length=1, max_length=100)
    category_type: bool
    icon_url:      Optional[str] = None


# ═══════════════════════════════════════════════════════════════════
# JARS
# ═══════════════════════════════════════════════════════════════════
class JarResponse(BaseModel):
    jar_id:             str
    jar_name:           str
    description:        Optional[str]
    budget:             float
    jar_type:           int   # 1 = Personal, 2 = Shared
    created_by_user_id: str
    created_at:         datetime
    # Tính toán từ Transactions
    spent_amount:       float = 0.0
    income_amount:      float = 0.0
    balance:            float = 0.0
    remaining:          float = 0.0
    usage_percent:      float = 0.0

    class Config:
        from_attributes = True


class CreateJarRequest(BaseModel):
    jar_name:    str   = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    budget:      float = Field(0, ge=0)
    jar_type:    int   = Field(1, ge=1, le=3)   # 1=Personal, 2=Shared, 3=Savings


class UpdateJarRequest(BaseModel):
    jar_name:    Optional[str]   = Field(None, min_length=1, max_length=100)
    description: Optional[str]   = None
    budget:      Optional[float] = Field(None, ge=0)
    jar_type:    Optional[int]   = Field(None, ge=1, le=3)


# ═══════════════════════════════════════════════════════════════════
# JAR MEMBERS
# ═══════════════════════════════════════════════════════════════════
class JarMemberResponse(BaseModel):
    jar_id:    str
    user_id:   str
    role:      str
    joined_at: datetime
    user:      Optional[UserResponse] = None

    class Config:
        from_attributes = True


class AddMemberRequest(BaseModel):
    user_id: str
    role:    str = Field("Member", pattern="^(Owner|Co-owner|Member)$")


class UpdateMemberRoleRequest(BaseModel):
    role: str = Field(..., pattern="^(Owner|Co-owner|Member)$")


# ═══════════════════════════════════════════════════════════════════
# TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════
class TransactionResponse(BaseModel):
    transaction_id:   str
    jar_id:           str
    user_id:          str
    category_id:      int
    amount:           float
    description:      Optional[str]
    receipt_image_url: Optional[str]
    transaction_type: bool   # True = Thu, False = Chi
    transaction_date: datetime
    # Join data
    category_name:    Optional[str] = None
    jar_name:         Optional[str] = None

    class Config:
        from_attributes = True


class CreateTransactionRequest(BaseModel):
    jar_id:           str
    category_id:      int
    amount:           float = Field(..., gt=0)
    description:      Optional[str] = None
    transaction_type: bool           # True = Thu, False = Chi
    transaction_date: Optional[datetime] = None


class UpdateTransactionRequest(BaseModel):
    category_id:      Optional[int]      = None
    amount:           Optional[float]    = Field(None, gt=0)
    description:      Optional[str]      = None
    transaction_type: Optional[bool]     = None
    transaction_date: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════════════
# THỐNG KÊ / DASHBOARD
# ═══════════════════════════════════════════════════════════════════
class DashboardResponse(BaseModel):
    total_balance:      float
    total_income:       float
    total_expense:      float
    saving_rate:        float   # % tiết kiệm
    jars:               List[JarResponse]
    recent_transactions: List[TransactionResponse]


class MonthlySummary(BaseModel):
    month:         int
    year:          int
    total_income:  float
    total_expense: float
    net:           float
