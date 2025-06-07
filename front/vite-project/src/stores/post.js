import { defineStore } from 'pinia';
import axios from 'axios';
import { ref, computed } from 'vue';

// API 基础 URL - 与用户 store 保持一致
const API_URL = 'http://localhost:8000';

export const usePostStore = defineStore('post', () => {
  // State
  const posts = ref([]);
  const loading = ref(false);
  const error = ref(null);
  const searchQuery = ref('');
  const currentPage = ref(1);
  const pageSize = ref(10);
  const totalPosts = ref(0);
  const currentPost = ref(null);
  
  // Getters
  const hasPosts = computed(() => posts.value.length > 0);
  
  // Actions
  // 搜索帖子
  async function searchPosts(query = '', page = 1, size = 10) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await axios.get(`${API_URL}/posts/search`, {
        params: {
          query,
          page,
          page_size: size
        },
        headers: {
          //请求添加bearer头
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      posts.value = response.data.results;
      totalPosts.value = response.data.total;
      currentPage.value = response.data.page;
      pageSize.value = response.data.page_size;
      searchQuery.value = query;
      
      return response.data;
    } catch (err) {
      error.value = err.response?.data?.detail || '获取帖子失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }
  
  // 获取所有帖子（不带搜索）
  async function fetchPosts(page = 1, size = 10) {
    return searchPosts('', page, size);
  }
  
  // 获取单个帖子详情
  async function getPostById(postId) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await axios.get(`${API_URL}/posts/${postId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      currentPost.value = response.data;
      return response.data;
    } catch (err) {
      error.value = err.response?.data?.detail || '获取帖子详情失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }
  
  // 创建新帖子
  async function createPost(postData) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await axios.post(`${API_URL}/posts/`, postData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      // 添加到帖子列表的开头
      if (posts.value.length > 0) {
        posts.value.unshift(response.data);
      }
      
      return response.data;
    } catch (err) {
      error.value = err.response?.data?.detail || '创建帖子失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }
  
  // 更新帖子
  async function updatePost(postId, postData) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await axios.put(`${API_URL}/posts/${postId}`, postData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      // 更新本地存储的帖子
      const index = posts.value.findIndex(post => post.id === postId);
      if (index !== -1) {
        posts.value[index] = response.data;
      }
      
      // 如果是当前查看的帖子，也更新它
      if (currentPost.value && currentPost.value.id === postId) {
        currentPost.value = response.data;
      }
      
      return response.data;
    } catch (err) {
      error.value = err.response?.data?.detail || '更新帖子失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }
  
  // 删除帖子
  async function deletePost(postId) {
    loading.value = true;
    error.value = null;
    
    try {
      await axios.delete(`${API_URL}/posts/${postId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      // 从列表中移除帖子
      posts.value = posts.value.filter(post => post.id !== postId);
      
      // 如果是当前帖子，清除它
      if (currentPost.value && currentPost.value.id === postId) {
        currentPost.value = null;
      }
      
      return true;
    } catch (err) {
      error.value = err.response?.data?.detail || '删除帖子失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }
  
  // 清除状态
  function clearPosts() {
    posts.value = [];
    error.value = null;
    searchQuery.value = '';
  }
  
  // 清除当前帖子
  function clearCurrentPost() {
    currentPost.value = null;
  }

  return {
    // State
    posts,
    loading,
    error,
    searchQuery,
    currentPage,
    pageSize,
    totalPosts,
    currentPost,
    // Getters
    hasPosts,
    // Actions
    searchPosts,
    fetchPosts,
    getPostById,
    createPost,
    updatePost,
    deletePost,
    clearPosts,
    clearCurrentPost
  };
});
