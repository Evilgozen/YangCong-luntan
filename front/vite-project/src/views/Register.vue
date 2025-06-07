<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-image-container">
        <div class="register-image-content">
          <h2>成为我们社区的一员</h2>
          <p>注册账号，开始您的论坛之旅</p>
          <img src="https://img.freepik.com/free-vector/sign-concept-illustration_114360-125.jpg" alt="注册插图" class="register-image">
        </div>
      </div>
      
      <div class="register-form-container">
        <div class="register-header">
          <h1>创建新账户</h1>
          <p>填写以下信息完成注册</p>
        </div>
        
        <el-form :model="registerForm" :rules="rules" ref="registerFormRef" class="register-form">
          <el-form-item prop="username">
            <el-input 
              v-model="registerForm.username" 
              placeholder="用户名" 
              size="large"
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item prop="email">
            <el-input 
              v-model="registerForm.email" 
              placeholder="电子邮箱" 
              size="large"
            >
              <template #prefix>
                <el-icon><Message /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input 
              v-model="registerForm.password" 
              type="password" 
              placeholder="密码" 
              size="large"
              show-password
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item prop="confirmPassword">
            <el-input 
              v-model="registerForm.confirmPassword" 
              type="password" 
              placeholder="确认密码" 
              size="large"
              show-password
            >
              <template #prefix>
                <el-icon><CircleCheck /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <div class="terms-agreement">
            <el-checkbox v-model="agreeTerms">我已阅读并同意<el-link type="primary">服务条款</el-link>和<el-link type="primary">隐私政策</el-link></el-checkbox>
          </div>
          
          <el-form-item>
            <el-button 
              type="primary" 
              @click="handleRegister" 
              :loading="loading" 
              class="register-button"
              size="large"
              :disabled="!agreeTerms"
            >
              注册
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="login-link">
          已有账号? <el-link type="primary" @click="$router.push('/login')">立即登录</el-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useUserStore } from '../stores/user';
import { User, Message, Lock, CircleCheck } from '@element-plus/icons-vue';

const router = useRouter();
const userStore = useUserStore();
const registerFormRef = ref(null);
const loading = ref(false);
const agreeTerms = ref(false);

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
});

const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'));
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致'));
  } else {
    callback();
  }
};

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应为3-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度应为6-20个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validatePass, trigger: 'blur' }
  ]
};

const handleRegister = async () => {
  if (!registerFormRef.value) return;
  
  if (!agreeTerms.value) {
    ElMessage.warning('请阅读并同意服务条款和隐私政策');
    return;
  }
  
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        await userStore.register({
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password
        });
        ElMessage.success('注册成功，请登录');
        router.push('/login');
      } catch (error) {
        ElMessage.error(error.message || '注册失败，请稍后再试');
      } finally {
        loading.value = false;
      }
    }
  });
};
</script>

<style scoped>
.register-page {
  min-height: calc(100vh - 120px);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
}

.register-container {
  display: flex;
  max-width: 1000px;
  width: 100%;
  min-height: 600px;
  background-color: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.register-form-container {
  flex: 1;
  padding: 40px;
  display: flex;
  flex-direction: column;
}

.register-header {
  margin-bottom: 40px;
  text-align: center;
}

.register-header h1 {
  font-size: 28px;
  color: #303133;
  margin-bottom: 10px;
}

.register-header p {
  color: #909399;
  font-size: 16px;
}

.register-form {
  margin-bottom: 20px;
}

.register-button {
  width: 100%;
  height: 50px;
  font-size: 16px;
  border-radius: 8px;
  margin-top: 10px;
}

.terms-agreement {
  margin-bottom: 20px;
  color: #606266;
}

.login-link {
  text-align: center;
  margin-top: auto;
  padding-top: 20px;
  color: #606266;
}

.register-image-container {
  flex: 1;
  background: linear-gradient(135deg, #67c23a, #2e9e4b);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.register-image-content {
  text-align: center;
}

.register-image-content h2 {
  font-size: 28px;
  margin-bottom: 20px;
}

.register-image-content p {
  font-size: 16px;
  margin-bottom: 40px;
  opacity: 0.9;
}

.register-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .register-container {
    flex-direction: column-reverse;
  }
  
  .register-image-container {
    display: none;
  }
}
</style>
