<template>
  <div class="nickname-generator">
    <el-card class="generator-card">
      <template #header>
        <div class="card-header">
          <h3>沙雕网名生成器</h3>
          <div class="subtitle">由RNN人工智能模型生成的有趣网名</div>
          <div v-if="modelStatus.trained" class="model-status trained">
            <el-tag type="success" size="small">模型已加载</el-tag>
          </div>
          <div v-else-if="modelStatus.training" class="model-status training">
            <el-tag type="warning" size="small">模型训练中 ({{modelStatus.progress}}%)</el-tag>
          </div>
          <div v-else class="model-status untrained">
            <el-tag type="info" size="small">模型未训练</el-tag>
          </div>
        </div>
      </template>
      
      <div class="generator-content">
        <div v-if="loading" class="loading-container">
          <el-skeleton :rows="3" animated />
        </div>
        
        <div v-else-if="modelStatus.training" class="training-container">
          <el-alert
            title="模型正在训练中"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>RNN模型正在训练中，请稍等片刻。训练完成后将自动可用。</p>
              <el-progress 
                :percentage="modelStatus.progress" 
                :format="percentageFormat" 
                status="warning" 
                :stroke-width="15"
              />
              <div v-if="modelStatus.sample_nicknames && modelStatus.sample_nicknames.length > 0" class="sample-nicknames">
                <p class="sample-title">训练过程中生成的示例:</p>
                <div class="sample-list">
                  <div v-for="(nickname, idx) in modelStatus.sample_nicknames" :key="idx" class="sample-item">
                    {{nickname}}
                  </div>
                </div>
              </div>
            </template>
          </el-alert>
        </div>
        
        <div v-else>
          <div class="nickname-list">
            <div v-if="nicknames.length === 0" class="empty-state">
              点击生成按钮获取沙雕网名
            </div>
            <transition-group name="nickname-list" tag="div">
              <div 
                v-for="(nickname, index) in nicknames" 
                :key="index" 
                class="nickname-item"
                @click="copyNickname(nickname)"
              >
                <div class="nickname-text">{{ nickname }}</div>
                <el-tooltip content="点击复制" placement="top" :show-after="300">
                  <el-icon class="copy-icon"><DocumentCopy /></el-icon>
                </el-tooltip>
              </div>
            </transition-group>
          </div>
          
          <div class="actions">
            <el-button 
              type="primary" 
              @click="generateNicknames" 
              :loading="loading"
              :disabled="modelStatus === 'training'"
            >
              {{ buttonText }}
            </el-button>
            
            <el-tooltip content="随机种子可以生成不同的结果" placement="top">
              <el-input-number 
                v-model="seed" 
                :min="1" 
                :max="9999" 
                placeholder="随机种子" 
                class="seed-input"
              />
            </el-tooltip>
            
            <el-tooltip content="生成的网名数量" placement="top">
              <el-select v-model="count" placeholder="数量" class="count-select">
                <el-option v-for="n in 10" :key="n" :label="`${n}个`" :value="n" />
              </el-select>
            </el-tooltip>
            
            <el-tooltip content="控制生成网名的长度" placement="top">
              <div class="length-control">
                <span class="length-label">长度: {{maxLength}}</span>
                <el-slider v-model="maxLength" :min="2" :max="20" :step="1" class="length-slider" />
              </div>
            </el-tooltip>
            
            <el-tooltip content="开启后将生成精确长度的网名" placement="top">
              <div class="exact-length-control">
                <el-checkbox v-model="exactLength" label="精确长度" />
              </div>
            </el-tooltip>
          </div>
          
          <div v-if="modelStatus.training" class="training-notice">
            <el-alert
              title="模型正在训练中"
              type="info"
              :closable="false"
              show-icon
            >
              <template #default>
                <p>训练进度: {{modelStatus.progress}}%</p>
                <el-progress :percentage="modelStatus.progress" :format="percentageFormat" />
              </template>
            </el-alert>
          </div>
          
          <div v-if="error" class="error-message">
            <el-alert
              :title="error"
              type="error"
              :closable="true"
              @close="error = ''"
              show-icon
            />
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { DocumentCopy } from '@element-plus/icons-vue';
import axios from 'axios';

// 状态变量
const nicknames = ref([]);
const loading = ref(false);
const error = ref('');
const seed = ref(Math.floor(Math.random() * 9000) + 1000); // 随机种子
const count = ref(5); // 生成数量
const maxLength = ref(10); // 昵称长度
const exactLength = ref(false); // 是否生成精确长度的昵称
const modelStatus = ref({
  trained: false,
  training: false,
  progress: 0,
  sample_nicknames: [],
  last_trained: null,
  current_loss: null
});

// 计算属性
const buttonText = computed(() => {
  if (modelStatus.value.training) return '模型训练中...';
  return nicknames.value.length > 0 ? '再来一批' : '生成网名';
});

// 格式化进度百分比
const percentageFormat = (percentage) => {
  return percentage === 100 ? '完成' : `${percentage}%`;
};

// 生成网名
const generateNicknames = async () => {
  if (loading.value) return;
  
  loading.value = true;
  error.value = '';
  
  try {
    // 先检查模型状态
    await checkModelStatus();
    
    if (modelStatus.value.training) {
      error.value = '模型正在训练中，请稍后再试';
      loading.value = false;
      return;
    }
    
    // 如果模型未训练，尝试启动训练
    if (!modelStatus.value.trained) {
      await trainModel();
      error.value = '模型正在训练中，首次使用需要等待几分钟';
      loading.value = false;
      return;
    }
    
    // 生成网名
    const response = await axios.get('/api/nickname/generate', {
      params: {
        count: count.value,
        seed: seed.value,
        max_length: maxLength.value,
        exact_length: exactLength.value
      }
    });
    
    nicknames.value = response.data;
    
    // 更新随机种子，以便下次生成不同的结果
    seed.value = Math.floor(Math.random() * 9000) + 1000;
    
  } catch (err) {
    console.error('生成网名失败:', err);
    if (err.response && err.response.status === 503) {
      error.value = '模型未训练，正在启动训练...';
      trainModel();
    } else {
      error.value = `生成失败: ${err.response?.data?.detail || err.message}`;
    }
  } finally {
    loading.value = false;
  }
};

// 检查模型状态
const checkModelStatus = async () => {
  try {
    const response = await axios.get('/api/nickname/status');
    // 更新整个模型状态对象
    modelStatus.value = response.data;
    return response.data;
  } catch (err) {
    console.error('检查模型状态失败:', err);
    modelStatus.value = {
      trained: false,
      training: false,
      progress: 0
    };
    throw err;
  }
};

// 定期检查模型状态
const startStatusPolling = () => {
  // 如果模型正在训练中，每3秒检查一次状态
  if (modelStatus.value.training) {
    setTimeout(async () => {
      await checkModelStatus();
      startStatusPolling();
    }, 3000);
  } else {
    // 如果模型不在训练中，每30秒检查一次状态
    setTimeout(async () => {
      await checkModelStatus();
      startStatusPolling();
    }, 30000);
  }
};

// 训练模型
const trainModel = async () => {
  try {
    await axios.post('/api/nickname/train');
    modelStatus.value = 'training';
  } catch (err) {
    console.error('启动模型训练失败:', err);
    error.value = `启动训练失败: ${err.response?.data?.detail || err.message}`;
  }
};

// 复制网名到剪贴板
const copyNickname = (nickname) => {
  navigator.clipboard.writeText(nickname)
    .then(() => {
      ElMessage.success('已复制到剪贴板');
    })
    .catch(err => {
      console.error('复制失败:', err);
      ElMessage.error('复制失败');
    });
};

// 组件挂载时检查模型状态
onMounted(async () => {
  try {
    await checkModelStatus();
    // 启动状态轮询
    startStatusPolling();
  } catch (err) {
    console.error('初始化失败:', err);
  }
});
</script>

<style scoped>
.nickname-generator {
  max-width: 600px;
  margin: 0 auto;
}

.generator-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  flex-direction: column;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
}

.subtitle {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.model-status {
  margin-top: 10px;
  display: flex;
  justify-content: center;
}

.training-container {
  margin-bottom: 20px;
}

.sample-nicknames {
  margin-top: 15px;
}

.sample-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
}

.sample-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.sample-item {
  background-color: #f0f9eb;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
}

.generator-content {
  min-height: 200px;
}

.loading-container {
  padding: 20px 0;
}

.nickname-list {
  margin-bottom: 20px;
  min-height: 150px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 150px;
  color: #909399;
  font-size: 14px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.nickname-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  margin-bottom: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  transition: all 0.3s;
  cursor: pointer;
}

.nickname-item:hover {
  background-color: #e6f1fc;
  transform: translateY(-2px);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.nickname-text {
  font-size: 16px;
  font-weight: 500;
}

.copy-icon {
  color: #909399;
  font-size: 16px;
}

.nickname-item:hover .copy-icon {
  color: #409EFF;
}

.actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
}

.seed-input {
  width: 120px;
}

.count-select {
  width: 80px;
}

.length-control {
  display: flex;
  flex-direction: column;
  width: 150px;
}

.length-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 5px;
}

.length-slider {
  width: 100%;
}

.training-notice {
  margin-top: 20px;
}

.error-message {
  margin-top: 20px;
}

/* 动画效果 */
.nickname-list-enter-active,
.nickname-list-leave-active {
  transition: all 0.5s ease;
}

.nickname-list-enter-from,
.nickname-list-leave-to {
  opacity: 0;
  transform: translateY(30px);
}
</style>
