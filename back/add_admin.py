from sqlmodel import Session, select
from passlib.context import CryptContext
from datetime import datetime
import sys
import os

# 确保能够导入项目模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine
import models

# 密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def add_admin_user(username, email, password):
    with Session(engine) as db:
        # 检查用户名是否已存在
        statement = select(models.User).where(models.User.username == username)
        db_user = db.exec(statement).first()
        if db_user:
            print(f"用户名 '{username}' 已存在")
            return False
        
        # 检查邮箱是否已存在
        statement = select(models.User).where(models.User.email == email)
        db_email = db.exec(statement).first()
        if db_email:
            print(f"邮箱 '{email}' 已存在")
            return False
        
        # 创建管理员用户
        hashed_password = get_password_hash(password)
        admin_user = models.User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_admin=True,  # 设置为管理员
            created_at=datetime.now()
        )
        
        # 添加到数据库
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"管理员用户 '{username}' 创建成功！")
        return True

if __name__ == "__main__":
    # 默认管理员信息
    default_username = "admin"
    default_email = "admin@example.com"
    default_password = "admin123"
    
    # 如果有命令行参数，使用命令行参数
    if len(sys.argv) > 3:
        username = sys.argv[1]
        email = sys.argv[2]
        password = sys.argv[3]
    else:
        username = default_username
        email = default_email
        password = default_password
        print("使用默认管理员信息:")
        print(f"用户名: {username}")
        print(f"邮箱: {email}")
        print(f"密码: {password}")
    
    # 添加管理员用户
    add_admin_user(username, email, password)
