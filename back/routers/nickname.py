from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any
import os
import sys
import time
import threading
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the RNN directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "RNN"))

# Import the nickname generator
from RNN.nickname_generator import NicknameGenerator

router = APIRouter(
    prefix="/nickname",
    tags=["nickname"],
    responses={404: {"description": "Not found"}},
)

# 初始化状态
model_status = {"trained": False, "training": False, "last_trained": None, "progress": 0}

# 训练进度回调函数
def training_progress_callback(iteration, total_iterations, loss, sample_nicknames):
    global model_status
    progress = min(100, int((iteration / total_iterations) * 100))
    model_status["progress"] = progress
    model_status["current_loss"] = loss
    if sample_nicknames:
        model_status["sample_nicknames"] = sample_nicknames
    logger.info(f"训练进度: {progress}%, 迭代: {iteration}/{total_iterations}, Loss: {loss}")

# 初始化生成器
generator = NicknameGenerator()

# 检查是否有预训练模型
if generator.load_model():
    model_status["trained"] = True
    model_status["last_trained"] = time.strftime("%Y-%m-%d %H:%M:%S")
    logger.info("预训练模型加载成功")
else:
    logger.info("未找到预训练模型，需要手动训练或运行预训练脚本")

# 后台训练函数
def train_model_background():
    global model_status
    try:
        model_status["training"] = True
        model_status["progress"] = 0
        # 使用回调函数跟踪训练进度
        generator.train(num_iterations=20000, callback=training_progress_callback)
        model_status["trained"] = True
        model_status["training"] = False
        model_status["last_trained"] = time.strftime("%Y-%m-%d %H:%M:%S")
        model_status["progress"] = 100
        logger.info("模型训练完成")
    except Exception as e:
        model_status["training"] = False
        model_status["error"] = str(e)
        logger.error(f"训练模型时出错: {str(e)}")

@router.get("/generate", response_model=List[str])
async def generate_nicknames(
    count: int = Query(5, ge=1, le=20, description="生成昵称的数量"),
    seed: int = Query(None, description="随机种子，用于生成可重复的结果"),
    max_length: int = Query(10, ge=2, le=20, description="生成昵称的长度"),
    exact_length: bool = Query(False, description="是否生成精确长度的昵称")
):
    """
    使用RNN模型生成有趣的昵称
    """
    # 检查模型是否已训练或已加载
    if not generator.parameters:
        # 尝试加载模型
        if os.path.exists(generator.model_path):
            success = generator.load_model()
            if success:
                model_status["trained"] = True
                logger.info("已成功加载模型")
            else:
                logger.error("加载模型失败")
                raise HTTPException(status_code=503, detail="模型未训练，且无法加载现有模型")
        else:
            logger.error("模型文件不存在")
            raise HTTPException(status_code=503, detail="模型未训练，请先训练模型")
    
    try:
        # 生成昵称
        nicknames = generator.generate_nicknames(
            num_nicknames=count, 
            seed=seed, 
            max_length=max_length,
            min_length=2,  # 最小长度设为2
            exact_length=exact_length  # 是否使用精确长度
        )
        logger.info(f"成功生成{len(nicknames)}个昵称")
        return nicknames
    except Exception as e:
        logger.error(f"生成昵称时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成昵称失败: {str(e)}")

@router.post("/train", response_model=Dict[str, Any])
async def train_model(background_tasks: BackgroundTasks):
    """
    在昵称数据上训练RNN模型
    """
    global model_status
    
    # 检查是否已经在训练中
    if model_status["training"]:
        return {"status": "training", "message": "模型正在训练中", "progress": model_status.get("progress", 0)}
    
    # 在后台线程中开始训练
    training_thread = threading.Thread(target=train_model_background)
    training_thread.daemon = True
    training_thread.start()
    
    return {"status": "started", "message": "模型训练已在后台启动", "progress": 0}

@router.get("/status", response_model=Dict[str, Any])
async def get_model_status():
    """
    获取模型的当前状态
    """
    # 添加更多状态信息
    status_info = {
        "trained": model_status.get("trained", False),
        "training": model_status.get("training", False),
        "last_trained": model_status.get("last_trained"),
        "progress": model_status.get("progress", 0)
    }
    
    # 如果有样本昵称，添加到状态信息中
    if "sample_nicknames" in model_status:
        status_info["sample_nicknames"] = model_status["sample_nicknames"]
    
    # 如果有错误信息，添加到状态信息中
    if "error" in model_status:
        status_info["error"] = model_status["error"]
    
    # 如果有当前损失值，添加到状态信息中
    if "current_loss" in model_status:
        status_info["current_loss"] = model_status["current_loss"]
        
    return status_info
