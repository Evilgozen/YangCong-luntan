<template>
  <div class="home">
    <!-- 未登录用户显示欢迎卡片 -->
    <el-card class="welcome-card" v-if="!isLoggedIn">
      <div class="welcome-text">
        <h1>欢迎来到洋葱个人论坛</h1>
      </div>
      <p>这是一个使用Vue + Element Plus + Pinia构建的前端和FastAPI + SQLite构建的后端的个人论坛项目。</p>
      <div class="action-buttons">
        <el-button type="primary" @click="$router.push('/login')" size="large">登录</el-button>
        <el-button type="success" @click="$router.push('/register')" size="large">注册</el-button>
      </div>
    </el-card>

    <!-- 已登录用户显示帖子列表和搜索 -->
    <div class="posts-container" v-else>
      <div class="search-container">
        <el-input
          v-model="searchQuery"
          placeholder="搜索帖子..."
          clearable
          @keyup.enter="handleSearch"
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
          <template #append>
            <el-button @click="handleSearch">搜索</el-button>
          </template>
        </el-input>
        <el-button type="primary" @click="createPost" class="create-post-btn">
          <el-icon><Plus /></el-icon> 发布新帖子
        </el-button>
      </div>

      <!-- 帖子列表 -->
      <div class="posts-list">
        <el-empty description="暂无帖子" v-if="!loading && !postStore.hasPosts" />
        
        <el-skeleton :rows="3" animated v-if="loading" v-for="i in 5" :key="i" />
        
        <el-card v-for="post in postStore.posts" :key="post.id" class="post-card" v-else>
          <div class="post-header">
            <h3 class="post-title" @click="viewPostDetail(post.id)">
              {{ post.title }}
              <el-tag size="small" type="success" v-if="post.is_pinned">置顶</el-tag>
              <el-tag size="small" type="info" v-if="post.is_closed">已关闭</el-tag>
            </h3>
            <div class="post-meta">
              <span class="author">
                <el-avatar :size="24" :src="`${API_URL}${post.author.avatar}`"></el-avatar>
                {{ post.author.username }}
              </span>
              <span class="time">{{ formatDate(post.created_at) }}</span>
              <!-- 在post-meta部分添加，大约在第56行的views后面 -->
              <span class="views"><el-icon><View /></el-icon> {{ post.view_count }}</span>
              <span class="likes" @click="toggleLike(post, $event)">
                <el-icon :class="{ 'liked': post.is_liked }">
                  <Star />
                </el-icon>
                {{ post.like_count || 0 }}
              </span>
            </div>
          </div>
          <p class="post-content">{{ truncateContent(post.content) }}</p>
          <div class="post-tags" v-if="post.tags">
            <el-tag 
              v-for="tag in parseTags(post.tags)" 
              :key="tag" 
              size="small" 
              effect="plain"
              @click="searchByTag(tag)"
            >
              {{ tag }}
            </el-tag>
          </div>
        </el-card>
        
        <!-- 分页 -->
        <div class="pagination-container" v-if="postStore.totalPosts > 0">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[5, 10, 20, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="postStore.totalPosts"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useUserStore } from '../stores/user';
import { usePostStore } from '../stores/post';
import { useRouter, useRoute } from 'vue-router';
import { Search, View, Plus, Star } from '@element-plus/icons-vue';
import { useLikeStore } from '../stores/like';
import { ElMessage } from 'element-plus';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const postStore = usePostStore();
const isLoggedIn = computed(() => userStore.isLoggedIn);

// 搜索和分页状态
const searchQuery = ref('');
const currentPage = ref(1);
const pageSize = ref(10);
const loading = ref(false);
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';
const API_URL = 'http://localhost:8000';

// 在组件挂载时获取帖子（如果已登录）
onMounted(async () => {
  if (isLoggedIn.value) {
    // 检查URL中是否有搜索参数
    if (route.query.search) {
      searchQuery.value = route.query.search;
      await handleSearch();
    } else {
      await fetchPosts();
    }
  }
});

// 监听登录状态变化，登录后自动获取帖子
watch(isLoggedIn, async (newValue) => {
  if (newValue) {
    await fetchPosts();
  } else {
    postStore.clearPosts();
  }
});

watch(
  () => postStore.posts[0]?.author?.avatar, // 使用可选链防止 author 为 undefined
  (newAvatar, oldAvatar) => {
    console.log(`${API_URL}${newAvatar}`);
  },
  { deep: true } // 如果需要深度监听对象内部变化
);

// 获取帖子
async function fetchPosts() {
  loading.value = true;
  try {
    await postStore.fetchPosts(currentPage.value, pageSize.value);
    // 获取每个帖子的点赞状态
    if (postStore.posts.length > 0) {
      await updatePostsLikeStatus();
    }
  } catch (error) {
    ElMessage.error('获取帖子失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
}

// 搜索帖子
async function handleSearch() {
  loading.value = true;
  currentPage.value = 1; // 重置到第一页
  try {
    await postStore.searchPosts(searchQuery.value, currentPage.value, pageSize.value);
    // 获取每个帖子的点赞状态
    if (postStore.posts.length > 0) {
      await updatePostsLikeStatus();
    }
  } catch (error) {
    ElMessage.error('搜索失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
}

// 按标签搜索
function searchByTag(tag) {
  searchQuery.value = tag;
  handleSearch();
}

// 分页处理
function handleSizeChange(val) {
  pageSize.value = val;
  fetchPostsWithCurrentSearch();
}

function handleCurrentChange(val) {
  currentPage.value = val;
  fetchPostsWithCurrentSearch();
}

// 根据当前搜索条件获取帖子
async function fetchPostsWithCurrentSearch() {
  loading.value = true;
  try {
    if (searchQuery.value) {
      await postStore.searchPosts(searchQuery.value, currentPage.value, pageSize.value);
    } else {
      await postStore.fetchPosts(currentPage.value, pageSize.value);
    }
    // 获取每个帖子的点赞状态
    if (postStore.posts.length > 0) {
      await updatePostsLikeStatus();
    }
  } catch (error) {
    ElMessage.error('获取帖子失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
}

// 查看帖子详情
function viewPostDetail(postId) {
  router.push(`/posts/${postId}`);
}

// 创建新帖子
function createPost() {
  router.push('/posts/create');
}

// 格式化日期
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// 截断内容
function truncateContent(content) {
  if (content.length > 100) {
    return content.substring(0, 100) + '...';
  }
  return content;
}

// 解析标签
function parseTags(tags) {
  if (!tags) return [];
  return tags.split(',').map(tag => tag.trim()).filter(tag => tag);
}

// 在setup部分添加
const likeStore = useLikeStore();

// 更新所有帖子的点赞状态
async function updatePostsLikeStatus() {
  try {
    for (const post of postStore.posts) {
      const likeStatus = await likeStore.getPostLikeStatus(post.id);
      post.is_liked = likeStatus.is_liked;
      post.like_count = likeStatus.like_count;
    }
  } catch (error) {
    console.error('获取点赞状态失败', error);
  }
}

// 添加点赞/取消点赞方法
async function toggleLike(post, event) {
  // 阻止事件冒泡，避免点击点赞按钮时触发帖子详情跳转
  event.stopPropagation();
  
  try {
    if (post.is_liked) {
      await likeStore.unlikePost(post.id);
      post.is_liked = false;
      post.like_count--;
    } else {
      await likeStore.likePost(post.id);
      post.is_liked = true;
      post.like_count++;
    }
  } catch (err) {
    ElMessage.error(err.message || '操作失败');
  }
}
</script>

<style scoped>
.welcome-text {
  margin-bottom: 20px;
}
.home {
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 20px;
  min-height: 80vh;
  box-sizing: border-box; /* 确保padding不会增加元素总宽度 */
}

.welcome-card {
  max-width: 600px;
  width: 100%;
  text-align: center;
  display: flex;
  justify-self: center;
  align-items: center;
}

.action-buttons {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 10px;
}

.posts-container {
  width: 100%;
  max-width: 1200px; /* 增加最大宽度，让内容在大屏幕上更舒适 */
}

.search-container {
  display: flex;
  margin-bottom: 20px;
  gap: 10px;
}

.search-input {
  flex: 1;
}

.create-post-btn {
  white-space: nowrap;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  width: 100%;
}

.post-card {
  cursor: pointer;
  transition: all 0.3s;
  width: 100%;
  margin-bottom: 15px;
}

.post-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.post-header {
  display: flex;
  flex-direction: column;
  margin-bottom: 10px;
  width: 100%;
}

.post-title {
  margin: 0 0 10px 0;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 15px;
  font-size: 0.85rem;
  color: #909399;
  flex-wrap: wrap; /* 在小屏幕上允许换行 */
}

.author {
  display: flex;
  align-items: center;
  gap: 5px;
}

.post-content {
  color: #606266;
  margin-bottom: 10px;
  line-height: 1.5;
  width: 100%;
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  width: 100%;
}
/* 在<style>部分添加 */
.likes {
  margin-left: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.likes .el-icon {
  font-size: 16px;
  transition: all 0.3s;
}

.likes .liked {
  color: #e6a23c;
  transform: scale(1.2);
}
</style>
