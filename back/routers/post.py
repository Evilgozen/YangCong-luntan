from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, or_, func
from typing import List, Optional
from datetime import datetime

from database import get_db
import models
import schemas
from auth import get_current_user

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
    responses={404: {"description": "Not found"}},
)

# 创建帖子
@router.post("/", response_model=schemas.PostResponse)
def create_post(
    post: schemas.PostCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_post = models.Post(
        title=post.title,
        content=post.content,
        tags=post.tags,
        author_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    # 创建第一个楼层（楼主发言）
    floor = models.Floor(
        content=post.content,
        post_id=db_post.id,
        author_id=current_user.id,
        floor_number=1,  # 第一楼
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(floor)
    db.commit()
    
    return db_post

# 获取所有帖子（分页）
@router.get("/", response_model=schemas.PostSearchResponse)
def get_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 查询帖子总数
    total_query = select(func.count()).select_from(models.Post)
    total = db.exec(total_query).one()
    
    # 查询帖子列表（按创建时间降序，置顶优先）
    query = (
        select(models.Post)
        .order_by(models.Post.is_pinned.desc(), models.Post.created_at.desc())
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
        
        # 查询当前用户是否点赞
        statement = select(models.PostLike).where(
            models.PostLike.user_id == current_user.id,
            models.PostLike.post_id == post.id
        )
        is_liked = db.exec(statement).first() is not None
        
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
            "is_liked": is_liked
        }
        result_posts.append(post_dict)
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": result_posts
    }

# 搜索帖子
@router.get("/search", response_model=schemas.PostSearchResponse)
def search_posts(
    query: str = "",
    tags: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 构建搜索条件
    conditions = []
    if query:
        conditions.append(models.Post.title.contains(query))
        conditions.append(models.Post.content.contains(query))
    
    if tags:
        for tag in tags.split(','):
            tag = tag.strip()
            if tag:
                conditions.append(models.Post.tags.contains(tag))
    
    # 如果有搜索条件，则使用OR组合
    if conditions:
        search_condition = or_(*conditions)
        
        # 查询帖子总数
        total_query = select(func.count()).select_from(models.Post).where(search_condition)
        total = db.exec(total_query).one()
        
        # 查询帖子列表
        query = (
            select(models.Post)
            .where(search_condition)
            .order_by(models.Post.is_pinned.desc(), models.Post.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
    else:
        # 无搜索条件时，返回所有帖子
        total_query = select(func.count()).select_from(models.Post)
        total = db.exec(total_query).one()
        
        query = (
            select(models.Post)
            .order_by(models.Post.is_pinned.desc(), models.Post.created_at.desc())
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

# 获取单个帖子详情
@router.get("/{post_id}", response_model=schemas.PostResponse)
def get_post(
    post_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 查询帖子
    statement = select(models.Post).where(models.Post.id == post_id)
    post = db.exec(statement).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 增加浏览次数
    post.view_count += 1
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # 查询楼层数量
    floor_count_query = select(func.count()).where(models.Floor.post_id == post_id)
    floor_count = db.exec(floor_count_query).one()
    
    # 查询点赞数量
    like_count_query = select(func.count()).where(models.PostLike.post_id == post_id)
    like_count = db.exec(like_count_query).one()
    
    # 查询当前用户是否点赞
    statement = select(models.PostLike).where(
        models.PostLike.user_id == current_user.id,
        models.PostLike.post_id == post_id
    )
    is_liked = db.exec(statement).first() is not None
    
    # 添加楼层数量和点赞信息到响应中
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
        "is_liked": is_liked
    }
    
    return post_dict

# 更新帖子
@router.put("/{post_id}", response_model=schemas.PostResponse)
def update_post(
    post_id: int,
    post_update: schemas.PostUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 查询帖子
    query = select(models.Post).where(models.Post.id == post_id)
    db_post = db.exec(query).first()
    
    if not db_post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 检查权限（只有作者或管理员可以更新）
    if db_post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有权限更新此帖子")
    
    # 更新帖子字段
    update_data = post_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_post, key, value)
    
    # 更新时间
    db_post.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_post)
    
    return db_post

# 删除帖子
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 查询帖子
    query = select(models.Post).where(models.Post.id == post_id)
    db_post = db.exec(query).first()
    
    if not db_post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 检查权限（只有作者或管理员可以删除）
    if db_post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有权限删除此帖子")
    
    # 先删除关联的楼层
    floor_query = select(models.Floor).where(models.Floor.post_id == post_id)
    floors = db.exec(floor_query).all()
    for floor in floors:
        db.delete(floor)
    
    # 删除帖子
    db.delete(db_post)
    db.commit()
    
    return None
