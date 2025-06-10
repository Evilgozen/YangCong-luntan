"""
预训练RNN模型并保存参数
运行此脚本会预先训练模型并保存到nickname_model.pkl文件中
"""

import os
import sys
import time
from nickname_generator import NicknameGenerator

def main():
    print("开始预训练RNN昵称生成模型...")
    start_time = time.time()
    
    # 创建生成器实例
    generator = NicknameGenerator()
    
    # 训练模型 (可以根据需要调整迭代次数)
    print(f"训练开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    generator.train(num_iterations=35000, n_a=50, dino_names=5)
    
    # 训练完成后保存模型
    generator.save_model()
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"训练结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总训练时间: {duration:.2f}秒 ({duration/60:.2f}分钟)")
    
    # 生成一些示例昵称
    print("\n生成示例昵称:")
    nicknames = generator.generate_nicknames(10)
    for i, nickname in enumerate(nicknames, 1):
        print(f"{i}. {nickname}")

if __name__ == "__main__":
    main()
