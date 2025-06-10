<template>
  <div class="following-list">
    <div class="list-header">
      <h3>我的关注</h3>
      <el-pagination
        v-if="totalPages > 1"
        small
        layout="prev, pager, next"
        :total="followData.following_count"
        :page-size="pageSize"
        v-model:current-page="currentPage"
        @current-change="handlePageChange"
      />
    </div>
    
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="3" animated />
    </div>
    
    <el-empty v-else-if="followData.following.length === 0" description="暂无关注的用户" />
    
    <div v-else class="follow-items">
      <div v-for="user in followData.following" :key="user.id" class="follow-item">
        <div class="user-info" @click="navigateToUserSpace(user.id)">
          <el-avatar :size="40" :src="user.avatar ? 'http://127.0.0.1:8000' + user.avatar : 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'" />
          <div class="user-details">
            <div class="username">{{ user.username }}</div>
            <div class="bio">{{ user.bio || '这个人很懒，还没有填写个人简介...' }}</div>
          </div>
        </div>
        <el-button 
          :type="user.is_following ? 'danger' : 'primary'" 
          size="small" 
          :plain="user.is_following"
          @click="user.is_following ? handleUnfollow(user.id) : handleFollow(user.id)"
          :loading="unfollowingId === user.id || followingId === user.id"
        >
          {{ user.is_following ? '取消关注' : '关注' }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import axios from 'axios';
import { useUserStore } from '../stores/user';

const props = defineProps({
  userId: {
    type: [String, Number],
    default: null
  }
});

const emit = defineEmits(['refresh-profile']);

const router = useRouter();
const userStore = useUserStore();

// 数据状态
const loading = ref(false);
const followData = reactive({
  followers: [],
  following: [],
  followers_count: 0,
  following_count: 0,
  page: 1,
  page_size: 10
});
const currentPage = ref(1);
const pageSize = ref(10);
const unfollowingId = ref(null);
const followingId = ref(null); // 正在关注的用户ID

// 计算总页数
const totalPages = computed(() => {
  return Math.ceil(followData.following_count / pageSize.value);
});

// 获取关注列表
const fetchFollowingList = async () => {
  try {
    loading.value = true;
    
    // 构建 API 路径
    let apiPath = '';
    if (props.userId) {
      // 获取指定用户的关注列表
      apiPath = `/api/follow/users/${props.userId}/following`;
    } else {
      // 获取当前用户的关注列表
      apiPath = '/api/follow/following';
    }
    
    // 添加分页参数
    apiPath += `?page=${currentPage.value}&page_size=${pageSize.value}`;
    
    // 发送请求
    const response = await axios.get(apiPath, {
      headers: userStore.isLoggedIn ? {
        Authorization: `Bearer ${userStore.token}`
      } : {}
    });
    
    // 更新数据
    Object.assign(followData, response.data);
    
    // 如果当前用户已登录，对每个用户获取关注状态
    if (userStore.isLoggedIn) {
      // 在关注列表中，我们需要检查每个用户的关注状态
      // 如果是当前用户的关注列表，则所有用户都是已关注状态
      if (!props.userId || props.userId === userStore.user?.id) {
        // 当前用户的关注列表，所有用户都是已关注状态
        followData.following.forEach(user => {
          user.is_following = true;
        });
      } else {
        // 其他用户的关注列表，需要检查当前用户是否关注了这些用户
        const checkPromises = followData.following.map(async (user) => {
          try {
            // 调用后端 API 检查关注状态
            const response = await axios.get(`/api/follow/check/${user.id}`, {
              headers: {
                Authorization: `Bearer ${userStore.token}`
              }
            });
            
            // 更新用户的关注状态
            if (response.data && response.data.is_following !== undefined) {
              user.is_following = response.data.is_following;
            } else {
              user.is_following = false; // 默认为未关注
            }
          } catch (error) {
            console.error(`检查用户 ${user.id} 的关注状态失败:`, error);
            user.is_following = false; // 出错时默认为未关注
          }
        });
        
        // 等待所有检查完成
        await Promise.all(checkPromises);
      }
    } else {
      // 未登录用户无法关注，所有用户都设置为未关注状态
      followData.following.forEach(user => {
        user.is_following = false;
      });
    }
  } catch (error) {
    console.error('获取关注列表失败:', error);
    ElMessage.error('获取关注列表失败');
  } finally {
    loading.value = false;
  }
};

// 处理关注用户
const handleFollow = async (userId) => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录');
    router.push('/login');
    return;
  }
  
  followingId.value = userId;
  try {
    // 发送关注请求
    await axios.post('/api/follow', {
      followed_id: userId
    }, {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    });
    
    ElMessage.success('关注成功');
    
    // 更新用户的关注状态
    const user = followData.following.find(u => u.id === userId);
    if (user) {
      user.is_following = true;
    }
    
    // 通知父组件刷新个人资料
    emit('refresh-profile');
    
    // 如果在用户空间页面，重新获取用户资料
    if (router.currentRoute.value.name === 'UserSpace' || router.currentRoute.value.path.includes('/user/')) {
      // 刷新当前页面以更新关注状态
      setTimeout(() => {
        window.location.reload();
      }, 500);
    }
  } catch (error) {
    console.error('关注失败:', error);
    ElMessage.error('关注失败');
  } finally {
    followingId.value = null;
  }
};

// 处理取消关注
const handleUnfollow = async (userId) => {
  try {
    unfollowingId.value = userId;
    
    // 确认取消关注
    await ElMessageBox.confirm(
      '确定要取消关注该用户吗？',
      '取消关注',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    // 发送取消关注请求
    await axios.delete(`/api/follow/${userId}`, {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    });
    
    ElMessage.success('已取消关注');
    
    // 更新用户的关注状态
    const user = followData.following.find(u => u.id === userId);
    if (user) {
      user.is_following = false;
    }
    
    // 从列表中移除该用户
    const index = followData.following.findIndex(user => user.id === userId);
    if (index !== -1) {
      followData.following.splice(index, 1);
      followData.following_count--;
    }
    
    // 通知父组件刷新个人资料
    emit('refresh-profile');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消关注失败:', error);
      ElMessage.error('取消关注失败');
    }
  } finally {
    unfollowingId.value = null;
  }
};

// 跳转到用户空间
const navigateToUserSpace = (userId) => {
  // 如果当前已经在用户空间路由，先强制刷新组件
  if (router.currentRoute.value.name === 'UserSpace') {
    // 先导航到一个临时路由，然后再导航到目标路由，强制组件重新渲染
    router.push('/').then(() => {
      router.push(`/user/${userId}/space`);
    });
  } else {
    // 直接导航到用户空间
    router.push(`/user/${userId}/space`);
  }
};

// 处理页码变化
const handlePageChange = (page) => {
  currentPage.value = page;
  fetchFollowingList();
};

// 检查关注状态
const checkFollowingStatus = async (userId) => {
  if (!userStore.isLoggedIn) return;
  
  try {
    // 调用后端 API 检查关注状态
    const response = await axios.get(`/api/follow/check/${userId}`, {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    });
    
    // 更新用户的关注状态
    const user = followData.following.find(u => u.id === userId);
    if (user && response.data && response.data.is_following !== undefined) {
      user.is_following = response.data.is_following;
    }
  } catch (error) {
    console.error(`检查用户 ${userId} 的关注状态失败:`, error);
  }
};

// 监听用户ID变化
watch(() => props.userId, () => {
  currentPage.value = 1;
  fetchFollowingList();
});

// 组件挂载时获取数据
onMounted(() => {
  fetchFollowingList();
});
</script>

<style scoped>
.following-list {
  margin-top: 20px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.list-header h3 {
  margin: 0;
  font-size: 16px;
}

.loading-container {
  padding: 10px;
}

.follow-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.follow-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-radius: 4px;
  background-color: #f5f7fa;
  transition: background-color 0.3s;
}

.follow-item:hover {
  background-color: #e6f1fc;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  cursor: pointer;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.username {
  font-weight: bold;
  color: #303133;
}

.bio {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}
</style>
