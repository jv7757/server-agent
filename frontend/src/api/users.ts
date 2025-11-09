/**
 * 用户管理 API（管理员）
 */
import { get, post, put, del } from './request'
import type { PaginatedResponse, PaginationParams } from '@/types/api'

export interface User {
  id: string
  username: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserQueryParams extends PaginationParams {
  role?: string
  is_active?: boolean
  search?: string
}

export interface UserCreateRequest {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface UserUpdateRequest {
  email?: string
  full_name?: string
  password?: string
}

export interface UserRoleUpdateRequest {
  role: string
}

export interface UserStatusUpdateRequest {
  is_active: boolean
}

/**
 * 获取用户列表
 */
export const getUsers = (params?: UserQueryParams) => get<PaginatedResponse<User>>('/users', params)

/**
 * 获取用户详情
 */
export const getUser = (userId: string) => get<User>(`/users/${userId}`)

/**
 * 创建用户
 */
export const createUser = (data: UserCreateRequest) => post<User>('/users', data)

/**
 * 更新用户信息
 */
export const updateUser = (userId: string, data: UserUpdateRequest) =>
  put<User>(`/users/${userId}`, data)

/**
 * 删除用户
 */
export const deleteUser = (userId: string) => del(`/users/${userId}`)

/**
 * 修改用户角色
 */
export const updateUserRole = (userId: string, data: UserRoleUpdateRequest) =>
  put<User>(`/users/${userId}/role`, data)

/**
 * 启用/禁用用户
 */
export const updateUserStatus = (userId: string, data: UserStatusUpdateRequest) =>
  put<User>(`/users/${userId}/status`, data)
