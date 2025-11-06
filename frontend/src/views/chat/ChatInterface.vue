<template>
  <div class="chat-interface">
    <el-container>
      <!-- 会话列表侧边栏 -->
      <el-aside width="280px" class="chat-aside">
        <div class="aside-header">
          <h3>{{ $t('chat.conversations') }}</h3>
          <el-button
            type="primary"
            size="small"
            :icon="Plus"
            @click="handleNewChat"
          >
            {{ $t('chat.new') }}
          </el-button>
        </div>

        <el-scrollbar class="conversation-list">
          <div
            v-for="conv in chatStore.conversations"
            :key="conv.conversation_id"
            class="conversation-item"
            :class="{ active: conv.conversation_id === chatStore.currentConversationId }"
            @click="handleLoadConversation(conv.conversation_id)"
          >
            <div class="conv-content">
              <div class="conv-title">
                {{ truncateText(conv.last_message, 30) || $t('chat.untitled') }}
              </div>
              <div class="conv-time">
                {{ formatDate(conv.last_message_at) }}
              </div>
            </div>
            <el-button
              link
              :icon="Delete"
              type="danger"
              size="small"
              @click.stop="handleDeleteConversation(conv.conversation_id)"
            />
          </div>

          <el-empty
            v-if="!chatStore.conversations.length && !chatStore.isLoadingConversations"
            :description="$t('chat.noConversations')"
            :image-size="80"
          />
        </el-scrollbar>
      </el-aside>

      <!-- 聊天主区域 -->
      <el-container class="chat-main">
        <!-- 工具栏 -->
        <el-header height="60px" class="chat-header">
          <div class="header-left">
            <el-icon><ChatDotRound /></el-icon>
            <span>{{ $t('chat.title') }}</span>
          </div>

          <div class="header-right">
            <!-- 服务器上下文选择 -->
            <el-select
              v-model="selectedServerId"
              clearable
              filterable
              :placeholder="$t('chat.selectServer')"
              size="default"
              style="width: 240px"
            >
              <el-option
                v-for="server in servers"
                :key="server.id"
                :label="server.name"
                :value="server.id"
              >
                <span>{{ server.name }}</span>
                <el-tag size="small" :type="getServerStatusType(server.status)" style="margin-left: 8px">
                  {{ server.status }}
                </el-tag>
              </el-option>
            </el-select>

            <el-button :icon="Refresh" @click="loadConversations">
              {{ $t('common.refresh') }}
            </el-button>
          </div>
        </el-header>

        <!-- 消息列表 -->
        <el-main class="chat-messages">
          <el-scrollbar ref="messagesScrollbar" class="messages-scrollbar">
            <div class="messages-container">
              <div
                v-for="(message, index) in chatStore.messages"
                :key="message.id || index"
                class="message-item"
                :class="message.role"
              >
                <div class="message-avatar">
                  <el-avatar v-if="message.role === 'user'" :icon="UserFilled" />
                  <el-avatar v-else>
                    <el-icon><Cpu /></el-icon>
                  </el-avatar>
                </div>

                <div class="message-content">
                  <div class="message-header">
                    <span class="message-role">
                      {{ message.role === 'user' ? $t('chat.you') : $t('chat.assistant') }}
                    </span>
                    <span class="message-time">
                      {{ formatTime(message.created_at) }}
                    </span>
                  </div>
                  <div class="message-text" v-html="renderMarkdown(message.content)" />
                </div>
              </div>

              <!-- 加载状态 -->
              <div v-if="chatStore.isSending" class="message-item assistant loading">
                <div class="message-avatar">
                  <el-avatar>
                    <el-icon><Cpu /></el-icon>
                  </el-avatar>
                </div>
                <div class="message-content">
                  <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>

              <!-- 空状态 -->
              <div v-if="!chatStore.hasMessages && !chatStore.isSending" class="empty-state">
                <el-icon :size="64" color="#c0c4cc"><ChatDotRound /></el-icon>
                <p>{{ $t('chat.startConversation') }}</p>
                <div class="quick-questions">
                  <el-tag
                    v-for="(q, idx) in quickQuestions"
                    :key="idx"
                    class="quick-question"
                    @click="handleQuickQuestion(q)"
                  >
                    {{ q }}
                  </el-tag>
                </div>
              </div>
            </div>
          </el-scrollbar>
        </el-main>

        <!-- 输入框 -->
        <el-footer height="auto" class="chat-footer">
          <div class="input-container">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              :placeholder="$t('chat.inputPlaceholder')"
              :disabled="chatStore.isSending"
              @keydown.ctrl.enter="handleSend"
              @keydown.meta.enter="handleSend"
            />
            <div class="footer-actions">
              <div class="action-left">
                <el-text type="info" size="small">
                  {{ $t('chat.sendTip') }}
                </el-text>
              </div>
              <div class="action-right">
                <el-button
                  type="primary"
                  :icon="Promotion"
                  :loading="chatStore.isSending"
                  :disabled="!inputMessage.trim()"
                  @click="handleSend"
                >
                  {{ $t('chat.send') }}
                </el-button>
              </div>
            </div>
          </div>
        </el-footer>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatDotRound,
  Plus,
  Delete,
  Refresh,
  UserFilled,
  Cpu,
  Promotion,
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import { useChatStore } from '@/stores/chat'
import { useServersStore } from '@/stores/servers'
import type { ElScrollbar } from 'element-plus'

const { t } = useI18n()
const chatStore = useChatStore()
const serversStore = useServersStore()

// State
const inputMessage = ref('')
const selectedServerId = ref<string>()
const messagesScrollbar = ref<InstanceType<typeof ElScrollbar>>()

const servers = computed(() => serversStore.servers)

// 快速问题
const quickQuestions = [
  t('chat.quickQuestion1'),
  t('chat.quickQuestion2'),
  t('chat.quickQuestion3'),
]

// Actions

const handleNewChat = () => {
  chatStore.startNewConversation(selectedServerId.value)
  inputMessage.value = ''
}

const handleLoadConversation = async (conversationId: string) => {
  await chatStore.loadConversation(conversationId)
  scrollToBottom()
}

const handleDeleteConversation = async (conversationId: string) => {
  try {
    await ElMessageBox.confirm(
      t('chat.deleteConfirm'),
      t('common.warning'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning',
      }
    )

    await chatStore.deleteConversation(conversationId)
  } catch {
    // User cancelled
  }
}

const handleSend = async () => {
  if (!inputMessage.value.trim() || chatStore.isSending) return

  const message = inputMessage.value
  inputMessage.value = ''

  const success = await chatStore.sendMessage({
    message,
    conversation_id: chatStore.currentConversationId || undefined,
    server_id: selectedServerId.value || undefined,
  })

  if (success) {
    await nextTick()
    scrollToBottom()
  }
}

const handleQuickQuestion = (question: string) => {
  inputMessage.value = question
  handleSend()
}

const loadConversations = async () => {
  await chatStore.fetchConversations()
}

const scrollToBottom = () => {
  nextTick(() => {
    messagesScrollbar.value?.setScrollTop(999999)
  })
}

const renderMarkdown = (text: string): string => {
  try {
    return marked.parse(text) as string
  } catch {
    return text
  }
}

const truncateText = (text: string, maxLength: number): string => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const formatDate = (date: string) => {
  const d = new Date(date)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return t('common.today')
  if (diffDays === 1) return t('common.yesterday')
  if (diffDays < 7) return `${diffDays} ${t('common.daysAgo')}`

  return d.toLocaleDateString()
}

const formatTime = (date: string) => {
  return new Date(date).toLocaleTimeString()
}

const getServerStatusType = (status: string) => {
  const statusMap: Record<string, 'success' | 'danger' | 'warning' | 'info'> = {
    online: 'success',
    offline: 'danger',
    error: 'danger',
    unknown: 'info',
  }
  return statusMap[status] || 'info'
}

// Watch for new messages to auto-scroll
watch(
  () => chatStore.messages.length,
  () => {
    scrollToBottom()
  }
)

// Lifecycle
onMounted(async () => {
  await Promise.all([
    serversStore.fetchServers(),
    chatStore.fetchConversations(),
  ])
})
</script>

<style scoped lang="scss">
.chat-interface {
  height: 100%;
  background: var(--el-bg-color);

  .el-container {
    height: 100%;
  }

  // 侧边栏
  .chat-aside {
    border-right: 1px solid var(--el-border-color);
    background: var(--el-bg-color-page);
    display: flex;
    flex-direction: column;

    .aside-header {
      padding: 16px;
      border-bottom: 1px solid var(--el-border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;

      h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
      }
    }

    .conversation-list {
      flex: 1;
      padding: 8px;

      .conversation-item {
        padding: 12px;
        margin-bottom: 8px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        gap: 8px;

        &:hover {
          background: var(--el-fill-color-light);
        }

        &.active {
          background: var(--el-color-primary-light-9);
          border-left: 3px solid var(--el-color-primary);
        }

        .conv-content {
          flex: 1;
          min-width: 0;

          .conv-title {
            font-weight: 500;
            margin-bottom: 4px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          .conv-time {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
      }
    }
  }

  // 主聊天区
  .chat-main {
    display: flex;
    flex-direction: column;
  }

  .chat-header {
    border-bottom: 1px solid var(--el-border-color);
    padding: 0 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-left {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 18px;
      font-weight: 600;
    }

    .header-right {
      display: flex;
      gap: 12px;
      align-items: center;
    }
  }

  .chat-messages {
    flex: 1;
    padding: 0;
    overflow: hidden;

    .messages-scrollbar {
      height: 100%;
    }

    .messages-container {
      padding: 20px;
      max-width: 900px;
      margin: 0 auto;

      .message-item {
        display: flex;
        gap: 12px;
        margin-bottom: 24px;

        &.user {
          flex-direction: row-reverse;

          .message-content {
            background: var(--el-color-primary-light-9);
            align-items: flex-end;
          }
        }

        .message-avatar {
          flex-shrink: 0;
        }

        .message-content {
          flex: 1;
          min-width: 0;

          .message-header {
            display: flex;
            gap: 12px;
            margin-bottom: 8px;
            font-size: 13px;

            .message-role {
              font-weight: 600;
              color: var(--el-text-color-primary);
            }

            .message-time {
              color: var(--el-text-color-secondary);
            }
          }

          .message-text {
            padding: 12px 16px;
            background: var(--el-fill-color-light);
            border-radius: 8px;
            line-height: 1.6;
            word-wrap: break-word;

            :deep(p) {
              margin: 0 0 8px;

              &:last-child {
                margin-bottom: 0;
              }
            }

            :deep(pre) {
              background: #1e1e1e;
              color: #d4d4d4;
              padding: 12px;
              border-radius: 4px;
              overflow-x: auto;
              margin: 8px 0;

              code {
                font-family: 'Courier New', Courier, monospace;
                font-size: 13px;
              }
            }

            :deep(code) {
              background: var(--el-fill-color);
              padding: 2px 6px;
              border-radius: 3px;
              font-family: 'Courier New', Courier, monospace;
              font-size: 13px;
            }
          }
        }

        &.loading {
          .loading-dots {
            display: flex;
            gap: 4px;
            padding: 12px 16px;

            span {
              width: 8px;
              height: 8px;
              border-radius: 50%;
              background: var(--el-color-primary);
              animation: bounce 1.4s infinite ease-in-out both;

              &:nth-child(1) {
                animation-delay: -0.32s;
              }

              &:nth-child(2) {
                animation-delay: -0.16s;
              }
            }
          }
        }
      }

      .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: var(--el-text-color-secondary);

        p {
          margin: 16px 0 24px;
          font-size: 16px;
        }

        .quick-questions {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          justify-content: center;

          .quick-question {
            cursor: pointer;
            transition: all 0.2s;

            &:hover {
              transform: translateY(-2px);
              box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
          }
        }
      }
    }
  }

  .chat-footer {
    border-top: 1px solid var(--el-border-color);
    padding: 16px 20px;

    .input-container {
      max-width: 900px;
      margin: 0 auto;

      .footer-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 12px;
      }
    }
  }
}

@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}
</style>
