/**
 * API 类型定义
 */

// ========== 通用类型 ==========

export interface PaginationParams {
  page?: number
  size?: number
}

export interface PaginatedResponse<T> {
  total: number
  page: number
  size: number
  items: T[]
}

// ========== 用户和认证 ==========

export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'user' | 'viewer'
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

// ========== 服务器 ==========

export interface Server {
  id: string
  name: string
  host: string
  port: number
  ssh_username: string
  description?: string
  tags: string[]
  status: 'online' | 'offline' | 'error' | 'unknown'
  owner_id: string
  created_at: string
  updated_at?: string
}

export interface ServerCreate {
  name: string
  host: string
  port: number
  ssh_username: string
  ssh_password?: string
  ssh_key?: string
  description?: string
  tags?: string[]
}

export interface ServerUpdate {
  name?: string
  host?: string
  port?: number
  ssh_username?: string
  ssh_password?: string
  ssh_key?: string
  description?: string
  tags?: string[]
}

export interface ConnectionTestResponse {
  success: boolean
  message: string
  latency?: number
}

// ========== 监控指标 ==========

export interface Metric {
  cpu_percent: number
  memory_percent: number
  memory_used_mb: number
  memory_total_mb: number
  disk_percent: number
  disk_used_gb: number
  disk_total_gb: number
  network_sent_mb: number
  network_recv_mb: number
  collected_at: string
}

export interface MetricsSummary {
  cpu: {
    avg: number
    min: number
    max: number
  }
  memory: {
    avg: number
    min: number
    max: number
  }
  disk: {
    current: number
  }
}

// ========== 命令执行 ==========

export interface CommandExecuteRequest {
  server_id: string
  command: string
  timeout?: number
}

export interface CommandExecuteResponse {
  success: boolean
  stdout: string
  stderr: string
  exit_code: number
  execution_time: number
}

export interface CommandValidateRequest {
  command: string
}

export interface CommandValidateResponse {
  is_safe: boolean
  is_dangerous: boolean
  message: string
}

export interface CommandHistory {
  id: number
  user_id: string
  server_id: string
  command: string
  success: boolean
  stdout: string
  stderr: string
  exit_code: number
  execution_time: number
  ip_address?: string
  created_at: string
}

// ========== AI 聊天 ==========

export interface ChatRequest {
  message: string
  conversation_id?: string
}

export interface ChatResponse {
  conversation_id: string
  message: string
  iterations?: number
  error?: string
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface Conversation {
  conversation_id: string
  last_message: string
  last_message_at: string
  role: string
}

// ========== 权限 ==========

export interface PermissionGrant {
  server_id: string
  target_user_id: string
  permissions: ('read' | 'write' | 'execute' | 'admin')[]
}

export interface PermissionRevoke {
  server_id: string
  target_user_id: string
}

export interface Permission {
  permission_id: number
  server_id: string
  user_id: string
  permissions: string[]
  created_at: string
}

export interface UserPermissionItem {
  permission_id: number
  server_id: string
  server_name: string
  server_host: string
  permissions: string[]
  created_at: string
}

export interface ServerPermissionItem {
  permission_id: number
  user_id: string
  username: string
  email: string
  permissions: string[]
  created_at: string
}

export interface PermissionCheckRequest {
  server_id: string
  required_permission: 'read' | 'write' | 'execute' | 'admin'
}

export interface PermissionCheckResponse {
  has_permission: boolean
  server_id: string
  required_permission: string
}
