import numpy as np
import pickle
import os
import jieba
import time
import random
# 明确导入utils中的所有函数
from utils import (
    softmax,
    smooth,
    get_initial_loss,
    initialize_parameters,
    rnn_forward,
    rnn_backward,
    update_parameters,
    clip,
    sample,
    optimize
)

class NicknameGenerator:
    def __init__(self, model_path=None):
        """
        Initialize the nickname generator with a pre-trained model
        """
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), "nickname_model.pkl")
        self.parameters = None
        self.char_to_ix = None
        self.ix_to_char = None
        
        # Try to load the model if it exists
        self.load_model()
    
    def load_model(self):
        """
        Load a pre-trained model if it exists
        """
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.parameters = model_data['parameters']
                    self.char_to_ix = model_data['char_to_ix']
                    self.ix_to_char = model_data['ix_to_char']
                print("Model loaded successfully!")
                return True
            except Exception as e:
                print(f"Error loading model: {e}")
        return False
    
    def save_model(self):
        """
        Save the trained model
        """
        if self.parameters and self.char_to_ix and self.ix_to_char:
            model_data = {
                'parameters': self.parameters,
                'char_to_ix': self.char_to_ix,
                'ix_to_char': self.ix_to_char
            }
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            print("Model saved successfully!")
            return True
        return False
    
    def load_data(self, filename):
        """
        Load training data and create character mappings
        """
        data = open(filename, 'r', encoding='utf-8').readlines()
        words = []
        for word in data:
            word = word.strip()
            if word:  # Skip empty lines
                words += jieba.lcut(word)
        
        vocabulary = set(words)
        print(f"Vocabulary size: {len(vocabulary)}")
        
        data_size, vocab_size = len(words), len(vocabulary)
        print(f'There are {data_size} total words and {vocab_size} unique words in your data.')
        
        self.char_to_ix = {word: i for i, word in enumerate(vocabulary)}
        self.ix_to_char = {i: word for i, word in enumerate(vocabulary)}
        
        return words
    
    def train(self, filename="nicknames.txt", num_iterations=10000, n_a=50, dino_names=5, callback=None):
        """
        Train the RNN model on the nickname data
        
        Args:
            filename: 训练数据文件名
            num_iterations: 训练迭代次数
            n_a: 隐藏层维度
            dino_names: 每次采样生成的昵称数量
            callback: 回调函数，用于报告训练进度，格式为callback(iteration, total_iterations, loss, sample_nicknames)
        """
        # Load data
        words = self.load_data(filename)
        vocab_size = len(self.char_to_ix)
        
        # Initialize parameters
        n_x, n_y = vocab_size, vocab_size
        self.parameters = initialize_parameters(n_a, n_x, n_y)
        
        # Initialize loss
        loss = get_initial_loss(vocab_size, dino_names)
        
        # Build list of all nicknames (training examples)
        with open(filename, 'r', encoding='utf-8') as f:
            examples = f.readlines()
        examples = [jieba.lcut(x.strip()) for x in examples if x.strip()]
        
        # Shuffle list of all nicknames
        np.random.seed(0)
        np.random.shuffle(examples)
        
        # Initialize the hidden state
        a_prev = np.zeros((n_a, 1))
        
        # Optimization loop
        for j in range(num_iterations):
            # Define one training example
            index = j % len(examples)
            X = [None] + [self.char_to_ix[ch] for ch in examples[index] if ch in self.char_to_ix]
            Y = X[1:] + [self.char_to_ix["\n"] if "\n" in self.char_to_ix else 0]
            
            # Perform one optimization step
            curr_loss, gradients, a_prev = optimize(X, Y, a_prev, self.parameters, learning_rate=0.01, vocab_size=vocab_size)
            
            # Smooth the loss
            loss = smooth(loss, curr_loss)
            
            # Print progress and generate samples
            if j % 1000 == 0:
                print(f'Iteration: {j}/{num_iterations} ({j/num_iterations*100:.1f}%), Loss: {loss}')
                
                # 每2000次迭代生成示例昵称
                sample_nicknames = []
                if j % 2000 == 0:
                    print("\nSample nicknames:")
                    seed = 0
                    for name in range(dino_names):
                        sampled_indices = sample(self.parameters, self.char_to_ix, seed)
                        nickname = self.indices_to_nickname(sampled_indices)
                        sample_nicknames.append(nickname)
                        print(f"  {nickname}")
                        seed += 1
                    print()
                
                # 如果提供了回调函数，报告进度
                if callback:
                    callback(j, num_iterations, loss, sample_nicknames)
            
            # 每5000次迭代保存一次模型，防止训练中断丢失进度
            if j > 0 and j % 5000 == 0:
                self.save_model()
                print(f"模型已保存 (迭代 {j}/{num_iterations})")
        
        # 训练结束，保存最终模型
        self.save_model()
        print("训练完成，模型已保存")
        return self.parameters
    
    def indices_to_nickname(self, indices):
        """
        Convert a list of indices to a nickname string
        """
        nickname = ''.join(self.ix_to_char[ix] for ix in indices)
        # Clean up the nickname
        if nickname and nickname[0] == '的':
            nickname = nickname[1:]
        return nickname
    
    def generate_nicknames(self, num_nicknames=5, seed=None, max_length=10, min_length=2, exact_length=False):
        """
        生成指定数量和长度的昵称
        
        参数:
        num_nicknames -- 要生成的昵称数量
        seed -- 随机种子，用于生成可重复的结果
        max_length -- 生成昵称的长度
        min_length -- 生成昵称的最小长度
        exact_length -- 是否生成精确长度的昵称（如果为True，将直接截断到指定长度）
        
        返回:
        生成的昵称列表
        """
        if not self.parameters or not self.char_to_ix or not self.ix_to_char:
            raise ValueError("模型未加载。请先训练或加载模型。")
            
        if seed is None:
            seed = random.randint(0, 10000)
        
        nicknames = []
        current_seed = seed
        
        # 生成时使用更长的长度限制，以确保有足够的内容可供截断
        generation_length = max_length * 2 if exact_length else max_length
        
        # 计数器和最大尝试次数
        attempts = 0
        max_attempts = num_nicknames * 3  # 每个昵称最多尝试三次
        
        i = 0
        while len(nicknames) < num_nicknames and attempts < max_attempts:
            # 对每个昵称使用不同的种子
            current_seed = seed + i if seed is not None else random.randint(0, 10000)
            attempts += 1
            i += 1
            
            # 生成昵称
            sampled_indices = sample(
                self.parameters, 
                self.char_to_ix, 
                current_seed, 
                max_length=generation_length
            )
            
            nickname = ''.join([self.ix_to_char[i] for i in sampled_indices])
            
            # 如果昵称以'的'开头，则移除这个字
            if nickname.startswith('的'):
                nickname = nickname[1:]
            
            # 如果需要精确长度，直接截断昵称
            if exact_length and len(nickname) > max_length:
                nickname = nickname[:max_length]
            
            # 确保昵称长度至少为min_length
            if len(nickname) < min_length:
                # 如果昵称太短，重新生成
                continue
                
            nicknames.append(nickname)
            
        return nicknames

# Example usage
if __name__ == "__main__":
    generator = NicknameGenerator()
    
    # Check if model exists, if not train it
    if not generator.parameters:
        print("Training new model...")
        generator.train(num_iterations=10000)
    
    # Generate some nicknames
    nicknames = generator.generate_nicknames(10)
    print("\nGenerated Nicknames:")
    for i, nickname in enumerate(nicknames, 1):
        print(f"{i}. {nickname}")
