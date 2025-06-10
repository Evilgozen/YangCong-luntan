from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime

from database import get_db
import models
import schemas
from auth import get_current_user

router = APIRouter(
    prefix="/follow",
    tags=["follow"],
    responses={404: {"description": "Not found"}},
)

@router.post("", response_model=schemas.FollowResponse)
async def follow_user(
    follow_data: schemas.FollowCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    关注用户
    """
    # 检查要关注的用户是否存在
    statement = select(models.User).where(models.User.id == follow_data.followed_id)
    followed_user = db.exec(statement).first()
    
    if not followed_user:
        raise HTTPException(status_code=404, detail="要关注的用户不存在")
    
    # 不能关注自己
    if current_user.id == follow_data.followed_id:
        raise HTTPException(status_code=400, detail="不能关注自己")
    
    # 检查是否已经关注
    statement = select(models.Follow).where(
        models.Follow.follower_id == current_user.id,
        models.Follow.followed_id == follow_data.followed_id
    )
    existing_follow = db.exec(statement).first()
    
    if existing_follow:
        raise HTTPException(status_code=400, detail="已经关注了该用户")
    
    # 创建关注关系
    new_follow = models.Follow(
        follower_id=current_user.id,
        followed_id=follow_data.followed_id,
        created_at=datetime.now()
    )
    
    db.add(new_follow)
    db.commit()
    db.refresh(new_follow)
    
    # 获取完整的关注信息（包括用户信息）
    statement = select(models.Follow).where(
        models.Follow.follower_id == current_user.id,
        models.Follow.followed_id == follow_data.followed_id
    )
    follow_with_users = db.exec(statement).first()
    
    return follow_with_users

@router.delete("/{user_id}", response_model=dict)
async def unfollow_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取消关注用户
    """
    # 检查要取消关注的用户是否存在
    statement = select(models.User).where(models.User.id == user_id)
    followed_user = db.exec(statement).first()
    
    if not followed_user:
        raise HTTPException(status_code=404, detail="要取消关注的用户不存在")
    
    # 检查是否已经关注
    statement = select(models.Follow).where(
        models.Follow.follower_id == current_user.id,
        models.Follow.followed_id == user_id
    )
    existing_follow = db.exec(statement).first()
    
    if not existing_follow:
        raise HTTPException(status_code=400, detail="未关注该用户")
    
    # 删除关注关系
    db.delete(existing_follow)
    db.commit()
    
    return {"message": "已取消关注"}

@router.get("/followers", response_model=schemas.UserFollowsResponse)
async def get_my_followers(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的粉丝列表
    """
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 查询粉丝总数
    followers_count_query = select(func.count()).select_from(models.Follow).where(
        models.Follow.followed_id == current_user.id
    )
    followers_count = db.exec(followers_count_query).one()
    
    # 查询关注总数
    following_count_query = select(func.count()).select_from(models.Follow).where(
        models.Follow.follower_id == current_user.id
    )
    following_count = db.exec(following_count_query).one()
    
    # 查询粉丝列表
    query = (
        select(models.User)
        .join(models.Follow, models.User.id == models.Follow.follower_id)
        .where(models.Follow.followed_id == current_user.id)
        .offset(offset)
        .limit(page_size)
    )
    followers = db.exec(query).all()
    
    return {
        "followers": followers,
        "following": [],
        "followers_count": followers_count,
        "following_count": following_count,
        "page": page,
        "page_size": page_size
    }

@router.get("/following", response_model=schemas.UserFollowsResponse)
async def get_my_following(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户关注的用户列表
    """
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 查询粉丝总数
    followers_count_query = select(func.count()).select_from(models.Follow).where(
        models.Follow.followed_id == current_user.id
    )
    followers_count = db.exec(followers_count_query).one()
    
    # 查询关注总数
    following_count_query = select(func.count()).select_from(models.Follow).where(
        models.Follow.follower_id == current_user.id
    )
    following_count = db.exec(following_count_query).one()
    
    # 查询关注列表
    query = (
        select(models.User)
        .join(models.Follow, models.User.id == models.Follow.followed_id)
        .where(models.Follow.follower_id == current_user.id)
        .offset(offset)
        .limit(page_size)
    )
    following = db.exec(query).all()
    
    return {
        "followers": [],
        "following": following,
        "followers_count": followers_count,
        "following_count": following_count,
        "page": page,
        "page_size": page_size
    }

@router.get("/users/{user_id}/followers", response_model=schemas.UserFollowsResponse)
async def get_user_followers(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定用户的粉丝列表
    """
    # 检查用户是否存在
    statement = select(models.User).where(models.User.id == user_id)
    user = db.exec(statement).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 查询粉丝总数
    followers_count_query = select(func.count()).select_from(models.Follow).where(
        models.Follow.followed_id == user_id
    )
    followers_count = db.exec(followers_count_query).one()
    
    # 查询关注总数
    following_count_query = select(func.count()).select_from(models.Follow).where(
        models.Follow.follower_id == user_id
    )
    following_count = db.exec(following_count_query).one()
    
    # 查询粉丝列表
    query = (
        select(models.User)
        .join(models.Follow, models.User.id == models.Follow.follower_id)
        .where(models.Follow.followed_id == user_id)
        .offset(offset)
        .limit(page_size)
    )
    followers = db.exec(query).all()
    
    return {
        "followers": followers,
        "following": [],
        "followers_count": followers_count,
        "following_count": following_count,
        "page": page,
        "page_size": page_size
    }

@router.get("/users/{user_id}/following", response_model=schemas.UserFollowsResponse)
async def get_user_following(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定用户关注的用户列表
    """
    # 检查用户是否存在
    statement = select(models.User).where(models.User.id == user_id)
    user = db.exec(statement).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 查询粉丝总数
    followers_count_query = select(func.count()).select_from(models.Follow).where(
        models.Follow.followed_id == user_id
    )
    followers_count = db.exec(followers_count_query).one()
    
    # 查询关注总数
    following_count_query = select(func.count()).select_from(models.Follow).where(
        models.Follow.follower_id == user_id
    )
    following_count = db.exec(following_count_query).one()
    
    # 查询关注列表
    query = (
        select(models.User)
        .join(models.Follow, models.User.id == models.Follow.followed_id)
        .where(models.Follow.follower_id == user_id)
        .offset(offset)
        .limit(page_size)
    )
    following = db.exec(query).all()
    
    return {
        "followers": [],
        "following": following,
        "followers_count": followers_count,
        "following_count": following_count,
        "page": page,
        "page_size": page_size
    }

@router.get("/check/{user_id}", response_model=dict)
async def check_follow_status(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    检查当前用户是否关注了指定用户
    """
    # 检查用户是否存在
    statement = select(models.User).where(models.User.id == user_id)
    user = db.exec(statement).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查是否已关注
    statement = select(models.Follow).where(
        models.Follow.follower_id == current_user.id,
        models.Follow.followed_id == user_id
    )
    existing_follow = db.exec(statement).first()
    
    return {"is_following": existing_follow is not None}
