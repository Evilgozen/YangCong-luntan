import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue' // 导入所有图标
import './style.css'
import App from './App.vue'
import router from './router/router'

// Create Pinia store
const pinia = createPinia()

// Create app
const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// Use plugins
app.use(router)
app.use(pinia)
app.use(ElementPlus)

// Mount app
app.mount('#app')
