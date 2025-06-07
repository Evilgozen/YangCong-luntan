<template>
  <div class="post-form-container">
    <el-page-header @back="goBack" :title="'返回'" />
    
    <h2 class="form-title">{{ isEditing ? '编辑帖子' : '创建新帖子' }}</h2>
    
    <el-form 
      ref="formRef"
      :model="postForm"
      :rules="rules"
      label-position="top"
      @submit.prevent="submitForm"
    >
      <el-form-item label="标题" prop="title">
        <el-input v-model="postForm.title" placeholder="请输入帖子标题" maxlength="100" show-word-limit />
      </el-form-item>
      
      <el-form-item label="内容" prop="content">
        <el-input
          v-model="postForm.content"
          type="textarea"
          placeholder="请输入帖子内容"
          :rows="10"
          maxlength="5000"
          show-word-limit
        />
      </el-form-item>
      
      <el-form-item label="标签">
        <el-input
          v-model="postForm.tags"
          placeholder="输入标签，用逗号分隔"
          maxlength="100"
        />
        <div class="form-tip">标签示例: 技术,问题,讨论</div>
      </el-form-item>
      
      <el-form-item v-if="isEditing && (isAdmin || isAuthor)">
        <el-checkbox v-model="postForm.is_pinned">置顶帖子</el-checkbox>
        <el-checkbox v-model="postForm.is_closed">关闭讨论</el-checkbox>
      </el-form-item>
      
      <el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading">
          {{ isEditing ? '保存修改' : '发布帖子' }}
        </el-button>
        <el-button @click="goBack">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { usePostStore } from '../stores/post';
import { useUserStore } from '../stores/user';
import { ElMessage } from 'element-plus';

const route = useRoute();
const router = useRouter();
const postStore = usePostStore();
const userStore = useUserStore();

const formRef = ref(null);
const loading = ref(false);
const postId = computed(() => parseInt(route.params.id));
const isEditing = computed(() => !!postId.value);
const isAdmin = computed(() => userStore.user?.is_admin);
const isAuthor = computed(() => {
  if (!isEditing.value || !postStore.currentPost) return true;
  return postStore.currentPost.author_id === userStore.user?.id;
});

const postForm = reactive({
  title: '',
  content: '',
  tags: '',
  is_pinned: false,
  is_closed: false
});

const rules = {
  title: [
    { required: true, message: '请输入帖子标题', trigger: 'blur' },
    { min: 3, max: 100, message: '标题长度应在3到100个字符之间', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入帖子内容', trigger: 'blur' },
    { min: 10, max: 5000, message: '内容长度应在10到5000个字符之间', trigger: 'blur' }
  ]
};

onMounted(async () => {
  if (isEditing.value) {
    await fetchPostData();
  }
});

async function fetchPostData() {
  loading.value = true;
  
  try {
    const post = await postStore.getPostById(postId.value);
    
    // 检查权限
    if (!isAdmin.value && post.author_id !== userStore.user?.id) {
      ElMessage.error('您没有权限编辑此帖子');
      router.push(`/posts/${postId.value}`);
      return;
    }
    
    // 填充表单数据
    postForm.title = post.title;
    postForm.content = post.content;
    postForm.tags = post.tags || '';
    postForm.is_pinned = post.is_pinned;
    postForm.is_closed = post.is_closed;
  } catch (err) {
    ElMessage.error('获取帖子数据失败');
    console.error(err);
    router.push('/');
  } finally {
    loading.value = false;
  }
}

async function submitForm() {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    
    loading.value = true;
    
    try {
      if (isEditing.value) {
        // 更新帖子
        await postStore.updatePost(postId.value, postForm);
        ElMessage.success('帖子已更新');
        router.push(`/posts/${postId.value}`);
      } else {
        // 创建新帖子
        const newPost = await postStore.createPost(postForm);
        ElMessage.success('帖子已发布');
        router.push(`/posts/${newPost.id}`);
      }
    } catch (err) {
      ElMessage.error(err.message || (isEditing.value ? '更新帖子失败' : '发布帖子失败'));
      console.error(err);
    } finally {
      loading.value = false;
    }
  });
}

function goBack() {
  router.back();
}
</script>

<style scoped>
.post-form-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.form-title {
  margin: 30px 0;
  text-align: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
