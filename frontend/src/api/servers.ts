/**
 * 服务器管理 API
 */
import { get, post, put, del } from './request'
import type {
  Server,
  ServerCreate,
  ServerUpdate,
  ConnectionTestResponse,
  PaginatedResponse,
  PaginationParams,
} from '@/types/api'

interface ServerQueryParams extends PaginationParams {
  status?: 'online' | 'offline' | 'error' | 'unknown'
  tags?: string
  search?: string
}

/**
 * 创建服务器
 */
export const createServer = (data: ServerCreate) => {
  return post<Server>('/servers', data)
}

/**
 * 获取服务器列表
 */
export const getServers = (params?: ServerQueryParams) => {
  return get<PaginatedResponse<Server>>('/servers', { params })
}

/**
 * 获取服务器详情
 */
export const getServer = (serverId: string) => {
  return get<Server>(`/servers/${serverId}`)
}

/**
 * 更新服务器
 */
export const updateServer = (serverId: string, data: ServerUpdate) => {
  return put<Server>(`/servers/${serverId}`, data)
}

/**
 * 删除服务器
 */
export const deleteServer = (serverId: string) => {
  return del(`/servers/${serverId}`)
}

/**
 * 测试服务器连接
 */
export const testConnection = (serverId: string) => {
  return post<ConnectionTestResponse>(`/servers/${serverId}/test-connection`)
}
