<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-form-container">
        <div class="login-header">
          <h1>欢迎回来</h1>
          <p>登录您的账户以继续访问论坛</p>
        </div>
        
        <el-form :model="loginForm" :rules="rules" ref="loginFormRef" class="login-form">
          <el-form-item prop="username">
            <el-input 
              v-model="loginForm.username" 
              placeholder="用户名" 
              prefix-icon="el-icon-user"
              size="large"
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input 
              v-model="loginForm.password" 
              type="password" 
              placeholder="密码"
              prefix-icon="el-icon-lock" 
              size="large"
              show-password
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              @click="handleLogin" 
              :loading="loading" 
              class="login-button"
              size="large"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="login-divider">
          <span>或者</span>
        </div>
        
        <div class="register-link">
          还没有账号? <el-link type="primary" @click="$router.push('/register')">立即注册</el-link>
        </div>
      </div>
      
      <div class="login-image-container">
        <div class="login-image-content">
          <h2>加入我们的社区</h2>
          <p>探索无限可能，分享您的想法，结交志同道合的朋友</p>
          <img src="https://img.freepik.com/free-vector/mobile-login-concept-illustration_114360-83.jpg" alt="登录插图" class="login-image">
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
import { User, Lock } from '@element-plus/icons-vue';

const router = useRouter();
const userStore = useUserStore();
const loginFormRef = ref(null);
const loading = ref(false);
const rememberMe = ref(false);

const loginForm = reactive({
  username: '',
  password: ''
});

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应为3-20个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度应为6-20个字符', trigger: 'blur' }
  ]
};

//对于这里，使用的是element-plus封装的validate，成功后异步调用pinia的action的login进行登录,然后报错用Message返回
const handleLogin = async () => {
  if (!loginFormRef.value) return;
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        await userStore.login(loginForm);
        ElMessage.success('登录成功');
        router.push('/');
      } catch (error) {
        ElMessage.error(error.message || '登录失败，请检查用户名和密码');
      } finally {
        loading.value = false;
      }
    }
  });
};
</script>

<style scoped>
.login-page {
  min-height: calc(100vh - 120px);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
}

.login-container {
  display: flex;
  max-width: 1000px;
  width: 100%;
  min-height: 600px;
  background-color: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.login-form-container {
  flex: 1;
  padding: 40px;
  display: flex;
  flex-direction: column;
}

.login-header {
  margin-bottom: 40px;
  text-align: center;
}

.login-header h1 {
  font-size: 28px;
  color: #303133;
  margin-bottom: 10px;
}

.login-header p {
  color: #909399;
  font-size: 16px;
}

.login-form {
  margin-bottom: 20px;
}

.login-button {
  width: 100%;
  height: 50px;
  font-size: 16px;
  border-radius: 8px;
  margin-top: 10px;
}

.remember-forgot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.login-divider {
  position: relative;
  text-align: center;
  margin: 20px 0;
}

.login-divider::before,
.login-divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 40%;
  height: 1px;
  background-color: #dcdfe6;
}

.login-divider::before {
  left: 0;
}

.login-divider::after {
  right: 0;
}

.login-divider span {
  display: inline-block;
  padding: 0 10px;
  background-color: #ffffff;
  color: #909399;
  position: relative;
  z-index: 1;
}

.social-login {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 30px;
}

.social-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.register-link {
  text-align: center;
  margin-top: auto;
  padding-top: 20px;
  color: #606266;
}

.login-image-container {
  flex: 1;
  background: linear-gradient(135deg, #409eff, #3367d6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.login-image-content {
  text-align: center;
}

.login-image-content h2 {
  font-size: 28px;
  margin-bottom: 20px;
}

.login-image-content p {
  font-size: 16px;
  margin-bottom: 40px;
  opacity: 0.9;
}

.login-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
  }
  
  .login-image-container {
    display: none;
  }
}
</style>
