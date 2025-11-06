/**
 * AI 聊天 API
 */
import { get, post, del } from './request'
import type {
  ChatRequest,
  ChatResponse,
  ChatMessage,
  Conversation,
  PaginatedResponse,
  PaginationParams,
} from '@/types/api'

/**
 * 发送消息
 */
export const sendMessage = (data: ChatRequest) => {
  return post<ChatResponse>('/chat/chat', data)
}

/**
 * 获取会话列表
 */
export const getConversations = (params?: PaginationParams) => {
  return get<PaginatedResponse<Conversation>>('/chat/conversations', { params })
}

/**
 * 获取会话消息
 */
export const getConversationMessages = (conversationId: string, params?: PaginationParams) => {
  return get<PaginatedResponse<ChatMessage>>(`/chat/conversations/${conversationId}`, { params })
}

/**
 * 删除会话
 */
export const deleteConversation = (conversationId: string) => {
  return del(`/chat/conversations/${conversationId}`)
}
