/**
 * 服务器管理状态
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Server, ServerCreate, ServerUpdate } from '@/types/api'
import * as serversApi from '@/api/servers'
import { ElMessage } from 'element-plus'

export const useServersStore = defineStore('servers', () => {
  // State
  const servers = ref<Server[]>([])
  const currentServer = ref<Server | null>(null)
  const isLoading = ref(false)
  const total = ref(0)

  // Actions

  /**
   * 获取服务器列表
   */
  const fetchServers = async (params?: any) => {
    isLoading.value = true
    try {
      const response = await serversApi.getServers(params)
      servers.value = response.items
      total.value = response.total
      return true
    } catch (error) {
      console.error('获取服务器列表失败:', error)
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取服务器详情
   */
  const fetchServer = async (serverId: string) => {
    isLoading.value = true
    try {
      currentServer.value = await serversApi.getServer(serverId)
      return true
    } catch (error) {
      console.error('获取服务器详情失败:', error)
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 创建服务器
   */
  const createServer = async (data: ServerCreate) => {
    isLoading.value = true
    try {
      const newServer = await serversApi.createServer(data)
      servers.value.unshift(newServer)
      ElMessage.success('服务器创建成功')
      return newServer
    } catch (error) {
      console.error('创建服务器失败:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 更新服务器
   */
  const updateServer = async (serverId: string, data: ServerUpdate) => {
    isLoading.value = true
    try {
      const updatedServer = await serversApi.updateServer(serverId, data)
      const index = servers.value.findIndex((s) => s.id === serverId)
      if (index !== -1) {
        servers.value[index] = updatedServer
      }
      if (currentServer.value?.id === serverId) {
        currentServer.value = updatedServer
      }
      ElMessage.success('服务器更新成功')
      return true
    } catch (error) {
      console.error('更新服务器失败:', error)
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 删除服务器
   */
  const deleteServer = async (serverId: string) => {
    isLoading.value = true
    try {
      await serversApi.deleteServer(serverId)
      servers.value = servers.value.filter((s) => s.id !== serverId)
      if (currentServer.value?.id === serverId) {
        currentServer.value = null
      }
      ElMessage.success('服务器删除成功')
      return true
    } catch (error) {
      console.error('删除服务器失败:', error)
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 测试连接
   */
  const testConnection = async (serverId: string) => {
    try {
      const result = await serversApi.testConnection(serverId)
      if (result.success) {
        ElMessage.success(`连接成功 (延迟: ${result.latency?.toFixed(2)}ms)`)
      } else {
        ElMessage.error(`连接失败: ${result.message}`)
      }
      return result.success
    } catch (error) {
      console.error('测试连接失败:', error)
      return false
    }
  }

  /**
   * 根据 ID 获取服务器
   */
  const getServerById = (serverId: string) => {
    return servers.value.find((s) => s.id === serverId)
  }

  return {
    // State
    servers,
    currentServer,
    isLoading,
    total,
    // Actions
    fetchServers,
    fetchServer,
    createServer,
    updateServer,
    deleteServer,
    testConnection,
    getServerById,
  }
})
