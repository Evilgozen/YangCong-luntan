import { defineStore } from 'pinia';
import axios from 'axios';
import { ref, computed } from 'vue';

// API 基础 URL - 修改此处以匹配您的后端 URL
const API_URL = 'http://0.0.0.0:8000';

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref(null);
  const token = ref(localStorage.getItem('token') || null);
  
  // 将avatarUrl改为计算属性，这样当user变化时会自动更新
  const avatarUrl = computed(() => {
    if (user.value?.avatar) {
      // 如果已经是完整URL，直接返回
      if (user.value.avatar.startsWith('http')) {
        return user.value.avatar;
      }
      // 否则拼接后端服务器地址
      return `${API_URL}${user.value.avatar}`;
    }
    return null;
  })

  // Getters
  const isLoggedIn = computed(() => !!token.value);
  
  // Actions
  async function register(userData) {
    try {
      const response = await axios.post(`${API_URL}/register`, userData);
      return response.data;
    } catch (error) {
      const message = error.response?.data?.detail || '注册失败';
      throw new Error(message);
    }
  }
  
  async function login(credentials) {
    try {
      // 将凭据转换为表单数据格式，用于 FastAPI OAuth2
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);
      
      const response = await axios.post(`${API_URL}/token`, formData);
      
      // 将令牌保存到状态和 localStorage
      token.value = response.data.access_token;
      localStorage.setItem('token', response.data.access_token);
      
      // 登录后获取用户资料
      await getUserProfile();
      
      return response.data;
    } catch (error) {
      const message = error.response?.data?.detail || '登录失败';
      throw new Error(message);
    }
  }
  
  async function getUserProfile() {
    if (!token.value) {
      throw new Error('未登录');
    }
    
    try {
      const response = await axios.get(`${API_URL}/users/me`, {
        headers: {
          Authorization: `Bearer ${token.value}`
        }
      });
      
      user.value = response.data;
      return response.data;
    } catch (error) {
      if (error.response?.status === 401) {
        // 令牌过期或无效
        logout();
      }
      throw error;
    }
  }
  
  async function updateProfile(profileData) {
    if (!token.value) {
      throw new Error('未登录');
    }
    
    try {
      // 如果有头像文件，先上传头像
      if (profileData.avatar instanceof File) {
        const formData = new FormData();
        formData.append('file', profileData.avatar);
        
        const uploadResponse = await axios.post(`${API_URL}/users/upload-avatar`, formData, {
          headers: {
            'Authorization': `Bearer ${token.value}`,
            'Content-Type': 'multipart/form-data'
          }
        });
        
        // 更新头像URL
        profileData.avatar = uploadResponse.data.avatar_url;
      }
      
      // 更新用户资料
      const response = await axios.put(`${API_URL}/users/update`, {
        email: profileData.email,
        bio: profileData.bio,
        avatar: profileData.avatar
      }, {
        headers: {
          Authorization: `Bearer ${token.value}`
        }
      });
      
      // 更新本地用户数据
      user.value = response.data;
      return response.data;
    } catch (error) {
      const message = error.response?.data?.detail || '更新个人资料失败';
      throw new Error(message);
    }
  }
  
  function logout() {
    user.value = null;
    token.value = null;
    localStorage.removeItem('token');
  }

  
  // 处理头像URL，确保完整路径
  function getAvatarUrl(avatarPath) {
    if (!avatarPath) return null;
    
    // 如果已经是完整URL，直接返回
    if (avatarPath.startsWith('http')) {
      return avatarPath;
    }
    
    // 否则拼接后端服务器地址
    return `http://localhost:8000${avatarPath}`;
  }

  // 获取用户个人空间信息
  async function getUserProfileSpace() {
    if (!token.value) {
      throw new Error('未登录');
    }
    
    try {
      const response = await axios.get(`${API_URL}/profile/me`, {
        headers: {
          Authorization: `Bearer ${token.value}`
        }
      });
      
      return response.data;
    } catch (error) {
      if (error.response?.status === 401) {
        // 令牌过期或无效
        logout();
      }
      throw error;
    }
  }

  // 获取用户发布的帖子
  async function getUserPosts(page = 1, pageSize = 10) {
    if (!token.value) {
      throw new Error('未登录');
    }
    
    try {
      const response = await axios.get(`${API_URL}/profile/me/posts`, {
        params: { page, page_size: pageSize },
        headers: {
          Authorization: `Bearer ${token.value}`
        }
      });
      
      return response.data;
    } catch (error) {
      if (error.response?.status === 401) {
        // 令牌过期或无效
        logout();
      }
      throw error;
    }
  }

  // 获取其他用户的个人空间信息
  async function getOtherUserProfile(userId) {
    try {
      const response = await axios.get(`${API_URL}/profile/users/${userId}`, {
        headers: token.value ? {
          Authorization: `Bearer ${token.value}`
        } : {}
      });
      
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // 获取其他用户发布的帖子
  async function getOtherUserPosts(userId, page = 1, pageSize = 10) {
    try {
      const response = await axios.get(`${API_URL}/profile/users/${userId}/posts`, {
        params: { page, page_size: pageSize },
        headers: token.value ? {
          Authorization: `Bearer ${token.value}`
        } : {}
      });
      
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  return {
    // State
    user,
    token,
    avatarUrl,
    // Getters
    isLoggedIn,
    // Actions
    register,
    login,
    getUserProfile,
    updateProfile,
    logout,
    getAvatarUrl,
    getUserProfileSpace,
    getUserPosts,
    getOtherUserProfile,
    getOtherUserPosts
  };
});
