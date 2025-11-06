/**
 * WebSocket连接工具类
 */
import { useAuthStore } from '@/stores/auth'

export interface WebSocketOptions {
  onOpen?: () => void
  onMessage?: (data: any) => void
  onError?: (error: Event) => void
  onClose?: () => void
  reconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private options: WebSocketOptions
  private reconnectAttempts = 0
  private shouldReconnect = true

  constructor(url: string, options: WebSocketOptions = {}) {
    this.url = url
    this.options = {
      reconnect: true,
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      ...options,
    }
  }

  /**
   * 连接WebSocket
   */
  connect(): void {
    // 添加token到URL
    const authStore = useAuthStore()
    const token = authStore.token

    if (!token) {
      console.error('No auth token found')
      return
    }

    const wsUrl = `${this.url}?token=${encodeURIComponent(token)}`

    try {
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket connected:', this.url)
        this.reconnectAttempts = 0
        this.options.onOpen?.()
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.options.onMessage?.(data)
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.options.onError?.(error)
      }

      this.ws.onclose = () => {
        console.log('WebSocket closed')
        this.options.onClose?.()

        // 自动重连
        if (
          this.shouldReconnect &&
          this.options.reconnect &&
          this.reconnectAttempts < (this.options.maxReconnectAttempts || 5)
        ) {
          this.reconnectAttempts++
          console.log(
            `Reconnecting... (${this.reconnectAttempts}/${this.options.maxReconnectAttempts})`
          )
          setTimeout(() => {
            this.connect()
          }, this.options.reconnectInterval)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
    }
  }

  /**
   * 发送消息
   */
  send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      this.ws.send(message)
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  /**
   * 关闭连接
   */
  close(): void {
    this.shouldReconnect = false
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * 获取连接状态
   */
  get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }

  /**
   * 是否已连接
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

/**
 * 创建WebSocket连接
 */
export function createWebSocket(path: string, options?: WebSocketOptions): WebSocketClient {
  // 构建WebSocket URL
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'

  // 使用专门的WebSocket URL配置，或者从API URL中提取host
  let host: string
  const wsUrl = import.meta.env.VITE_WS_URL
  const apiUrl = import.meta.env.VITE_API_BASE_URL

  if (wsUrl) {
    // 如果配置了WebSocket URL，直接使用
    host = wsUrl.replace(/^wss?:\/\//, '')
  } else if (apiUrl) {
    // 从API URL中提取host（去掉协议和路径）
    host = apiUrl.replace(/^https?:\/\//, '').replace(/\/.*$/, '')
  } else {
    // 默认值
    host = 'localhost:8000'
  }

  const url = `${protocol}//${host}${path}`

  return new WebSocketClient(url, options)
}
