/**
 * 命令执行状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type {
  CommandExecuteRequest,
  CommandExecuteResponse,
  CommandHistory,
  PaginatedResponse,
} from '@/types/api'
import * as executeApi from '@/api/execute'
import { ElMessage } from 'element-plus'

export const useExecuteStore = defineStore('execute', () => {
  // State
  const isExecuting = ref(false)
  const currentResult = ref<CommandExecuteResponse | null>(null)
  const history = ref<CommandHistory[]>([])
  const historyTotal = ref(0)
  const isLoadingHistory = ref(false)

  // Actions

  /**
   * 执行命令
   */
  const execute = async (data: CommandExecuteRequest): Promise<boolean> => {
    isExecuting.value = true
    try {
      const { server_id, ...requestData } = data
      const result = await executeApi.executeCommand(server_id, requestData)
      currentResult.value = result

      if (result.exit_code === 0) {
        ElMessage.success('命令执行成功')
      } else {
        ElMessage.warning(`命令执行完成，退出码: ${result.exit_code}`)
      }

      return true
    } catch (error: any) {
      console.error('命令执行失败:', error)
      ElMessage.error(error.response?.data?.detail || '命令执行失败')
      return false
    } finally {
      isExecuting.value = false
    }
  }

  /**
   * 验证命令安全性
   */
  const validate = async (command: string): Promise<boolean> => {
    try {
      const result = await executeApi.validateCommand({ command })

      if (!result.is_valid || result.risk_level === 'dangerous') {
        ElMessage.warning({
          message: `${result.message || '该命令可能具有风险'}`,
          duration: 5000,
        })
        return false
      }

      if (result.risk_level === 'warning') {
        ElMessage.warning({
          message: result.message || '该命令需要谨慎执行',
          duration: 3000,
        })
      }

      return result.is_valid
    } catch (error) {
      console.error('命令验证失败:', error)
      return false
    }
  }

  /**
   * 批量执行命令
   */
  const executeBatch = async (
    serverIds: string[],
    command: string,
    timeout?: number
  ): Promise<boolean> => {
    isExecuting.value = true
    try {
      await executeApi.executeBatch(serverIds, command, timeout)
      ElMessage.success(`命令已发送到 ${serverIds.length} 台服务器`)
      return true
    } catch (error: any) {
      console.error('批量执行失败:', error)
      ElMessage.error(error.response?.data?.detail || '批量执行失败')
      return false
    } finally {
      isExecuting.value = false
    }
  }

  /**
   * 获取命令历史
   */
  const fetchHistory = async (
    page: number = 1,
    size: number = 20,
    serverId?: string
  ): Promise<void> => {
    isLoadingHistory.value = true
    try {
      const params: any = { page, size }
      if (serverId) {
        params.server_id = serverId
      }

      const result: PaginatedResponse<CommandHistory> = await executeApi.getCommandHistory(params)
      history.value = result.items
      historyTotal.value = result.total
    } catch (error) {
      console.error('获取命令历史失败:', error)
      ElMessage.error('获取命令历史失败')
    } finally {
      isLoadingHistory.value = false
    }
  }

  /**
   * 清除当前结果
   */
  const clearResult = () => {
    currentResult.value = null
  }

  return {
    // State
    isExecuting,
    currentResult,
    history,
    historyTotal,
    isLoadingHistory,
    // Actions
    execute,
    validate,
    executeBatch,
    fetchHistory,
    clearResult,
  }
})
