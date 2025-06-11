from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime

from database import get_db
import models
import schemas
from auth import get_current_user

router = APIRouter(
    prefix="/likes",
    tags=["likes"],
    responses={404: {"description": "Not found"}},
)

@router.post("", response_model=schemas.PostLikeResponse)
async def like_post(
    like_data: schemas.PostLikeCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    点赞帖子
    """
    # 检查帖子是否存在
    statement = select(models.Post).where(models.Post.id == like_data.post_id)
    post = db.exec(statement).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 检查是否已经点赞
    statement = select(models.PostLike).where(
        models.PostLike.user_id == current_user.id,
        models.PostLike.post_id == like_data.post_id
    )
    existing_like = db.exec(statement).first()
    
    if existing_like:
        raise HTTPException(status_code=400, detail="已经点赞了该帖子")
    
    # 创建点赞关系
    new_like = models.PostLike(
        user_id=current_user.id,
        post_id=like_data.post_id,
        created_at=datetime.now()
    )
    
    db.add(new_like)
    db.commit()
    db.refresh(new_like)
    
    return new_like

@router.delete("/{post_id}", response_model=dict)
async def unlike_post(
    post_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取消点赞帖子
    """
    # 检查帖子是否存在
    statement = select(models.Post).where(models.Post.id == post_id)
    post = db.exec(statement).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 检查是否已经点赞
    statement = select(models.PostLike).where(
        models.PostLike.user_id == current_user.id,
        models.PostLike.post_id == post_id
    )
    existing_like = db.exec(statement).first()
    
    if not existing_like:
        raise HTTPException(status_code=400, detail="未点赞该帖子")
    
    # 删除点赞关系
    db.delete(existing_like)
    db.commit()
    
    return {"message": "已取消点赞"}

@router.get("/posts/{post_id}", response_model=schemas.PostLikesResponse)
async def get_post_likes(
    post_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取帖子的点赞列表
    """
    # 检查帖子是否存在
    statement = select(models.Post).where(models.Post.id == post_id)
    post = db.exec(statement).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 查询点赞总数
    like_count_query = select(func.count()).select_from(models.PostLike).where(
        models.PostLike.post_id == post_id
    )
    like_count = db.exec(like_count_query).one()
    
    # 查询当前用户是否点赞
    statement = select(models.PostLike).where(
        models.PostLike.user_id == current_user.id,
        models.PostLike.post_id == post_id
    )
    is_liked = db.exec(statement).first() is not None
    
    # 查询点赞列表
    query = (
        select(models.PostLike)
        .where(models.PostLike.post_id == post_id)
        .order_by(models.PostLike.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    likes = db.exec(query).all()
    
    return {
        "likes": likes,
        "like_count": like_count,
        "is_liked": is_liked,
        "page": page,
        "page_size": page_size
    }

@router.get("/users/me/liked-posts", response_model=schemas.PostSearchResponse)
async def get_my_liked_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户点赞的帖子列表
    """
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 查询点赞帖子总数
    total_query = select(func.count()).select_from(models.PostLike).where(
        models.PostLike.user_id == current_user.id
    )
    total = db.exec(total_query).one()
    
    # 查询点赞帖子列表
    query = (
        select(models.Post)
        .join(models.PostLike, models.Post.id == models.PostLike.post_id)
        .where(models.PostLike.user_id == current_user.id)
        .order_by(models.PostLike.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    posts = db.exec(query).all()
    
    # 为每个帖子添加楼层数量和点赞信息
    result_posts = []
    for post in posts:
        # 查询楼层数量
        floor_count_query = select(func.count()).where(models.Floor.post_id == post.id)
        floor_count = db.exec(floor_count_query).one()
        
        # 查询点赞数量
        like_count_query = select(func.count()).where(models.PostLike.post_id == post.id)
        like_count = db.exec(like_count_query).one()
        
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
            "floor_count": floor_count,
            "like_count": like_count,
            "is_liked": True  # 当前用户肯定点赞了这些帖子
        }
        result_posts.append(post_dict)
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": result_posts
    }