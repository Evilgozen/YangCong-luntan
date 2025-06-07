from sqlmodel import SQLModel, create_engine, Session

# 数据库uri
My_SQLLite = "sqlite:///./forum.db"

# 创建连接
engine = create_engine(
    My_SQLLite, connect_args={"check_same_thread": False}
)

# 获取会话
def get_db():
    with Session(engine) as session:
        yield session
