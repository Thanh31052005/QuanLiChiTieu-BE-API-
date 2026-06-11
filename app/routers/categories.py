"""
Router: /categories
  GET    /categories          – Lấy tất cả danh mục (có thể lọc thu/chi)
  GET    /categories/{id}     – Chi tiết danh mục
  POST   /categories          – Tạo danh mục mới (cần đăng nhập)
  PUT    /categories/{id}     – Cập nhật
  DELETE /categories/{id}     – Xoá
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Category, User
from app.schemas import CategoryResponse, CreateCategoryRequest
from app.security import get_current_user

router = APIRouter(prefix="/categories", tags=["Categories"])


def _map(c: Category) -> CategoryResponse:
    return CategoryResponse(
        category_id   = c.CategoryId,
        category_name = c.CategoryName,
        category_type = bool(c.CategoryType),
        icon_url      = c.IconUrl,
    )


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    is_income: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Category)
    if is_income is not None:
        q = q.filter(Category.CategoryType == is_income)
    return [_map(c) for c in q.all()]


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    c = db.query(Category).filter(Category.CategoryId == category_id).first()
    if not c:
        raise HTTPException(404, "Danh mục không tồn tại")
    return _map(c)


@router.post("", response_model=CategoryResponse, status_code=201)
def create_category(
    body: CreateCategoryRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cat = Category(
        CategoryName = body.category_name,
        CategoryType = body.category_type,
        IconUrl      = body.icon_url,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return _map(cat)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    body: CreateCategoryRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cat = db.query(Category).filter(Category.CategoryId == category_id).first()
    if not cat:
        raise HTTPException(404, "Danh mục không tồn tại")
    cat.CategoryName = body.category_name
    cat.CategoryType = body.category_type
    cat.IconUrl      = body.icon_url
    db.commit()
    db.refresh(cat)
    return _map(cat)


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cat = db.query(Category).filter(Category.CategoryId == category_id).first()
    if not cat:
        raise HTTPException(404, "Danh mục không tồn tại")
    db.delete(cat)
    db.commit()
