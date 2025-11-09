/**
 * AI聊天状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ChatRequest,
  ChatMessage,
  Conversation,
  PaginatedResponse,
} from '@/types/api'
import * as chatApi from '@/api/chat'
import { ElMessage } from 'element-plus'

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref<ChatMessage[]>([])
  const conversations = ref<Conversation[]>([])
  const currentConversationId = ref<string | null>(null)
  const isSending = ref(false)
  const isLoadingConversations = ref(false)
  const isLoadingMessages = ref(false)

  // Getters
  const currentConversation = computed(() => {
    return conversations.value.find((c) => c.conversation_id === currentConversationId.value)
  })

  const hasMessages = computed(() => messages.value.length > 0)

  // Actions

  /**
   * 发送消息
   */
  const sendMessage = async (data: ChatRequest): Promise<boolean> => {
    isSending.value = true
    try {
      // 添加用户消息到列表
      const userMessage: ChatMessage = {
        id: `temp-${Date.now()}`,
        role: 'user',
        content: data.message,
        created_at: new Date().toISOString(),
      }
      messages.value.push(userMessage)

      // 发送消息到后端
      const response = await chatApi.sendMessage(data)

      // 添加AI回复到列表
      const aiMessage: ChatMessage = {
        id: response.message_id || `ai-${Date.now()}`,
        role: 'assistant',
        content: response.message,
        created_at: new Date().toISOString(),
      }
      messages.value.push(aiMessage)

      // 如果有会话ID，更新当前会话
      if (response.conversation_id && !currentConversationId.value) {
        currentConversationId.value = response.conversation_id
      }

      return true
    } catch (error: any) {
      console.error('发送消息失败:', error)
      ElMessage.error(error.response?.data?.detail || '发送消息失败')
      // 移除临时添加的用户消息
      messages.value.pop()
      return false
    } finally {
      isSending.value = false
    }
  }

  /**
   * 获取会话列表
   */
  const fetchConversations = async (page: number = 1, size: number = 20): Promise<void> => {
    isLoadingConversations.value = true
    try {
      const result: PaginatedResponse<Conversation> = await chatApi.getConversations({
        page,
        size,
      })
      conversations.value = result.items
    } catch (error) {
      console.error('获取会话列表失败:', error)
      ElMessage.error('获取会话列表失败')
    } finally {
      isLoadingConversations.value = false
    }
  }

  /**
   * 加载会话消息
   */
  const loadConversation = async (conversationId: string): Promise<void> => {
    isLoadingMessages.value = true
    currentConversationId.value = conversationId
    try {
      const result: PaginatedResponse<ChatMessage> = await chatApi.getConversationMessages(
        conversationId,
        { page: 1, size: 100 }
      )
      messages.value = result.items.reverse() // 最新消息在最后
    } catch (error) {
      console.error('加载会话消息失败:', error)
      ElMessage.error('加载会话消息失败')
    } finally {
      isLoadingMessages.value = false
    }
  }

  /**
   * 删除会话
   */
  const deleteConversation = async (conversationId: string): Promise<boolean> => {
    try {
      await chatApi.deleteConversation(conversationId)

      // 从列表中移除
      conversations.value = conversations.value.filter((c) => c.conversation_id !== conversationId)

      // 如果删除的是当前会话，清空消息
      if (currentConversationId.value === conversationId) {
        clearMessages()
      }

      ElMessage.success('会话已删除')
      return true
    } catch (error: any) {
      console.error('删除会话失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除会话失败')
      return false
    }
  }

  /**
   * 开始新会话
   */
  const startNewConversation = (_serverId?: string) => {
    currentConversationId.value = null
    messages.value = []
  }

  /**
   * 清空消息列表
   */
  const clearMessages = () => {
    messages.value = []
    currentConversationId.value = null
  }

  return {
    // State
    messages,
    conversations,
    currentConversationId,
    isSending,
    isLoadingConversations,
    isLoadingMessages,
    // Getters
    currentConversation,
    hasMessages,
    // Actions
    sendMessage,
    fetchConversations,
    loadConversation,
    deleteConversation,
    startNewConversation,
    clearMessages,
  }
})
