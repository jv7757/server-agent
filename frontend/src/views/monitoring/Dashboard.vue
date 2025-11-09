<template>
  <div class="monitoring-dashboard">
    <!-- 服务器选择 -->
    <el-card shadow="never" class="server-select-card">
      <el-select
        v-model="selectedServerId"
        filterable
        placeholder="选择服务器"
        style="width: 100%"
        size="large"
        @change="handleServerChange"
      >
        <el-option
          v-for="server in servers"
          :key="server.id"
          :label="`${server.name} (${server.host})`"
          :value="server.id"
        >
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span>{{ server.name }}</span>
            <el-tag :type="server.status === 'online' ? 'success' : 'danger'" size="small">
              {{ server.status }}
            </el-tag>
          </div>
        </el-option>
      </el-select>
    </el-card>

    <template v-if="selectedServerId">
      <!-- 实时状态指标 -->
      <div class="metrics-grid">
        <el-card shadow="never" class="metric-card">
          <div class="metric-content">
            <div class="metric-icon cpu">
              <el-icon><Cpu /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-label">CPU使用率</div>
              <div class="metric-value">{{ currentMetrics.cpu?.usage?.toFixed(1) || 0 }}%</div>
              <div class="metric-detail">{{ currentMetrics.cpu?.cores || 0 }} 核心</div>
            </div>
          </div>
          <el-progress
            :percentage="currentMetrics.cpu?.usage || 0"
            :color="getProgressColor(currentMetrics.cpu?.usage || 0)"
            :show-text="false"
          />
        </el-card>

        <el-card shadow="never" class="metric-card">
          <div class="metric-content">
            <div class="metric-icon memory">
              <el-icon><Memo /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-label">内存使用率</div>
              <div class="metric-value">{{ currentMetrics.memory?.usage?.toFixed(1) || 0 }}%</div>
              <div class="metric-detail">
                {{ formatBytes(currentMetrics.memory?.used || 0) }} /
                {{ formatBytes(currentMetrics.memory?.total || 0) }}
              </div>
            </div>
          </div>
          <el-progress
            :percentage="currentMetrics.memory?.usage || 0"
            :color="getProgressColor(currentMetrics.memory?.usage || 0)"
            :show-text="false"
          />
        </el-card>

        <el-card shadow="never" class="metric-card">
          <div class="metric-content">
            <div class="metric-icon disk">
              <el-icon><Files /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-label">磁盘使用率</div>
              <div class="metric-value">{{ currentMetrics.disk?.usage?.toFixed(1) || 0 }}%</div>
              <div class="metric-detail">
                {{ currentMetrics.disk?.used?.toFixed(1) || 0 }} GB /
                {{ currentMetrics.disk?.total?.toFixed(1) || 0 }} GB
              </div>
            </div>
          </div>
          <el-progress
            :percentage="currentMetrics.disk?.usage || 0"
            :color="getProgressColor(currentMetrics.disk?.usage || 0)"
            :show-text="false"
          />
        </el-card>

        <el-card shadow="never" class="metric-card">
          <div class="metric-content">
            <div class="metric-icon network">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-label">网络流量</div>
              <div class="metric-value">
                {{ formatBytes(currentMetrics.network?.bytes_sent || 0) }}
              </div>
              <div class="metric-detail">
                ↑ {{ formatBytes(currentMetrics.network?.bytes_sent || 0) }} / ↓
                {{ formatBytes(currentMetrics.network?.bytes_recv || 0) }}
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 连接状态 -->
      <el-card shadow="never" class="status-card">
        <div class="status-info">
          <el-tag :type="wsConnected ? 'success' : 'info'" size="large">
            <el-icon v-if="wsConnected"><Connection /></el-icon>
            <el-icon v-else><Loading /></el-icon>
            {{ wsConnected ? '实时连接' : '连接中...' }}
          </el-tag>
          <span class="update-time"> 最后更新: {{ lastUpdateTime }} </span>
          <span class="uptime"> 运行时间: {{ formatUptime(currentMetrics.uptime || 0) }} </span>
          <el-button
            type="primary"
            :icon="Refresh"
            :loading="isCollecting"
            style="margin-left: auto"
            @click="handleCollectMetrics"
          >
            {{ isCollecting ? '采集中...' : '立即采集' }}
          </el-button>
        </div>
      </el-card>

      <!-- 历史图表 -->
      <el-card shadow="never" class="chart-card">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span>历史趋势</span>
            <el-button-group>
              <el-button
                v-for="period in timePeriods"
                :key="period.value"
                :type="selectedPeriod === period.value ? 'primary' : 'default'"
                size="small"
                @click="selectedPeriod = period.value"
              >
                {{ period.label }}
              </el-button>
            </el-button-group>
          </div>
        </template>
        <div ref="chartRef" class="chart-container"></div>
      </el-card>
    </template>

    <el-empty v-else description="请选择一个服务器查看监控数据" :image-size="200" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Cpu, Memo, Files, Connection, Loading, Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { useServersStore } from '@/stores/servers'
import { createWebSocket, WebSocketClient } from '@/utils/websocket'
import * as metricsApi from '@/api/metrics'

const serversStore = useServersStore()

// State
const selectedServerId = ref<string>('')
const wsConnected = ref(false)
const currentMetrics = ref<any>({})
const lastUpdateTime = ref<string>('--')
const selectedPeriod = ref('1h')
const chartRef = ref<HTMLElement>()
const isCollecting = ref(false)

let ws: WebSocketClient | null = null
let chart: ECharts | null = null

const servers = computed(() => serversStore.servers)

const timePeriods = [
  { label: '1小时', value: '1h' },
  { label: '6小时', value: '6h' },
  { label: '24小时', value: '24h' },
  { label: '7天', value: '7d' },
]

// WebSocket连接
const connectWebSocket = () => {
  if (!selectedServerId.value) {
    return
  }

  // 断开旧连接
  ws?.close()

  const path = `/api/v1/ws/monitoring/${selectedServerId.value}`

  ws = createWebSocket(path, {
    onOpen: () => {
      wsConnected.value = true
      console.log('Monitoring WebSocket connected')
    },
    onMessage: data => {
      if (data.type === 'metrics') {
        currentMetrics.value = data.data
        lastUpdateTime.value = new Date().toLocaleTimeString()
        updateChart(data.data)
      } else if (data.type === 'connected') {
        ElMessage.success(data.message)
      } else if (data.type === 'error') {
        ElMessage.error(data.message)
      }
    },
    onError: () => {
      wsConnected.value = false
      ElMessage.error('监控连接失败')
    },
    onClose: () => {
      wsConnected.value = false
    },
    reconnect: true,
    maxReconnectAttempts: 5,
  })

  ws.connect()
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value) {
    return
  }

  chart = echarts.init(chartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    legend: {
      data: ['CPU', '内存', '磁盘'],
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'time',
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: {
        formatter: '{value}%',
      },
    },
    series: [
      {
        name: 'CPU',
        type: 'line',
        smooth: true,
        data: [],
        itemStyle: { color: '#409EFF' },
      },
      {
        name: '内存',
        type: 'line',
        smooth: true,
        data: [],
        itemStyle: { color: '#67C23A' },
      },
      {
        name: '磁盘',
        type: 'line',
        smooth: true,
        data: [],
        itemStyle: { color: '#E6A23C' },
      },
    ],
  }

  chart.setOption(option)

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
}

// 更新图表
const updateChart = (metrics: any) => {
  if (!chart) {
    return
  }

  const now = new Date()
  const option = chart.getOption() as any

  // 添加新数据点
  option.series[0].data.push([now, metrics.cpu?.usage || 0])
  option.series[1].data.push([now, metrics.memory?.usage || 0])
  option.series[2].data.push([now, metrics.disk?.usage || 0])

  // 限制数据点数量（最多保留60个点）
  if (option.series[0].data.length > 60) {
    option.series.forEach((series: any) => series.data.shift())
  }

  chart.setOption(option)
}

// 格式化字节
const formatBytes = (bytes: number): string => {
  if (bytes === 0) {
    return '0 B'
  }
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}

// 格式化运行时间
const formatUptime = (seconds: number): string => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  const parts = []
  if (days > 0) {
    parts.push(`${days}天`)
  }
  if (hours > 0) {
    parts.push(`${hours}小时`)
  }
  if (minutes > 0) {
    parts.push(`${minutes}分钟`)
  }

  return parts.join(' ') || '0分钟'
}

// 获取进度条颜色
const getProgressColor = (value: number): string => {
  if (value >= 90) {
    return '#F56C6C'
  }
  if (value >= 70) {
    return '#E6A23C'
  }
  return '#67C23A'
}

// 调整图表大小
const handleResize = () => {
  chart?.resize()
}

// 服务器切换
const handleServerChange = () => {
  currentMetrics.value = {}
  lastUpdateTime.value = '--'
  connectWebSocket()
  nextTick(() => {
    chart?.clear()
  })
  // 切换服务器后自动采集一次
  handleCollectMetrics()
}

// 手动采集监控数据
const handleCollectMetrics = async () => {
  if (!selectedServerId.value || isCollecting.value) {
    return
  }

  isCollecting.value = true
  try {
    await metricsApi.collectMetrics(selectedServerId.value)
    ElMessage.success('监控数据采集成功')
    // 采集成功后，等待1秒让数据写入数据库，然后WebSocket会自动推送新数据
  } catch (error: any) {
    console.error('Failed to collect metrics:', error)
    ElMessage.error(error.response?.data?.detail || '采集监控数据失败')
  } finally {
    isCollecting.value = false
  }
}

// 清理
const cleanup = () => {
  window.removeEventListener('resize', handleResize)
  ws?.close()
  chart?.dispose()
}

// 生命周期
onMounted(async () => {
  await serversStore.fetchServers()

  if (servers.value.length > 0) {
    selectedServerId.value = servers.value[0].id
    connectWebSocket()
    // 首次加载时自动采集一次监控数据
    handleCollectMetrics()
  }

  nextTick(() => {
    initChart()
  })
})

onBeforeUnmount(() => {
  cleanup()
})
</script>

<style scoped lang="scss">
.monitoring-dashboard {
  padding: 20px;

  .server-select-card {
    margin-bottom: 20px;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-bottom: 20px;

    .metric-card {
      .metric-content {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 12px;

        .metric-icon {
          width: 56px;
          height: 56px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          color: white;

          &.cpu {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }

          &.memory {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          }

          &.disk {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
          }

          &.network {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
          }
        }

        .metric-info {
          flex: 1;

          .metric-label {
            font-size: 13px;
            color: var(--el-text-color-secondary);
            margin-bottom: 4px;
          }

          .metric-value {
            font-size: 24px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin-bottom: 2px;
          }

          .metric-detail {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
      }
    }
  }

  .status-card {
    margin-bottom: 20px;

    .status-info {
      display: flex;
      align-items: center;
      gap: 20px;

      .update-time,
      .uptime {
        font-size: 14px;
        color: var(--el-text-color-secondary);
      }
    }
  }

  .chart-card {
    .chart-container {
      height: 400px;
    }
  }
}
</style>
