from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from typing import List, Optional

from database import get_db
import models
import schemas
from auth import get_current_user

router = APIRouter(
    prefix="/profile",
    tags=["profile"],
    responses={404: {"description": "Not found"}},
)

@router.get("/me", response_model=schemas.UserProfileResponse)
async def get_my_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前登录用户的个人空间信息
    """
    # 查询用户发帖数量
    post_count_query = select(func.count()).where(models.Post.author_id == current_user.id)
    post_count = db.exec(post_count_query).one()
    
    # 查询用户回复数量
    floor_count_query = select(func.count()).where(models.Floor.author_id == current_user.id)
    floor_count = db.exec(floor_count_query).one()
    
    return {
        "user": current_user,
        "post_count": post_count,
        "floor_count": floor_count
    }

@router.get("/users/{user_id}", response_model=schemas.UserProfileResponse)
async def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定用户的个人空间信息
    """
    # 查询用户
    statement = select(models.User).where(models.User.id == user_id)
    user = db.exec(statement).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 查询用户发帖数量
    post_count_query = select(func.count()).where(models.Post.author_id == user_id)
    post_count = db.exec(post_count_query).one()
    
    # 查询用户回复数量
    floor_count_query = select(func.count()).where(models.Floor.author_id == user_id)
    floor_count = db.exec(floor_count_query).one()
    
    return {
        "user": user,
        "post_count": post_count,
        "floor_count": floor_count
    }

@router.get("/me/posts", response_model=schemas.UserPostsResponse)
async def get_my_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前登录用户发布的帖子（分页）
    """
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 查询帖子总数
    total_query = select(func.count()).select_from(models.Post).where(models.Post.author_id == current_user.id)
    total = db.exec(total_query).one()
    
    # 查询帖子列表（按创建时间降序）
    query = (
        select(models.Post)
        .where(models.Post.author_id == current_user.id)
        .order_by(models.Post.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    posts = db.exec(query).all()
    
    # 为每个帖子添加楼层数量
    result_posts = []
    for post in posts:
        floor_count_query = select(func.count()).where(models.Floor.post_id == post.id)
        floor_count = db.exec(floor_count_query).one()
        
        post_dict = {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "view_count": post.view_count,
            "is_pinned": post.is_pinned,
            "is_closed": post.is_closed,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "tags": post.tags,
            "author_id": post.author_id,
            "author": post.author,
            "floor_count": floor_count
        }
        result_posts.append(post_dict)
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": result_posts
    }

@router.get("/users/{user_id}/posts", response_model=schemas.UserPostsResponse)
async def get_user_posts(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取指定用户发布的帖子（分页）
    """
    # 查询用户是否存在
    user_query = select(models.User).where(models.User.id == user_id)
    user = db.exec(user_query).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 查询帖子总数
    total_query = select(func.count()).select_from(models.Post).where(models.Post.author_id == user_id)
    total = db.exec(total_query).one()
    
    # 查询帖子列表（按创建时间降序）
    query = (
        select(models.Post)
        .where(models.Post.author_id == user_id)
        .order_by(models.Post.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    posts = db.exec(query).all()
    
    # 为每个帖子添加楼层数量
    result_posts = []
    for post in posts:
        floor_count_query = select(func.count()).where(models.Floor.post_id == post.id)
        floor_count = db.exec(floor_count_query).one()
        
        post_dict = {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "view_count": post.view_count,
            "is_pinned": post.is_pinned,
            "is_closed": post.is_closed,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "tags": post.tags,
            "author_id": post.author_id,
            "author": post.author,
            "floor_count": floor_count
        }
        result_posts.append(post_dict)
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": result_posts
    }
