/**
 * 权限管理 API
 */
import { get, post } from './request'
import type {
  PermissionGrant,
  PermissionRevoke,
  PermissionCheckRequest,
  PermissionCheckResponse,
  UserPermissionItem,
  ServerPermissionItem,
  PaginatedResponse,
  PaginationParams,
} from '@/types/api'

/**
 * 授予权限
 */
export const grantPermission = (data: PermissionGrant) => post('/permissions/grant', data)

/**
 * 撤销权限
 */
export const revokePermission = (data: PermissionRevoke) => post('/permissions/revoke', data)

/**
 * 检查权限
 */
export const checkPermission = (data: PermissionCheckRequest) =>
  post<PermissionCheckResponse>('/permissions/check', data)

/**
 * 获取用户权限列表
 */
export const getUserPermissions = (params?: PaginationParams) =>
  get<PaginatedResponse<UserPermissionItem>>('/permissions/user/permissions', { params })

/**
 * 获取服务器权限列表
 */
export const getServerPermissions = (serverId: string, params?: PaginationParams) =>
  get<PaginatedResponse<ServerPermissionItem>>(`/permissions/server/${serverId}`, {
    params,
  })

/**
 * 获取可访问服务器
 */
export const getAccessibleServers = (minPermission = 'read') =>
  get<{ server_ids: string[]; count: number }>('/permissions/user/accessible-servers', {
    params: { min_permission: minPermission },
  })
