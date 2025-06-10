from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, SQLModel, select
from datetime import datetime, timedelta
from passlib.context import CryptContext
from pathlib import Path

import models
import schemas
from database import engine, get_db
from auth import get_current_user, create_access_token
from routers import post, floor, user, profile, follow, nickname

# 为所有表模型创建表，会根据database的元数据自动创建
SQLModel.metadata.create_all(engine)

app = FastAPI(title="论坛 API")

origins = [
    "http://localhost:5173",
    "http://124.156.207.70",
]

# CORS 的跨域请求配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 对于来源 url 的配置
    allow_credentials=True, # 跨域请求支持 cookie
    allow_methods=["*"],
    allow_headers=["*"], # 拦截器，考虑 bearer 规范？
)

# 密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    statement = select(models.User).where(models.User.username == username)
    user = db.exec(statement).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

# 创建上传目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
AVATAR_DIR = UPLOAD_DIR / "avatars"
AVATAR_DIR.mkdir(exist_ok=True)

# 挂载静态文件目录
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 使用 SQLModel 的 select 语句替代 db.query
    statement = select(models.User).where(models.User.username == user.username)
    db_user = db.exec(statement).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已经注册")
    
    # 检查邮箱是否存在
    statement = select(models.User).where(models.User.email == user.email)
    db_email = db.exec(statement).first()
    if db_email:
        raise HTTPException(status_code=400, detail="邮箱已经注册")
    
    # 创建新用户
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        created_at=datetime.now()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 更新用户的最后登录时间
    user.last_login = datetime.now()
    db.add(user)
    db.commit()
    
    access_token_expires = timedelta(minutes=30)  # 使用与auth.py中相同的过期时间
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.get("/")
def read_root():
    return {"message": "欢迎使用论坛 API"}

# 包含路由
app.include_router(post.router)
app.include_router(floor.router)
app.include_router(user.router)
app.include_router(profile.router)
app.include_router(follow.router)
app.include_router(nickname.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
