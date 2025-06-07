<script setup>
import { computed } from 'vue';
import { useUserStore } from './stores/user';
import { useRouter } from 'vue-router';
import HelloWorld from './components/HelloWorld.vue'

const userStore = useUserStore();
const router = useRouter();
const isLoggedIn = computed(() => userStore.isLoggedIn);

const logout = () => {
  userStore.logout();
  router.push('/login');
};
</script>

<template>
  <div class="app-container">
    <el-container>
      <el-header>
        <div class="header-container">
          <div class="logo" @click="router.push('/')">个人论坛</div>
          <div class="nav-links">
            <template v-if="isLoggedIn">
              <el-button type="text" @click="router.push('/myspace')">我的空间</el-button>
              <el-button type="text" @click="router.push('/profile')">个人资料</el-button>
              <el-button type="text" @click="logout">退出登录</el-button>
            </template>
            <template v-else>
              <el-button type="text" @click="router.push('/login')">登录</el-button>
              <el-button type="text" @click="router.push('/register')">注册</el-button>
            </template>
          </div>
        </div>
      </el-header>
      
      <el-main>
        <router-view />
      </el-main>
      
      <el-footer>
        <div class="footer-container">
          <p> 2025 洋葱论坛 - 使用 Vue + FastAPI 构建</p>
        </div>
      </el-footer>
    </el-container>
  </div>
</template>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#app {
  height: 100vh;
  width: 100vw;
}

.el-container {
  height: 100%;
  min-height: 100vh;
}

.el-header {
  background-color: #409eff;
  color: white;
  line-height: 60px;
  padding: 0 20px;
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0 auto;
}

.logo {
  font-size: 24px;
  font-weight: bold;
  cursor: pointer;
}

.nav-links {
  display: flex;
  gap: 15px;
}

.nav-links .el-button {
  color: white;
  font-size: 16px;
}

.el-main {
  flex:1;
  /* min-height: 0; */
}

.el-footer {
  text-align: center;
  background-color: #f5f7fa;
  color: #909399;
  padding: 20px;
  border-top: 1px solid #e4e7ed;
}

.footer-container {
  margin: 0 auto;
}


</style>
