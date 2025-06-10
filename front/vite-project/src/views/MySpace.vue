<template>
  <div class="myspace-container">
    <el-row :gutter="20">
      <!-- 左侧个人信息卡片 -->
      <el-col :span="8">
        <el-card class="profile-card">
          <template #header>
            <div class="header">
              <h2>{{ isCurrentUser ? '我的空间' : '用户空间' }}</h2>
            </div>
          </template>
          
          <div class="profile-content" v-if="profileData">
            <div class="avatar-container">
              <el-avatar 
                :size="120" 
                :src="(isCurrentUser ? userStore.avatarUrl : userAvatarUrl) || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'"
                @click="handleAvatarClick"
              ></el-avatar>
              <div class="avatar-edit-hint" v-if="isCurrentUser">点击更换头像</div>
            </div>
            
            <div class="user-stats">
              <div class="stat-item">
                <div class="stat-value">{{ profileData.post_count }}</div>
                <div class="stat-label">发帖</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ profileData.floor_count }}</div>
                <div class="stat-label">回复</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ profileData.followers_count }}</div>
                <div class="stat-label">粉丝</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ profileData.following_count }}</div>
                <div class="stat-label">关注</div>
              </div>
            </div>
            
            <!-- 关注按钮 -->
            <div v-if="!isCurrentUser" class="follow-action">
              <el-button 
                :type="profileData.is_following ? 'danger' : 'primary'" 
                :plain="profileData.is_following"
                @click="handleFollowAction"
                :loading="followActionLoading"
              >
                {{ profileData.is_following ? '取消关注' : '关注' }}
              </el-button>
            </div>
            
            <!-- 个人资料标签页 -->
            <el-tabs v-model="activeTab" class="profile-tabs">
              <el-tab-pane label="个人资料" name="profile">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="用户名">{{ profileData.user.username }}</el-descriptions-item>
                  <el-descriptions-item label="邮箱">{{ profileData.user.email }}</el-descriptions-item>
                  <el-descriptions-item label="注册时间">{{ formatDate(profileData.user.created_at) }}</el-descriptions-item>
                  <el-descriptions-item label="上次登录">
                    {{ profileData.user.last_login ? formatDate(profileData.user.last_login) : '暂无记录' }}
                  </el-descriptions-item>
                </el-descriptions>
                
                <div class="bio-section">
                  <div class="bio-header">
                    <h3>个人简介</h3>
                    <el-button v-if="isCurrentUser" type="primary" size="small" @click="showBioEdit = true">编辑</el-button>
                  </div>
                  <div class="bio-content">
                    {{ profileData.user.bio || '这个人很懒，还没有填写个人简介...' }}
                  </div>
                </div>
              </el-tab-pane>
              
              <el-tab-pane :label="`关注 (${profileData.following_count})`" name="following">
                <following-list 
                  :userId="userId" 
                  @refresh-profile="fetchProfileData" 
                />
              </el-tab-pane>
              
              <el-tab-pane label="沙雕网名" name="nickname">
                <nickname-generator />
              </el-tab-pane>
            </el-tabs>
          </div>
          
          <div v-else class="loading-container">
            <el-skeleton :rows="6" animated />
          </div>
        </el-card>
      </el-col>
      
      <!-- 右侧帖子列表 -->
      <el-col :span="16">
        <el-card class="posts-card">
          <template #header>
            <div class="header">
              <h2>{{ isCurrentUser ? '我的帖子' : '用户帖子' }}</h2>
              <el-button v-if="isCurrentUser" type="primary" size="small" @click="router.push('/posts/create')">发布新帖</el-button>
            </div>
          </template>
          
          <div v-if="postsData">
            <el-empty v-if="postsData.results.length === 0" :description="isCurrentUser ? '您还没有发布过帖子' : '该用户还没有发布过帖子'"></el-empty>
            
            <div v-else>
              <el-table :data="postsData.results" style="width: 100%" @row-click="handleRowClick">
                <el-table-column prop="title" label="标题" min-width="200">
                  <template #default="scope">
                    <div class="post-title">{{ scope.row.title }}</div>
                  </template>
                </el-table-column>
                <el-table-column prop="view_count" label="浏览" width="80" align="center" />
                <el-table-column prop="floor_count" label="回复" width="80" align="center" />
                <el-table-column label="发布时间" width="180" align="center">
                  <template #default="scope">
                    {{ formatDate(scope.row.created_at) }}
                  </template>
                </el-table-column>
              </el-table>
              
              <div class="pagination-container">
                <el-pagination
                  v-model:current-page="currentPage"
                  v-model:page-size="pageSize"
                  :page-sizes="[5, 10, 20, 50]"
                  layout="total, sizes, prev, pager, next, jumper"
                  :total="postsData.total"
                  @size-change="handleSizeChange"
                  @current-change="handleCurrentChange"
                />
              </div>
            </div>
          </div>
          
          <div v-else class="loading-container">
            <el-skeleton :rows="6" animated />
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 头像上传对话框 -->
    <el-dialog v-model="showAvatarUpload" title="更换头像" width="400px">
      <el-upload
        class="avatar-uploader"
        action="#"
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleAvatarChange"
        accept="image/*"
      >
        <img v-if="avatarPreview" :src="avatarPreview" class="avatar-preview" />
        <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
      </el-upload>
      <div class="upload-hint">点击上方区域选择图片</div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAvatarUpload = false">取消</el-button>
          <el-button type="primary" @click="handleUpdateAvatar" :loading="uploading">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 个人简介编辑对话框 -->
    <el-dialog v-model="showBioEdit" title="编辑个人简介" width="500px">
      <el-form :model="bioForm" ref="bioFormRef">
        <el-form-item prop="bio">
          <el-input 
            v-model="bioForm.bio" 
            type="textarea" 
            :rows="5" 
            placeholder="请输入个人简介（最多200字）"
            maxlength="200"
            show-word-limit
          ></el-input>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showBioEdit = false">取消</el-button>
          <el-button type="primary" @click="handleUpdateBio" :loading="updating">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '../stores/user';
import { ElMessage } from 'element-plus';
import FollowingList from '../components/FollowingList.vue';
import NicknameGenerator from '../components/NicknameGenerator.vue';
import axios from 'axios';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

// 判断是否为当前用户的空间
const userId = ref(null);
const isCurrentUser = computed(() => !userId.value);
const profileData = ref(null);
const postsData = ref(null);
const currentPage = ref(1);
const pageSize = ref(10);
const userAvatarUrl = ref('');
const activeTab = ref('profile');
const followActionLoading = ref(false);

// 头像上传相关
const showAvatarUpload = ref(false);
const avatarPreview = ref('');
const avatarFile = ref(null);
const uploading = ref(false);

// 个人简介编辑相关
const showBioEdit = ref(false);
const bioForm = reactive({
  bio: ''
});
const bioFormRef = ref(null);
const updating = ref(false);

// 获取个人空间数据
const fetchProfileData = async () => {
  try {
    if (isCurrentUser.value) {
      // 获取当前用户的个人空间信息
      profileData.value = await userStore.getUserProfileSpace();
    } else {
      // 获取其他用户的个人空间信息
      profileData.value = await userStore.getOtherUserProfile(userId.value);
    }
    
    // 初始化个人简介表单
    if (profileData.value && profileData.value.user) {
      bioForm.bio = profileData.value.user.bio || '';
      
      // 处理头像URL
      if (profileData.value.user.avatar) {
        userAvatarUrl.value = userStore.getAvatarUrl(profileData.value.user.avatar);
      }
    }
  } catch (error) {
    ElMessage.error('获取个人空间信息失败');
    console.error(error);
  }
};

// 获取帖子列表
const fetchPostsData = async () => {
  try {
    if (isCurrentUser.value) {
      // 获取当前用户的帖子
      postsData.value = await userStore.getUserPosts(currentPage.value, pageSize.value);
    } else {
      // 获取其他用户的帖子
      postsData.value = await userStore.getOtherUserPosts(userId.value, currentPage.value, pageSize.value);
    }
  } catch (error) {
    ElMessage.error('获取帖子列表失败');
    console.error(error);
  }
};

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString();
};

// 处理头像变更
const handleAvatarChange = (file) => {
  if (!file) return;
  
  // 验证文件类型
  const isImage = file.raw.type.startsWith('image/');
  if (!isImage) {
    ElMessage.error('只能上传图片文件!');
    return;
  }
  
  // 验证文件大小 (限制为 2MB)
  const isLt2M = file.size / 1024 / 1024 < 2;
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!');
    return;
  }
  
  // 设置预览
  avatarPreview.value = URL.createObjectURL(file.raw);
  avatarFile.value = file.raw;
};

// 更新头像
const handleUpdateAvatar = async () => {
  if (!avatarFile.value) {
    ElMessage.warning('请先选择图片');
    return;
  }
  
  uploading.value = true;
  try {
    await userStore.updateProfile({
      email: profileData.value.user.email,
      bio: profileData.value.user.bio,
      avatar: avatarFile.value
    });
    
    ElMessage.success('头像更新成功');
    showAvatarUpload.value = false;
    
    // 重新获取个人资料
    await fetchProfileData();
  } catch (error) {
    ElMessage.error('头像更新失败');
    console.error(error);
  } finally {
    uploading.value = false;
  }
};

// 更新个人简介
const handleUpdateBio = async () => {
  updating.value = true;
  try {
    await userStore.updateProfile({
      email: profileData.value.user.email,
      bio: bioForm.bio,
      avatar: profileData.value.user.avatar
    });
    
    ElMessage.success('个人简介更新成功');
    showBioEdit.value = false;
    
    // 更新本地数据
    if (profileData.value && profileData.value.user) {
      profileData.value.user.bio = bioForm.bio;
    }
  } catch (error) {
    ElMessage.error('个人简介更新失败');
    console.error(error);
  } finally {
    updating.value = false;
  }
};

// 分页处理
const handleSizeChange = (val) => {
  pageSize.value = val;
  fetchPostsData();
};

const handleCurrentChange = (val) => {
  currentPage.value = val;
  fetchPostsData();
};

// 点击帖子行
const handleRowClick = (row) => {
  router.push(`/posts/${row.id}`);
};

// 处理头像点击事件
const handleAvatarClick = () => {
  if (isCurrentUser.value) {
    showAvatarUpload.value = true;
  }
};

  // 关注/取消关注用户
  const handleFollowAction = async () => {
    if (!userStore.isLoggedIn) {
      ElMessage.warning('请先登录');
      router.push('/login');
      return;
    }
    
    followActionLoading.value = true;
    try {
      if (profileData.value.is_following) {
        // 取消关注
        await axios.delete(`/api/follow/${userId.value}`, {
          headers: {
            Authorization: `Bearer ${userStore.token}`
          }
        });
        ElMessage.success('已取消关注');
        profileData.value.is_following = false;
        profileData.value.followers_count--;
      } else {
        // 关注用户
        await axios.post('/api/follow', {
          followed_id: userId.value
        }, {
          headers: {
            Authorization: `Bearer ${userStore.token}`
          }
        });
        ElMessage.success('关注成功');
        profileData.value.is_following = true;
        profileData.value.followers_count++;
      }
    } catch (error) {
      console.error('关注操作失败:', error);
      ElMessage.error('操作失败，请重试');
    } finally {
      followActionLoading.value = false;
    }
  };

// 组件挂载时获取数据
onMounted(async () => {
  // 检查是查看自己的空间还是其他用户的空间
  if (route.params.id) {
    userId.value = route.params.id;
  }
  // 如果是查看自己的空间，需要登录
  if (isCurrentUser.value && !userStore.isLoggedIn) {
    router.push('/login');
    return;
  }
  
  // 获取个人空间数据
  await fetchProfileData();
  
  // 获取帖子列表
  await fetchPostsData();
});
</script>

<style scoped>
.myspace-container {
  padding: 20px;
}

.profile-card, .posts-card {
  margin-bottom: 20px;
  height: 100%;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;
  cursor: pointer;
}

.avatar-edit-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.user-stats {
  display: flex;
  justify-content: space-around;
  margin: 20px 0;
  text-align: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.follow-action {
  display: flex;
  justify-content: center;
  margin: 15px 0;
}

.profile-tabs {
  margin-top: 20px;
}

.bio-section {
  margin-top: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px;
}

.bio-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.bio-header h3 {
  margin: 0;
  font-size: 16px;
}

.bio-content {
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  min-height: 60px;
  white-space: pre-wrap;
  word-break: break-all;
}

.loading-container {
  padding: 20px;
}

.post-title {
  cursor: pointer;
  color: #409eff;
}

.post-title:hover {
  text-decoration: underline;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.avatar-uploader {
  width: 200px;
  height: 200px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s;
  margin: 0 auto;
}

.avatar-uploader:hover {
  border-color: #409EFF;
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 200px;
  height: 200px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.avatar-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-hint {
  text-align: center;
  margin-top: 10px;
  color: #909399;
  font-size: 14px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
