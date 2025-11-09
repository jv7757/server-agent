<template>
  <div class="terminal-container">
    <div class="terminal-header">
      <div class="header-left">
        <el-icon><Monitor /></el-icon>
        <span>{{ title }}</span>
      </div>
      <div class="header-right">
        <el-tag v-if="connected" type="success" size="small">
          <el-icon><CircleCheck /></el-icon>
          已连接
        </el-tag>
        <el-tag v-else type="info" size="small">
          <el-icon><CircleClose /></el-icon>
          未连接
        </el-tag>
        <el-button :icon="FullScreen" circle size="small" @click="toggleFullscreen" />
        <el-button :icon="Close" circle size="small" @click="handleClose" />
      </div>
    </div>
    <div ref="terminalRef" class="terminal-body"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Monitor, FullScreen, Close, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import { WebLinksAddon } from 'xterm-addon-web-links'
import 'xterm/css/xterm.css'
import { createWebSocket, WebSocketClient } from '@/utils/websocket'

interface Props {
  serverId: string
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Terminal',
})

const emit = defineEmits<{
  close: []
}>()

// State
const terminalRef = ref<HTMLElement>()
const connected = ref(false)

let terminal: Terminal | null = null
let fitAddon: FitAddon | null = null
let ws: WebSocketClient | null = null

// 初始化Terminal
const initTerminal = () => {
  if (!terminalRef.value) {
    return
  }

  // 创建Terminal实例
  terminal = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme: {
      background: '#1e1e1e',
      foreground: '#d4d4d4',
      cursor: '#d4d4d4',
      black: '#000000',
      red: '#cd3131',
      green: '#0dbc79',
      yellow: '#e5e510',
      blue: '#2472c8',
      magenta: '#bc3fbc',
      cyan: '#11a8cd',
      white: '#e5e5e5',
      brightBlack: '#666666',
      brightRed: '#f14c4c',
      brightGreen: '#23d18b',
      brightYellow: '#f5f543',
      brightBlue: '#3b8eea',
      brightMagenta: '#d670d6',
      brightCyan: '#29b8db',
      brightWhite: '#ffffff',
    },
    rows: 24,
    cols: 80,
  })

  // 添加插件
  fitAddon = new FitAddon()
  terminal.loadAddon(fitAddon)
  terminal.loadAddon(new WebLinksAddon())

  // 挂载到DOM
  terminal.open(terminalRef.value)
  fitAddon.fit()

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)

  // 监听用户输入
  terminal.onData(data => {
    if (ws && ws.isConnected) {
      ws.send({
        type: 'input',
        data: data,
      })
    }
  })
}

// WebSocket连接
const connectWebSocket = () => {
  const path = `/api/v1/ws/terminal/${props.serverId}`

  ws = createWebSocket(path, {
    onOpen: () => {
      connected.value = true
      terminal?.writeln('\x1b[32m正在连接到服务器...\x1b[0m')
    },
    onMessage: data => {
      if (data.type === 'output') {
        terminal?.write(data.data)
      } else if (data.type === 'error') {
        terminal?.writeln(`\r\n\x1b[31m错误: ${data.message}\x1b[0m\r\n`)
        ElMessage.error(data.message)
      }
    },
    onError: error => {
      console.error('Terminal WebSocket error:', error)
      ElMessage.error('连接失败')
    },
    onClose: () => {
      connected.value = false
      terminal?.writeln('\r\n\x1b[33m连接已关闭\x1b[0m')
    },
    reconnect: true,
    maxReconnectAttempts: 3,
  })

  ws.connect()
}

// 调整终端大小
const handleResize = () => {
  if (fitAddon && terminal) {
    fitAddon.fit()
    // 通知服务器终端大小改变
    if (ws && ws.isConnected) {
      ws.send({
        type: 'resize',
        rows: terminal.rows,
        cols: terminal.cols,
      })
    }
  }
}

// 全屏切换
const toggleFullscreen = () => {
  if (!terminalRef.value) {
    return
  }

  const container = terminalRef.value.parentElement
  if (!container) {
    return
  }

  if (!document.fullscreenElement) {
    container.requestFullscreen().then(() => {
      setTimeout(() => handleResize(), 100)
    })
  } else {
    document.exitFullscreen().then(() => {
      setTimeout(() => handleResize(), 100)
    })
  }
}

// 关闭Terminal
const handleClose = () => {
  emit('close')
}

// 清理
const cleanup = () => {
  window.removeEventListener('resize', handleResize)
  ws?.close()
  terminal?.dispose()
}

// 生命周期
onMounted(() => {
  initTerminal()
  connectWebSocket()
})

onBeforeUnmount(() => {
  cleanup()
})

// 监听serverId变化
watch(
  () => props.serverId,
  () => {
    cleanup()
    initTerminal()
    connectWebSocket()
  }
)
</script>

<style scoped lang="scss">
.terminal-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
  border-radius: 4px;
  overflow: hidden;

  .terminal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 16px;
    background: #2d2d2d;
    border-bottom: 1px solid #3d3d3d;

    .header-left {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #d4d4d4;
      font-size: 14px;
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }

  .terminal-body {
    flex: 1;
    padding: 8px;
    overflow: hidden;

    :deep(.xterm) {
      height: 100%;
    }

    :deep(.xterm-viewport) {
      overflow-y: auto;
    }
  }
}

// 全屏样式
:fullscreen .terminal-container {
  .terminal-body {
    height: calc(100vh - 48px);
  }
}
</style>
