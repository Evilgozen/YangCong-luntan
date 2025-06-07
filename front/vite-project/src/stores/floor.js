import { defineStore } from 'pinia';
import axios from 'axios';
import { ref, computed } from 'vue';

// API 基础 URL
const API_URL = 'http://localhost:8000';

export const useFloorStore = defineStore('floor', () => {
  // State
  const floors = ref([]);
  const loading = ref(false);
  const error = ref(null);
  const currentPage = ref(1);
  const pageSize = ref(20);
  const replyingTo = ref(null);
  
  // Getters
  const hasFloors = computed(() => floors.value.length > 0);
  
  // Actions
  // 获取帖子的所有楼层
  async function getFloorsByPostId(postId, page = 1, size = 20) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await axios.get(`${API_URL}/floors/post/${postId}`, {
        params: {
          page,
          page_size: size
        },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      floors.value = response.data;
      currentPage.value = page;
      pageSize.value = size;
      
      return response.data;
    } catch (err) {
      error.value = err.response?.data?.detail || '获取楼层失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }
  
  // 创建新楼层（回复）
  async function createFloor(floorData) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await axios.post(`${API_URL}/floors/`, floorData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      // 添加到楼层列表
      floors.value.push(response.data);
      
      // 清除回复状态
      replyingTo.value = null;
      
      return response.data;
    } catch (err) {
      error.value = err.response?.data?.detail || '创建回复失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }
  
  // 更新楼层
  async function updateFloor(floorId, content) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await axios.put(`${API_URL}/floors/${floorId}`, { content }, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      // 更新本地存储的楼层
      const index = floors.value.findIndex(floor => floor.id === floorId);
      if (index !== -1) {
        floors.value[index] = response.data;
      }
      
      return response.data;
    } catch (err) {
      error.value = err.response?.data?.detail || '更新回复失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }
  
  // 删除楼层
  async function deleteFloor(floorId) {
    loading.value = true;
    error.value = null;
    
    try {
      await axios.delete(`${API_URL}/floors/${floorId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      // 从列表中移除楼层
      floors.value = floors.value.filter(floor => floor.id !== floorId);
      
      return true;
    } catch (err) {
      error.value = err.response?.data?.detail || '删除回复失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }
  
  // 设置回复目标
  function setReplyTarget(floor) {
    replyingTo.value = floor;
  }
  
  // 清除回复目标
  function clearReplyTarget() {
    replyingTo.value = null;
  }
  
  // 清除楼层
  function clearFloors() {
    floors.value = [];
    error.value = null;
  }

  return {
    // State
    floors,
    loading,
    error,
    currentPage,
    pageSize,
    replyingTo,
    // Getters
    hasFloors,
    // Actions
    getFloorsByPostId,
    createFloor,
    updateFloor,
    deleteFloor,
    setReplyTarget,
    clearReplyTarget,
    clearFloors
  };
});
