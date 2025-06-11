import { defineStore } from 'pinia';
import axios from 'axios';
import { ref } from 'vue';

// API 基础 URL
const API_URL = 'http://127.0.0.1:8000';

export const useLikeStore = defineStore('like', () => {
  // State
  const loading = ref(false);
  const error = ref(null);
  
  // Actions
  // 点赞帖子
  async function likePost(postId) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await axios.post(`${API_URL}/likes`, {
        post_id: postId
      }, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      return response.data;
    } catch (err) {
      error.value = err.response?.data?.detail || '点赞失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }
  
  // 取消点赞帖子
  async function unlikePost(postId) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await axios.delete(`${API_URL}/likes/${postId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      return response.data;
    } catch (err) {
      error.value = err.response?.data?.detail || '取消点赞失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }
  
  // 获取帖子点赞列表
  async function getPostLikes(postId, page = 1, pageSize = 10) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await axios.get(`${API_URL}/likes/posts/${postId}`, {
        params: {
          page,
          page_size: pageSize
        },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      return response.data;
    } catch (err) {
      error.value = err.response?.data?.detail || '获取点赞列表失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }
  
  // 获取当前用户点赞的帖子
  async function getMyLikedPosts(page = 1, pageSize = 10) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await axios.get(`${API_URL}/likes/users/me/liked-posts`, {
        params: {
          page,
          page_size: pageSize
        },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      return response.data;
    } catch (err) {
      error.value = err.response?.data?.detail || '获取点赞帖子失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // 获取帖子的点赞状态
  async function getPostLikeStatus(postId) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await axios.get(`${API_URL}/likes/posts/${postId}`, {
        params: {
          page: 1,
          page_size: 1
        },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      return {
        is_liked: response.data.is_liked,
        like_count: response.data.like_count
      };
    } catch (err) {
      error.value = err.response?.data?.detail || '获取点赞状态失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }
  
  return {
    loading,
    error,
    likePost,
    unlikePost,
    getPostLikes,
    getMyLikedPosts,
    getPostLikeStatus
  };
});