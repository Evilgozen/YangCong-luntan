<template>
  <div class="post-detail-container">
    <el-page-header @back="goBack" :title="'返回'" />
    
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>
    
    <div v-else-if="error" class="error-container">
      <el-result
        icon="error"
        title="加载失败"
        :sub-title="error"
      >
        <template #extra>
          <el-button type="primary" @click="fetchPostDetail">重试</el-button>
        </template>
      </el-result>
    </div>
    
    <template v-else-if="post">
      <div class="post-header">
        <h1 class="post-title">
          {{ post.title }}
          <el-tag v-if="post.is_pinned" type="success" size="small">置顶</el-tag>
          <el-tag v-if="post.is_closed" type="info" size="small">已关闭</el-tag>
        </h1>
        
        <div class="post-meta">
          <span class="author" @click="navigateToUserSpace(post.author_id)">
            <el-avatar :size="32" :src="getAvatarUrl(post.author?.avatar)"></el-avatar>
            {{ post.author?.username }}
          </span>
          <span class="time">发布于: {{ formatDate(post.created_at) }}</span>
          <span class="views"><el-icon><View /></el-icon> {{ post.view_count }}</span>
        </div>
        
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
      </div>
      
      <div class="post-content">
        {{ post.content }}
      </div>
      
      <div class="post-actions" v-if="canEdit">
        <el-button type="primary" @click="editPost" :icon="Edit">编辑</el-button>
        <el-popconfirm
          title="确定要删除这个帖子吗？"
          @confirm="deletePost"
          confirm-button-text="确定"
          cancel-button-text="取消"
        >
          <template #reference>
            <el-button type="danger" :icon="Delete">删除</el-button>
          </template>
        </el-popconfirm>
      </div>
      
      <!-- 楼层列表 -->
      <div class="floors-section">
        <h2 class="section-title">全部回复 ({{ floors.length }})</h2>
        
        <div v-if="floorLoading" class="loading-container">
          <el-skeleton :rows="5" animated />
        </div>
        
        <div v-else-if="floorError" class="error-container">
          <el-alert
            :title="floorError"
            type="error"
            show-icon
            @close="floorError = null"
          />
          <el-button class="mt-3" type="primary" @click="fetchFloors">重试</el-button>
        </div>
        
        <div v-else-if="floors.length === 0" class="empty-floors">
          <el-empty description="暂无回复，来发表第一条回复吧！" />
        </div>
        
        <div v-else class="floor-list">
          <div v-for="floor in floors" :key="floor.id" class="floor-item" :id="`floor-${floor.id}`">
            <div class="floor-header">
              <div class="floor-author" @click="navigateToUserSpace(floor.author_id)">
                <el-avatar :size="32" :src="getAvatarUrl(floor.author?.avatar)"></el-avatar>
                <span class="author-name">{{ floor.author?.username }}</span>
              </div>
              <div class="floor-meta">
                <span class="floor-number">#{{ floor.floor_number }}</span>
                <span class="floor-time">{{ formatDate(floor.created_at) }}</span>
              </div>
            </div>
            
            <div class="floor-content">
              <!-- 如果是回复其他楼层 -->
              <div v-if="floor.reply_to_floor_id" class="reply-reference">
                <el-tag size="small" type="info">
                  回复 #{{ getFloorNumber(floor.reply_to_floor_id) }}
                </el-tag>
              </div>
              
              <div class="content-text">{{ floor.content }}</div>
            </div>
            
            <div class="floor-actions">
              <el-button 
                type="primary" 
                size="small" 
                text 
                @click="replyToFloor(floor)"
                :disabled="post.is_closed"
              >
                回复
              </el-button>
              
              <template v-if="canEditFloor(floor)">
                <el-button 
                  type="primary" 
                  size="small" 
                  text 
                  @click="editFloor(floor)"
                >
                  编辑
                </el-button>
                
                <el-popconfirm
                  title="确定要删除这条回复吗？"
                  @confirm="deleteFloor(floor.id)"
                  confirm-button-text="确定"
                  cancel-button-text="取消"
                >
                  <template #reference>
                    <el-button type="danger" size="small" text>删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 回复编辑器 -->
      <div class="reply-editor" v-if="!post.is_closed">
        <h3 class="reply-title">
          {{ floorStore.replyingTo ? `回复 #${floorStore.replyingTo.floor_number}` : '发表回复' }}
          <el-button 
            v-if="floorStore.replyingTo" 
            type="info" 
            size="small" 
            text 
            @click="floorStore.clearReplyTarget()"
          >
            取消回复
          </el-button>
        </h3>
        
        <el-form @submit.prevent="submitReply">
          <el-form-item>
            <el-input
              v-model="replyContent"
              type="textarea"
              :rows="4"
              placeholder="请输入回复内容..."
              :disabled="floorSubmitting"
            />
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              @click="submitReply" 
              :loading="floorSubmitting"
              :disabled="!replyContent.trim()"
            >
              发表回复
            </el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <el-alert
        v-else
        title="该帖子已关闭，无法回复"
        type="info"
        :closable="false"
        show-icon
      />
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { usePostStore } from '../stores/post';
import { useUserStore } from '../stores/user';
import { useFloorStore } from '../stores/floor';
import { ElMessage } from 'element-plus';
import { Edit, Delete, View } from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();
const postStore = usePostStore();
const userStore = useUserStore();
const floorStore = useFloorStore();

const loading = ref(true);
const error = ref(null);
const floorLoading = ref(false);
const floorError = ref(null);
const floorSubmitting = ref(false);
const replyContent = ref('');
const editingFloorId = ref(null);
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';
const API_URL = 'http://localhost:8000';

const post = computed(() => postStore.currentPost);
const floors = computed(() => floorStore.floors);
const canEdit = computed(() => {
  if (!post.value || !userStore.user) return false;
  return post.value.author_id === userStore.user.id || userStore.user.is_admin;
});

onMounted(async () => {
  await fetchPostDetail();
  if (post.value) {
    await fetchFloors();
  }
});

async function fetchPostDetail() {
  const postId = parseInt(route.params.id);
  if (isNaN(postId)) {
    error.value = '无效的帖子ID';
    loading.value = false;
    return;
  }
  
  loading.value = true;
  error.value = null;
  
  try {
    await postStore.getPostById(postId);
  } catch (err) {
    error.value = err.message || '获取帖子详情失败';
    console.error(err);
  } finally {
    loading.value = false;
  }
}

function goBack() {
  router.back();
}

function searchByTag(tag) {
  router.push({
    path: '/',
    query: { search: tag }
  });
}

function editPost() {
  router.push(`/posts/edit/${post.value.id}`);
}

async function deletePost() {
  try {
    await postStore.deletePost(post.value.id);
    ElMessage.success('帖子已删除');
    router.push('/');
  } catch (err) {
    ElMessage.error(err.message || '删除帖子失败');
    console.error(err);
  }
}

// 格式化日期
function formatDate(dateString) {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    return date.toLocaleTimeString();
  }
  
  return date.toLocaleDateString();
}

// 处理头像URL
function getAvatarUrl(avatarPath) {
  if (!avatarPath) return defaultAvatar;
  
  // 如果已经是完整URL，直接返回
  if (avatarPath.startsWith('http')) {
    return avatarPath;
  }
  
  // 否则拼接后端服务器地址
  return `${API_URL}${avatarPath}`;
}

// 导航到用户空间
function navigateToUserSpace(userId) {
  if (!userId) return;
  
  // 如果是当前用户，导航到我的空间
  if (userStore.user && userId === userStore.user.id) {
    router.push('/myspace');
  } else {
    // 否则导航到该用户的空间
    router.push(`/user/${userId}/space`);
  }
}

// 解析标签
function parseTags(tags) {
  if (!tags) return [];
  return tags.split(',').map(tag => tag.trim()).filter(tag => tag);
}

// 获取楼层列表
async function fetchFloors() {
  if (!post.value) return;
  
  floorLoading.value = true;
  floorError.value = null;
  
  try {
    await floorStore.getFloorsByPostId(post.value.id);
  } catch (err) {
    floorError.value = err.message || '获取回复列表失败';
    console.error(err);
  } finally {
    floorLoading.value = false;
  }
}

// 根据楼层ID获取楼层号
function getFloorNumber(floorId) {
  const floor = floors.value.find(f => f.id === floorId);
  return floor ? floor.floor_number : '?';
}

// 回复楼层
function replyToFloor(floor) {
  floorStore.setReplyTarget(floor);
  // 滚动到回复框
  nextTick(() => {
    document.querySelector('.reply-editor').scrollIntoView({ behavior: 'smooth' });
  });
}

// 提交回复
async function submitReply() {
  if (!replyContent.value.trim()) return;
  
  floorSubmitting.value = true;
  
  try {
    if (editingFloorId.value) {
      // 更新楼层
      await floorStore.updateFloor(editingFloorId.value, replyContent.value);
      editingFloorId.value = null;
      ElMessage.success('回复更新成功');
    } else {
      // 创建新楼层
      const floorData = {
        content: replyContent.value,
        post_id: post.value.id,
        reply_to_floor_id: floorStore.replyingTo ? floorStore.replyingTo.id : null
      };
      await floorStore.createFloor(floorData);
      ElMessage.success('回复发表成功');
    }
    replyContent.value = '';
    floorStore.clearReplyTarget();
  } catch (err) {
    ElMessage.error(err.message || '操作失败');
    console.error(err);
  } finally {
    floorSubmitting.value = false;
  }
}

// 编辑楼层
function editFloor(floor) {
  replyContent.value = floor.content;
  editingFloorId.value = floor.id;
  
  // 滚动到回复框
  nextTick(() => {
    document.querySelector('.reply-editor').scrollIntoView({ behavior: 'smooth' });
  });
}

// 删除楼层
async function deleteFloor(floorId) {
  try {
    await floorStore.deleteFloor(floorId);
    ElMessage.success('回复已删除');
  } catch (err) {
    ElMessage.error(err.message || '删除回复失败');
    console.error(err);
  }
}

// 判断是否可以编辑楼层
function canEditFloor(floor) {
  if (!userStore.user) return false;
  return floor.author_id === userStore.user.id || userStore.user.is_admin;
}
</script>

<style scoped>
.post-detail-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.loading-container, .error-container {
  margin-top: 40px;
}

.post-header {
  margin-top: 30px;
  margin-bottom: 20px;
}

.post-title {
  font-size: 24px;
  margin-bottom: 15px;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
  color: #606266;
  font-size: 14px;
}

.author {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.author:hover {
  background-color: #f0f9ff;
}

.post-tags {
  margin-bottom: 20px;
}

.post-tags .el-tag {
  margin-right: 8px;
  cursor: pointer;
}

.post-content {
  font-size: 16px;
  line-height: 1.6;
  white-space: pre-wrap;
  margin-bottom: 30px;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.post-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
}

/* 楼层样式 */
.floors-section {
  margin-top: 40px;
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
}

.section-title {
  font-size: 18px;
  margin-bottom: 20px;
  font-weight: 600;
}

.floor-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.floor-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 15px;
  background-color: #fff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.floor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.floor-author {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.floor-author:hover {
  background-color: #f0f9ff;
}

.author-name {
  font-weight: 500;
}

.floor-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #909399;
  font-size: 14px;
}

.floor-content {
  margin-bottom: 15px;
  white-space: pre-wrap;
}

.reply-reference {
  margin-bottom: 10px;
}

.floor-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.reply-editor {
  margin-top: 30px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
  background-color: #f9f9f9;
}

.reply-title {
  font-size: 16px;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.empty-floors {
  padding: 30px 0;
}

.mt-3 {
  margin-top: 15px;
}
</style>
