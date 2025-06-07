<template>
  <div class="profile-container">
    <el-card class="profile-card">
      <template #header>
        <div class="header">
          <h2>个人资料</h2>
          <el-button type="danger" @click="handleLogout" size="small">退出登录</el-button>
        </div>
      </template>
      
      <div class="profile-content" v-if="userStore.user">
        <div class="avatar-container">
          <el-avatar :size="100" :src="userStore.avatarUrl || avatarPreview || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'"></el-avatar>
        </div>
        
        <el-descriptions title="用户信息" :column="1" border>
          <el-descriptions-item label="用户名">{{ userStore.user.username }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ userStore.user.email }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ formatDate(userStore.user.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="上次登录">{{ userStore.user.last_login ? formatDate(userStore.user.last_login) : '暂无记录' }}</el-descriptions-item>
        </el-descriptions>
        
        <div class="profile-actions">
          <el-button type="primary" @click="showEditForm = true">编辑资料</el-button>
        </div>
      </div>
      
      <el-dialog v-model="showEditForm" title="编辑个人资料" width="500px">
        <el-form :model="editForm" :rules="rules" ref="editFormRef" label-width="100px">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="editForm.username" disabled></el-input>
          </el-form-item>
          
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="editForm.email"></el-input>
          </el-form-item>
          
          <el-form-item label="个人简介" prop="bio">
            <el-input v-model="editForm.bio" type="textarea" :rows="4"></el-input>
          </el-form-item>
          
          <el-form-item label="头像" prop="avatar">
            <div class="avatar-upload">
              <el-upload
                class="avatar-uploader"
                action="http://localhost:8000/uploads/avatars"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleAvatarChange"
                accept="image/*"
              >
                <img v-if="avatarPreview" :src="avatarPreview" class="avatar-preview" />
                <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
              </el-upload>
              <div class="avatar-upload-tip">
                <p>点击上传头像</p>
                <p v-if="avatarPreview" class="current-file">
                  已选择: {{ avatarFileName || '预览中' }}
                </p>
              </div>
            </div>
          </el-form-item>
        </el-form>
        
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showEditForm = false">取消</el-button>
            <el-button type="primary" @click="handleUpdateProfile" :loading="loading">
              保存
            </el-button>
          </span>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useUserStore } from '../stores/user';
import { Plus } from '@element-plus/icons-vue';

const router = useRouter();
const userStore = useUserStore();
const editFormRef = ref(null);
const loading = ref(false);
const showEditForm = ref(false);
const avatarPreview = ref('');
const avatarFileName = ref('');

watch(() => userStore.user, (newValue) => {
  if (newValue && newValue.avatar) {
    console.log('Avatar path:', newValue.avatar);
  }
})

const editForm = reactive({
  username: '',
  email: '',
  bio: '',
  avatar: null
});

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  bio: [
    { max: 200, message: '个人简介不能超过200个字符', trigger: 'blur' }
  ]
};

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
  avatarFileName.value = file.name;
  
  // 将文件对象保存到表单数据中
  editForm.avatar = file.raw;
};

onMounted(async () => {
  if (!userStore.isLoggedIn) {
    router.push('/login');
    return;
  }
  
  try {
    await userStore.getUserProfile();
    if (userStore.user) {
      editForm.username = userStore.user.username;
      editForm.email = userStore.user.email;
      editForm.bio = userStore.user.bio || '';
      
      // 设置当前头像预览
      if (userStore.avatarUrl) {
        avatarPreview.value = userStore.avatarUrl;
        console.log('Real path:', avatarPreview.value);
      }
    }
  } catch (error) {
    ElMessage.error('获取用户信息失败');
  }
});

const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString();
};

const handleUpdateProfile = async () => {
  if (!editFormRef.value) return;
  
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        await userStore.updateProfile(editForm);
        ElMessage.success('个人资料更新成功');
        showEditForm.value = false;
      } catch (error) {
        ElMessage.error(error.message || '更新失败，请稍后再试');
      } finally {
        loading.value = false;
      }
    }
  });
};

const handleLogout = () => {
  userStore.logout();
  ElMessage.success('已退出登录');
  router.push('/');
};
</script>

<style scoped>
.profile-container {
  display: flex;
  justify-content: center;
  padding: 20px;
}

.profile-card {
  width: 100%;
  max-width: 600px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.avatar-container {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.profile-actions {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.avatar-upload {
  display: flex;
  align-items: center;
}

.avatar-uploader {
  width: 100px;
  height: 100px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s;
}

.avatar-uploader:hover {
  border-color: #409EFF;
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.avatar-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-upload-tip {
  margin-left: 16px;
  font-size: 14px;
  color: #606266;
}

.current-file {
  color: #409EFF;
  font-size: 12px;
  margin-top: 4px;
}
</style>
