from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from typing import List
from datetime import datetime

from database import get_db
import models
import schemas
from auth import get_current_user

router = APIRouter(
    prefix="/floors",
    tags=["floors"],
    responses={404: {"description": "Not found"}},
)

# 获取帖子的所有楼层
@router.get("/post/{post_id}", response_model=List[schemas.FloorResponse])
def get_floors_by_post(
    post_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查帖子是否存在
    post_query = select(models.Post).where(models.Post.id == post_id)
    post = db.exec(post_query).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 查询楼层（按楼层号排序）
    query = (
        select(models.Floor)
        .where(models.Floor.post_id == post_id)
        .order_by(models.Floor.floor_number)
        .offset(offset)
        .limit(page_size)
    )
    floors = db.exec(query).all()
    
    return floors

# 创建新楼层（回复）
@router.post("/", response_model=schemas.FloorResponse)
def create_floor(
    floor: schemas.FloorCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查帖子是否存在
    post_query = select(models.Post).where(models.Post.id == floor.post_id)
    post = db.exec(post_query).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 检查帖子是否已关闭
    if post.is_closed:
        raise HTTPException(status_code=400, detail="该帖子已关闭，无法回复")
    
    # 检查回复的楼层是否存在
    if floor.reply_to_floor_id:
        reply_floor_query = select(models.Floor).where(models.Floor.id == floor.reply_to_floor_id)
        reply_floor = db.exec(reply_floor_query).first()
        if not reply_floor:
            raise HTTPException(status_code=404, detail="回复的楼层不存在")
    
    # 获取当前最大楼层号
    max_floor_query = select(func.max(models.Floor.floor_number)).where(models.Floor.post_id == floor.post_id)
    max_floor = db.exec(max_floor_query).one() or 0
    
    # 创建新楼层
    new_floor = models.Floor(
        content=floor.content,
        post_id=floor.post_id,
        author_id=current_user.id,
        floor_number=max_floor + 1,
        reply_to_floor_id=floor.reply_to_floor_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(new_floor)
    db.commit()
    db.refresh(new_floor)
    
    # 更新帖子的更新时间
    post.updated_at = datetime.utcnow()
    db.commit()
    
    return new_floor

# 更新楼层
@router.put("/{floor_id}", response_model=schemas.FloorResponse)
def update_floor(
    floor_id: int,
    floor_update: schemas.FloorUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 查询楼层
    query = select(models.Floor).where(models.Floor.id == floor_id)
    db_floor = db.exec(query).first()
    
    if not db_floor:
        raise HTTPException(status_code=404, detail="楼层不存在")
    
    # 检查权限（只有作者或管理员可以更新）
    if db_floor.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有权限更新此楼层")
    
    # 更新楼层内容
    db_floor.content = floor_update.content
    db_floor.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_floor)
    
    return db_floor

# 删除楼层
@router.delete("/{floor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_floor(
    floor_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 查询楼层
    query = select(models.Floor).where(models.Floor.id == floor_id)
    db_floor = db.exec(query).first()
    
    if not db_floor:
        raise HTTPException(status_code=404, detail="楼层不存在")
    
    # 检查权限（只有作者或管理员可以删除）
    if db_floor.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有权限删除此楼层")
    
    # 检查是否是一楼（帖子的第一个楼层）
    if db_floor.floor_number == 1:
        # 如果是一楼，需要删除整个帖子
        post_query = select(models.Post).where(models.Post.id == db_floor.post_id)
        post = db.exec(post_query).first()
        if post:
            # 删除所有相关楼层
            floors_query = select(models.Floor).where(models.Floor.post_id == post.id)
            floors = db.exec(floors_query).all()
            for floor in floors:
                db.delete(floor)
            
            # 删除帖子
            db.delete(post)
    else:
        # 如果不是一楼，删除该楼层及其所有回复
        # 递归删除所有回复
        def delete_floor_and_replies(floor_id):
            replies_query = select(models.Floor).where(models.Floor.reply_to_floor_id == floor_id)
            replies = db.exec(replies_query).all()
            
            for reply in replies:
                delete_floor_and_replies(reply.id)
                db.delete(reply)
        
        # 删除所有回复
        delete_floor_and_replies(floor_id)
        # 删除当前楼层
        db.delete(db_floor)
    
    db.commit()
    
    return None
