/**
 * 认证相关 API
 */
import { get, post, put } from './request'
import type { LoginRequest, RegisterRequest, LoginResponse, TokenResponse, User } from '@/types/api'

/**
 * 用户登录
 */
export const login = (data: LoginRequest) => post<LoginResponse>('/auth/login', data)

/**
 * 用户注册
 */
export const register = (data: RegisterRequest) => post<User>('/auth/register', data)

/**
 * 刷新 token
 */
export const refreshToken = (refreshToken: string) =>
  post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken })

/**
 * 获取当前用户信息
 */
export const getCurrentUser = () => get<User>('/auth/me')

/**
 * 更新用户资料
 */
export const updateProfile = (data: Partial<User>) => put<User>('/auth/me', data)

/**
 * 修改密码
 */
export const changePassword = (oldPassword: string, newPassword: string) =>
  post('/auth/change-password', {
    old_password: oldPassword,
    new_password: newPassword,
  })
