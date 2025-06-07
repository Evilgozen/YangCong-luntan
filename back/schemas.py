from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel

# 用户模式
class UserBase(SQLModel):
    username: str
    email: str  # 使用str替代EmailStr以保持兼容性

class UserCreate(UserBase):
    password: str

class UserUpdate(SQLModel):
    email: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None

class UserResponse(UserBase):
    id: int
    avatar: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True  # 从orm_mode = True更新为Pydantic V2兼容性

# 头像上传响应
class AvatarUploadResponse(SQLModel):
    avatar_url: str

# 令牌模式
class Token(SQLModel):
    access_token: str
    token_type: str

class TokenData(SQLModel):
    username: Optional[str] = None

# 帖子模式
class PostBase(SQLModel):
    title: str
    content: str
    tags: Optional[str] = None

class PostCreate(PostBase):
    pass

class PostUpdate(SQLModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_closed: Optional[bool] = None

class PostResponse(PostBase):
    id: int
    author_id: int
    view_count: int
    is_pinned: bool
    is_closed: bool
    created_at: datetime
    updated_at: datetime
    author: UserResponse
    floor_count: Optional[int] = None  # 非数据库字段，用于API返回

    class Config:
        from_attributes = True

# 楼层模式
class FloorBase(SQLModel):
    content: str
    reply_to_floor_id: Optional[int] = None

class FloorCreate(FloorBase):
    post_id: int

class FloorUpdate(SQLModel):
    content: Optional[str] = None

class FloorResponse(FloorBase):
    id: int
    post_id: int
    author_id: int
    floor_number: int
    created_at: datetime
    updated_at: datetime
    author: UserResponse

    class Config:
        from_attributes = True

# 搜索模式
class PostSearchQuery(SQLModel):
    query: str
    tags: Optional[str] = None
    page: int = 1
    page_size: int = 10

class PostSearchResponse(SQLModel):
    total: int
    page: int
    page_size: int
    results: List[PostResponse]

# 个人空间模式
class UserProfileResponse(SQLModel):
    user: UserResponse
    post_count: int
    floor_count: int

class UserPostsResponse(SQLModel):
    total: int
    page: int
    page_size: int
    results: List[PostResponse]
