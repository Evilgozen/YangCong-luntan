from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlmodel import Session, select
from typing import List
import os
import shutil
from pathlib import Path
import uuid

import models
import schemas
from database import get_db
from auth import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# 创建上传目录
UPLOAD_DIR = Path("uploads/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.put("/update", response_model=schemas.UserResponse)
async def update_user_profile(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新当前登录用户的个人资料
    """
    # 获取当前用户
    statement = select(models.User).where(models.User.id == current_user.id)
    db_user = db.exec(statement).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查邮箱是否已被其他用户使用
    if user_update.email and user_update.email != db_user.email:
        email_statement = select(models.User).where(
            (models.User.email == user_update.email) & 
            (models.User.id != current_user.id)
        )
        existing_email = db.exec(email_statement).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="该邮箱已被其他用户使用")
    
    # 更新用户信息
    if user_update.email is not None:
        db_user.email = user_update.email
    if user_update.bio is not None:
        db_user.bio = user_update.bio
    if user_update.avatar is not None:
        db_user.avatar = user_update.avatar
    
    # 提交更改
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/upload-avatar", response_model=schemas.AvatarUploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传用户头像
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只允许上传图片文件")
    
    # 生成唯一文件名
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 构建访问URL
    avatar_url = f"/uploads/avatars/{unique_filename}"
    
    # 更新用户头像
    statement = select(models.User).where(models.User.id == current_user.id)
    db_user = db.exec(statement).first()
    
    # 保存旧头像路径，以便后续可能的清理
    old_avatar = db_user.avatar
    
    # 更新用户头像URL
    db_user.avatar = avatar_url
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"avatar_url": avatar_url}

@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    根据用户ID获取用户信息
    """
    statement = select(models.User).where(models.User.id == user_id)
    user = db.exec(statement).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return user
