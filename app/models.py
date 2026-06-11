"""
ORM Models – mapping 1:1 với Query_Data.sql (ManageMoneyDB)

Bảng:
  1. Users
  2. Categories
  3. Jars
  4. JarMembers
  5. Transactions
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, Numeric, SmallInteger,
    DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


# ── 1. Users ─────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "Users"

    UserId       = Column(String(36), primary_key=True, default=new_uuid)
    FullName     = Column(String(100), nullable=False)
    Email        = Column(String(150), unique=True, nullable=False)
    PasswordHash = Column(String(255), nullable=False)
    CreatedAt    = Column(DateTime, default=datetime.utcnow)

    # Relationships
    jars_created  = relationship("Jar",        back_populates="creator",         foreign_keys="Jar.CreatedByUserId")
    memberships   = relationship("JarMember",  back_populates="user")
    transactions  = relationship("Transaction", back_populates="user")


# ── 2. Categories ─────────────────────────────────────────────────────────────
class Category(Base):
    __tablename__ = "Categories"

    CategoryId   = Column(Integer, primary_key=True, autoincrement=True)
    CategoryName = Column(String(100), nullable=False)
    # BIT: True = Income (Thu), False = Expense (Chi)
    CategoryType = Column(Boolean, nullable=False)
    IconUrl      = Column(String(255), nullable=True)

    # Relationships
    transactions = relationship("Transaction", back_populates="category")


# ── 3. Jars ───────────────────────────────────────────────────────────────────
class Jar(Base):
    __tablename__ = "Jars"

    JarId           = Column(String(36), primary_key=True, default=new_uuid)
    JarName         = Column(String(100), nullable=False)
    Description     = Column(String(255), nullable=True)
    Budget          = Column(Numeric(18, 2), default=0)
    # TINYINT: 1 = Personal, 2 = Shared/Group
    JarType         = Column(SmallInteger, default=1)
    CreatedByUserId = Column(String(36), ForeignKey("Users.UserId"), nullable=False)
    CreatedAt       = Column(DateTime, default=datetime.utcnow)

    # Relationships
    creator      = relationship("User",        back_populates="jars_created", foreign_keys=[CreatedByUserId])
    members      = relationship("JarMember",   back_populates="jar",  cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="jar",  cascade="all, delete-orphan")


# ── 4. JarMembers ─────────────────────────────────────────────────────────────
class JarMember(Base):
    __tablename__ = "JarMembers"
    __table_args__ = (
        UniqueConstraint("JarId", "UserId", name="PK_JarMembers"),
    )

    JarId    = Column(String(36), ForeignKey("Jars.JarId"),  primary_key=True)
    UserId   = Column(String(36), ForeignKey("Users.UserId"), primary_key=True)
    # 'Owner' | 'Co-owner' | 'Member'
    Role     = Column(String(20), default="Member")
    JoinedAt = Column(DateTime, default=datetime.utcnow)

    # Relationships
    jar  = relationship("Jar",  back_populates="members")
    user = relationship("User", back_populates="memberships")


# ── 5. Transactions ───────────────────────────────────────────────────────────
class Transaction(Base):
    __tablename__ = "Transactions"

    TransactionId   = Column(String(36), primary_key=True, default=new_uuid)
    JarId           = Column(String(36), ForeignKey("Jars.JarId"),        nullable=False)
    UserId          = Column(String(36), ForeignKey("Users.UserId"),       nullable=False)
    CategoryId      = Column(Integer,    ForeignKey("Categories.CategoryId"), nullable=False)
    Amount          = Column(Numeric(18, 2), nullable=False)
    Description     = Column(String(500), nullable=True)
    ReceiptImageUrl = Column(String(500), nullable=True)  # URL ảnh hóa đơn
    # BIT: True = Income (Thu), False = Expense (Chi)
    TransactionType = Column(Boolean, nullable=False)
    TransactionDate = Column(DateTime, default=datetime.utcnow)

    # Relationships
    jar      = relationship("Jar",      back_populates="transactions")
    user     = relationship("User",     back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
