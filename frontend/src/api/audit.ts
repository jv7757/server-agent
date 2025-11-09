/**
 * 审计日志 API
 */
import { get } from './request'
import type { PaginatedResponse, PaginationParams } from '@/types/api'

export interface AuditLog {
  id: number
  user_id: string | null
  username: string | null
  server_id: string | null
  server_name: string | null
  action: string
  resource_type: string | null
  details: Record<string, any> | null
  ip_address: string | null
  created_at: string
}

export interface AuditLogQueryParams extends PaginationParams {
  user_id?: string
  server_id?: string
  action?: string
  resource_type?: string
  search?: string
}

/**
 * 获取审计日志列表
 */
export const getAuditLogs = (params?: AuditLogQueryParams) =>
  get<PaginatedResponse<AuditLog>>('/audit-logs', params)

/**
 * 获取单条审计日志详情
 */
export const getAuditLog = (logId: number) => get<AuditLog>(`/audit-logs/${logId}`)
