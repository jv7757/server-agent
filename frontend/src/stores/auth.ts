/**
 * 认证状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginRequest, RegisterRequest } from '@/types/api'
import * as authApi from '@/api/auth'
import { ElMessage } from 'element-plus'

export const useAuthStore = defineStore(
  'auth',
  () => {
    // State
    const token = ref<string>('')
    const refreshToken = ref<string>('')
    const user = ref<User | null>(null)
    const isLoading = ref(false)

    // Getters
    const isAuthenticated = computed(() => !!token.value)
    const isAdmin = computed(() => user.value?.role === 'admin')
    const isUser = computed(() => user.value?.role === 'user')
    const isViewer = computed(() => user.value?.role === 'viewer')

    // Actions

    /**
     * 登录
     */
    const login = async (credentials: LoginRequest) => {
      isLoading.value = true
      try {
        const response = await authApi.login(credentials)
        token.value = response.access_token
        refreshToken.value = response.refresh_token
        user.value = response.user
        ElMessage.success('登录成功')
        return true
      } catch (error) {
        console.error('登录失败:', error)
        return false
      } finally {
        isLoading.value = false
      }
    }

    /**
     * 注册
     */
    const register = async (data: RegisterRequest) => {
      isLoading.value = true
      try {
        const newUser = await authApi.register(data)
        ElMessage.success('注册成功，请登录')
        return true
      } catch (error) {
        console.error('注册失败:', error)
        return false
      } finally {
        isLoading.value = false
      }
    }

    /**
     * 登出
     */
    const logout = () => {
      token.value = ''
      refreshToken.value = ''
      user.value = null
      ElMessage.info('已退出登录')
    }

    /**
     * 刷新 token
     */
    const refresh = async () => {
      if (!refreshToken.value) {
        return false
      }

      try {
        const response = await authApi.refreshToken(refreshToken.value)
        token.value = response.access_token
        return true
      } catch (error) {
        console.error('刷新 token 失败:', error)
        logout()
        return false
      }
    }

    /**
     * 获取当前用户信息
     */
    const fetchUser = async () => {
      if (!token.value) {
        return false
      }

      try {
        user.value = await authApi.getCurrentUser()
        return true
      } catch (error) {
        console.error('获取用户信息失败:', error)
        return false
      }
    }

    /**
     * 检查认证状态（应用启动时调用）
     */
    const checkAuth = async () => {
      // 如果没有 token，直接返回
      if (!token.value) {
        return false
      }

      // 尝试获取用户信息以验证 token 是否有效
      const success = await fetchUser()

      // 如果失败，尝试刷新 token
      if (!success && refreshToken.value) {
        const refreshed = await refresh()
        if (refreshed) {
          // 刷新成功后再次获取用户信息
          return await fetchUser()
        }
      }

      // 如果都失败了，清除认证状态
      if (!success) {
        logout()
      }

      return success
    }

    /**
     * 更新用户资料
     */
    const updateProfile = async (data: Partial<User>) => {
      try {
        const updatedUser = await authApi.updateProfile(data)
        user.value = updatedUser
        ElMessage.success('资料更新成功')
        return true
      } catch (error) {
        console.error('更新资料失败:', error)
        return false
      }
    }

    /**
     * 修改密码
     */
    const changePassword = async (oldPassword: string, newPassword: string) => {
      try {
        await authApi.changePassword(oldPassword, newPassword)
        ElMessage.success('密码修改成功，请重新登录')
        logout()
        return true
      } catch (error) {
        console.error('修改密码失败:', error)
        return false
      }
    }

    return {
      // State
      token,
      refreshToken,
      user,
      isLoading,
      // Getters
      isAuthenticated,
      isAdmin,
      isUser,
      isViewer,
      // Actions
      login,
      register,
      logout,
      refresh,
      fetchUser,
      checkAuth,
      updateProfile,
      changePassword,
    }
  },
  {
    // 持久化存储
    persist: {
      key: 'auth',
      storage: localStorage,
      paths: ['token', 'refreshToken', 'user'],
    },
  }
)
