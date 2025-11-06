<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="collapsed ? '64px' : '200px'" class="layout-aside">
      <div class="logo">
        <el-icon v-if="collapsed" :size="30">
          <Monitor />
        </el-icon>
        <template v-else>
          <el-icon :size="30">
            <Monitor />
          </el-icon>
          <span>Server Agent</span>
        </template>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        :collapse-transition="false"
        router
        class="menu"
      >
        <el-menu-item
          v-for="route in menuRoutes"
          :key="route.path"
          :index="route.path"
        >
          <el-icon>
            <component :is="route.meta?.icon" />
          </el-icon>
          <template #title>{{ route.meta?.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部导航栏 -->
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon class="collapse-icon" @click="toggleCollapse">
            <component :is="collapsed ? Expand : Fold" />
          </el-icon>
        </div>

        <div class="header-right">
          <!-- 语言切换 -->
          <el-dropdown @command="changeLocale">
            <el-icon :size="20">
              <Globe />
            </el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="zh-CN">中文</el-dropdown-item>
                <el-dropdown-item command="en-US">English</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <!-- 用户菜单 -->
          <el-dropdown @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32">
                <el-icon>
                  <User />
                </el-icon>
              </el-avatar>
              <span class="username">{{ authStore.user?.username }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  {{ $t('layout.profile') }}
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  {{ $t('layout.logout') }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容 -->
      <el-main class="layout-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import {
  Monitor,
  Fold,
  Expand,
  User,
  SwitchButton,
  Globe,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { locale } = useI18n()

// 侧边栏折叠状态
const collapsed = ref(false)

// 切换侧边栏
const toggleCollapse = () => {
  collapsed.value = !collapsed.value
}

// 当前激活的菜单
const activeMenu = computed(() => {
  const path = route.path
  // 如果是详情页等子页面，高亮父菜单
  if (path.startsWith('/servers/')) {
    return '/servers'
  }
  return path
})

// 菜单路由（过滤掉hidden的路由）
const menuRoutes = computed(() => {
  const routes = router.getRoutes()
  const layoutChildren = routes.find((r) => r.name === 'Layout')?.children || []

  return layoutChildren.filter((route) => {
    // 过滤掉隐藏的路由
    if (route.meta?.hidden) return false

    // 如果需要管理员权限，检查当前用户是否是管理员
    if (route.meta?.requiresAdmin && !authStore.isAdmin) {
      return false
    }

    return true
  })
})

// 处理用户菜单命令
const handleCommand = (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'logout':
      authStore.logout()
      router.push('/login')
      break
  }
}

// 切换语言
const changeLocale = (lang: string) => {
  locale.value = lang
  localStorage.setItem('locale', lang)
}
</script>

<style scoped lang="scss">
.layout-container {
  height: 100vh;
}

.layout-aside {
  background: #001529;
  transition: width 0.3s;

  .logo {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    height: 60px;
    color: white;
    font-size: 18px;
    font-weight: bold;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .menu {
    border-right: none;
    background: #001529;

    :deep(.el-menu-item) {
      color: rgba(255, 255, 255, 0.65);

      &:hover {
        color: white;
        background: rgba(255, 255, 255, 0.1);
      }

      &.is-active {
        color: white;
        background: #1890ff;
      }
    }
  }
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  border-bottom: 1px solid #f0f0f0;
  padding: 0 20px;

  .header-left {
    .collapse-icon {
      font-size: 20px;
      cursor: pointer;
      transition: color 0.3s;

      &:hover {
        color: #1890ff;
      }
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 20px;

    .el-icon {
      cursor: pointer;
      transition: color 0.3s;

      &:hover {
        color: #1890ff;
      }
    }

    .user-info {
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;

      .username {
        font-size: 14px;
      }
    }
  }
}

.layout-main {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

// 页面过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.fade-enter-from {
  opacity: 0;
  transform: translateX(-10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateX(10px);
}
</style>
