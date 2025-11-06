<template>
  <div class="server-terminal">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon><Monitor /></el-icon>
            <span>SSH Terminal</span>
          </div>
          <div class="header-right">
            <el-select
              v-model="selectedServerId"
              filterable
              placeholder="选择服务器"
              style="width: 300px"
              @change="handleServerChange"
            >
              <el-option
                v-for="server in servers"
                :key="server.id"
                :label="`${server.name} (${server.host})`"
                :value="server.id"
              >
                <span style="float: left">{{ server.name }}</span>
                <span
                  style="float: right; color: var(--el-text-color-secondary); font-size: 13px"
                >
                  {{ server.host }}
                </span>
              </el-option>
            </el-select>
          </div>
        </div>
      </template>

      <div class="terminal-wrapper">
        <Terminal
          v-if="selectedServerId"
          :key="selectedServerId"
          :server-id="selectedServerId"
          :title="`Terminal - ${currentServerName}`"
        />
        <el-empty
          v-else
          description="请选择一个服务器开始SSH连接"
          :image-size="200"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Monitor } from '@element-plus/icons-vue'
import Terminal from '@/components/Terminal.vue'
import { useServersStore } from '@/stores/servers'

const route = useRoute()
const serversStore = useServersStore()

const selectedServerId = ref<string>('')

const servers = computed(() => serversStore.servers)
const currentServerName = computed(() => {
  const server = servers.value.find((s) => s.id === selectedServerId.value)
  return server?.name || 'Unknown'
})

const handleServerChange = () => {
  // 服务器切换
}

onMounted(async () => {
  // 加载服务器列表
  await serversStore.fetchServers()

  // 如果URL中有server_id参数，自动选择
  const serverId = route.query.server_id as string
  if (serverId && servers.value.some((s) => s.id === serverId)) {
    selectedServerId.value = serverId
  } else if (servers.value.length > 0) {
    // 默认选择第一个
    selectedServerId.value = servers.value[0].id
  }
})
</script>

<style scoped lang="scss">
.server-terminal {
  padding: 20px;
  height: calc(100vh - 80px);

  .el-card {
    height: 100%;
    display: flex;
    flex-direction: column;

    :deep(.el-card__body) {
      flex: 1;
      padding: 0;
      overflow: hidden;
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-left {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      font-size: 16px;
    }
  }

  .terminal-wrapper {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
}
</style>
