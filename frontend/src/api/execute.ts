/**
 * 命令执行 API
 */
import { get, post } from './request'
import type {
  CommandExecuteRequest,
  CommandExecuteResponse,
  CommandValidateRequest,
  CommandValidateResponse,
  CommandHistory,
  PaginatedResponse,
  PaginationParams,
} from '@/types/api'

interface CommandHistoryParams extends PaginationParams {
  server_id?: string
}

/**
 * 执行命令
 */
export const executeCommand = (serverId: string, data: CommandExecuteRequest) => {
  return post<CommandExecuteResponse>(`/execute/servers/${serverId}`, data)
}

/**
 * 验证命令
 */
export const validateCommand = (data: CommandValidateRequest) => {
  return post<CommandValidateResponse>('/execute/validate', data)
}

/**
 * 批量执行命令
 */
export const executeBatch = (serverIds: string[], command: string, timeout?: number) => {
  return post('/execute/batch', {
    server_ids: serverIds,
    command,
    timeout,
  })
}

/**
 * 获取命令历史
 */
export const getCommandHistory = (params?: CommandHistoryParams) => {
  return get<PaginatedResponse<CommandHistory>>('/execute/history', { params })
}
