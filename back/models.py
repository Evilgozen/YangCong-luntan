from sqlalchemy.orm import relationship
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List

# 基础表模型（不包含关系）
class UserBase(SQLModel):
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    avatar: Optional[str] = None
    bio: Optional[str] = None  # SQLModel 无 Text 类型，可用 str
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

# 数据库表模型
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 定义关系但不作为表字段
    posts: List["Post"] = Relationship(back_populates="author", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    floors: List["Floor"] = Relationship(back_populates="author", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

# 带关系的模型（用于API响应）
class UserRead(UserBase):
    id: int
    posts: List["Post"] = []
    floors: List["Floor"] = []

# 基础帖子模型
class PostBase(SQLModel):
    title: str = Field(index=True)  # 标题，建立索引便于搜索
    content: str  # 帖子内容
    view_count: int = Field(default=0)  # 浏览次数
    is_pinned: bool = Field(default=False)  # 是否置顶
    is_closed: bool = Field(default=False)  # 是否关闭讨论
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: Optional[str] = None  # 可以存储逗号分隔的标签

# 数据库表模型
class Post(PostBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    # 定义关系但不作为表字段
    author: Optional["User"] = Relationship(back_populates="posts")
    floors: List["Floor"] = Relationship(back_populates="post", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

# 基础楼层模型
class FloorBase(SQLModel):
    content: str  # 楼层内容
    floor_number: int  # 楼层号（1楼、2楼等）
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# 数据库表模型
class Floor(FloorBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id")
    author_id: int = Field(foreign_key="user.id")
    reply_to_floor_id: Optional[int] = Field(default=None, foreign_key="floor.id")
    
    # 定义关系但不作为表字段
    post: "Post" = Relationship(back_populates="floors")
    author: "User" = Relationship(back_populates="floors")
    replies: List["Floor"] = Relationship(
        back_populates="reply_to", 
        sa_relationship_kwargs={"foreign_keys": "Floor.reply_to_floor_id"}
    )
    reply_to: Optional["Floor"] = Relationship(
        back_populates="replies", 
        sa_relationship_kwargs={
            "foreign_keys": "Floor.reply_to_floor_id", 
            "remote_side": "Floor.id"
        }
    )
