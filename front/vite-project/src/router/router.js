import { createRouter, createWebHistory } from 'vue-router'

// 导入页面组件
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Profile from '../views/Profile.vue'
import PostDetail from '../views/PostDetail.vue'
import PostForm from '../views/PostForm.vue'
import MySpace from '../views/MySpace.vue'

// 创建路由
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Home, name: 'Home' },
    { path: '/login', component: Login, name: 'Login' },
    { path: '/register', component: Register, name: 'Register' },
    { path: '/profile', component: Profile, name: 'Profile', meta: { requiresAuth: true } },
    { path: '/myspace', component: MySpace, name: 'MySpace', meta: { requiresAuth: true } },
    { path: '/user/:id/space', component: MySpace, name: 'UserSpace' },
    { path: '/posts/create', component: PostForm, name: 'CreatePost', meta: { requiresAuth: true } },
    { path: '/posts/edit/:id', component: PostForm, name: 'EditPost', meta: { requiresAuth: true } },
    { path: '/posts/:id', component: PostDetail, name: 'PostDetail', meta: { requiresAuth: true } }
  ]
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    alert("请先登录");
    next('/login')
  } else {
    next()
  }
})

export default router