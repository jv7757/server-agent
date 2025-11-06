/**
 * Vue Router 配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false, title: '登录' },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresAuth: false, title: '注册' },
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layout/Layout.vue'),
    meta: { requiresAuth: true },
    redirect: '/servers',
    children: [
      {
        path: 'servers',
        name: 'Servers',
        component: () => import('@/views/servers/ServerList.vue'),
        meta: { title: '服务器管理', icon: 'Server' },
      },
      {
        path: 'servers/:id',
        name: 'ServerDetail',
        component: () => import('@/views/servers/ServerDetail.vue'),
        meta: { title: '服务器详情', hidden: true },
      },
      {
        path: 'monitoring',
        name: 'Monitoring',
        component: () => import('@/views/monitoring/Dashboard.vue'),
        meta: { title: '监控面板', icon: 'Monitor' },
      },
      {
        path: 'execute',
        name: 'Execute',
        component: () => import('@/views/execute/CommandExecute.vue'),
        meta: { title: '命令执行', icon: 'Console' },
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/chat/ChatInterface.vue'),
        meta: { title: 'AI 助手', icon: 'ChatDotRound' },
      },
      {
        path: 'permissions',
        name: 'Permissions',
        component: () => import('@/views/permissions/PermissionManage.vue'),
        meta: { title: '权限管理', icon: 'Key', requiresAdmin: true },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/UserProfile.vue'),
        meta: { title: '个人中心', icon: 'User', hidden: true },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { requiresAuth: false, title: '404' },
  },
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// 全局前置守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - Server Agent` : 'Server Agent'

  // 检查是否需要认证
  if (to.meta.requiresAuth !== false) {
    if (!authStore.isAuthenticated) {
      // 未登录，重定向到登录页
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }

    // 检查是否需要管理员权限
    if (to.meta.requiresAdmin && !authStore.isAdmin) {
      ElMessage.error('需要管理员权限')
      next(from.fullPath ? from : '/')
      return
    }
  }

  // 已登录用户访问登录页，重定向到首页
  if (authStore.isAuthenticated && (to.name === 'Login' || to.name === 'Register')) {
    next('/')
    return
  }

  next()
})

export default router
