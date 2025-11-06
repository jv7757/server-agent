<template>
  <div class="command-execute">
    <!-- 命令执行表单 -->
    <el-card shadow="never" class="execute-card">
      <template #header>
        <div class="card-header">
          <el-icon><Terminal /></el-icon>
          <span>{{ $t('execute.title') }}</span>
        </div>
      </template>

      <el-form :model="executeForm" label-position="top" size="large">
        <!-- 服务器选择 -->
        <el-form-item :label="$t('execute.selectServer')" required>
          <el-select
            v-model="executeForm.server_id"
            filterable
            :placeholder="$t('execute.serverPlaceholder')"
            style="width: 100%"
            @change="handleServerChange"
          >
            <el-option
              v-for="server in servers"
              :key="server.id"
              :label="`${server.name} (${server.host})`"
              :value="server.id"
            >
              <span style="float: left">{{ server.name }}</span>
              <span style="float: right; color: var(--el-text-color-secondary); font-size: 13px">
                {{ server.host }}
              </span>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- 命令输入 -->
        <el-form-item :label="$t('execute.command')" required>
          <el-input
            v-model="executeForm.command"
            type="textarea"
            :rows="4"
            :placeholder="$t('execute.commandPlaceholder')"
            @keydown.ctrl.enter="handleExecute"
          />
          <div class="command-tips">
            <el-text type="info" size="small">
              {{ $t('execute.commandTips') }}
            </el-text>
          </div>
        </el-form-item>

        <!-- 高级选项 -->
        <el-collapse v-model="advancedOpen" class="advanced-options">
          <el-collapse-item :title="$t('execute.advancedOptions')" name="advanced">
            <el-form-item :label="$t('execute.timeout')">
              <el-input-number
                v-model="executeForm.timeout"
                :min="1"
                :max="3600"
                :step="10"
              />
              <el-text type="info" size="small" style="margin-left: 10px">
                {{ $t('execute.timeoutUnit') }}
              </el-text>
            </el-form-item>

            <el-form-item :label="$t('execute.workingDirectory')">
              <el-input v-model="executeForm.working_directory" />
            </el-form-item>

            <el-form-item>
              <el-checkbox v-model="executeForm.sudo">
                {{ $t('execute.useSudo') }}
              </el-checkbox>
            </el-form-item>
          </el-collapse-item>
        </el-collapse>

        <!-- 操作按钮 -->
        <el-form-item>
          <el-space>
            <el-button
              type="primary"
              :icon="VideoPlay"
              :loading="executeStore.isExecuting"
              :disabled="!canExecute"
              @click="handleExecute"
            >
              {{ $t('execute.execute') }}
            </el-button>
            <el-button
              :icon="Check"
              :disabled="!executeForm.server_id || !executeForm.command"
              @click="handleValidate"
            >
              {{ $t('execute.validate') }}
            </el-button>
            <el-button :icon="Delete" @click="handleClear">
              {{ $t('common.clear') }}
            </el-button>
          </el-space>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 执行结果 -->
    <el-card v-if="executeStore.currentResult" shadow="never" class="result-card">
      <template #header>
        <div class="card-header">
          <el-icon><Document /></el-icon>
          <span>{{ $t('execute.result') }}</span>
          <el-tag
            :type="resultType"
            size="small"
            style="margin-left: 10px"
          >
            {{ $t('execute.exitCode') }}: {{ executeStore.currentResult.exit_code }}
          </el-tag>
        </div>
      </template>

      <div class="result-content">
        <!-- 标准输出 -->
        <div v-if="executeStore.currentResult.output" class="output-section">
          <div class="output-header">
            <el-text type="success">{{ $t('execute.stdout') }}</el-text>
            <el-button
              link
              :icon="CopyDocument"
              @click="copyToClipboard(executeStore.currentResult.output)"
            >
              {{ $t('common.copy') }}
            </el-button>
          </div>
          <pre class="output-pre">{{ executeStore.currentResult.output }}</pre>
        </div>

        <!-- 标准错误 -->
        <div v-if="executeStore.currentResult.error_output" class="output-section">
          <div class="output-header">
            <el-text type="danger">{{ $t('execute.stderr') }}</el-text>
            <el-button
              link
              :icon="CopyDocument"
              @click="copyToClipboard(executeStore.currentResult.error_output)"
            >
              {{ $t('common.copy') }}
            </el-button>
          </div>
          <pre class="output-pre error">{{ executeStore.currentResult.error_output }}</pre>
        </div>

        <!-- 执行信息 -->
        <el-descriptions :column="2" border size="small" class="result-meta">
          <el-descriptions-item :label="$t('execute.executionTime')">
            {{ executeStore.currentResult.execution_time?.toFixed(2) }}s
          </el-descriptions-item>
          <el-descriptions-item :label="$t('execute.timestamp')">
            {{ formatDate(executeStore.currentResult.executed_at) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

    <!-- 历史记录 -->
    <el-card shadow="never" class="history-card">
      <template #header>
        <div class="card-header">
          <el-icon><Clock /></el-icon>
          <span>{{ $t('execute.history') }}</span>
          <el-button
            link
            :icon="Refresh"
            @click="loadHistory"
            style="margin-left: auto"
          >
            {{ $t('common.refresh') }}
          </el-button>
        </div>
      </template>

      <el-table
        v-loading="executeStore.isLoadingHistory"
        :data="executeStore.history"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="action" :label="$t('execute.command')" min-width="200">
          <template #default="{ row }">
            <el-text class="command-text" truncated>
              {{ getCommandFromDetails(row) }}
            </el-text>
          </template>
        </el-table-column>

        <el-table-column prop="resource_type" :label="$t('execute.server')" width="150">
          <template #default="{ row }">
            {{ getServerNameFromDetails(row) }}
          </template>
        </el-table-column>

        <el-table-column :label="$t('execute.status')" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row)" size="small">
              {{ getStatusText(row) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" :label="$t('common.time')" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column :label="$t('common.actions')" width="100" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleViewDetail(row)">
              {{ $t('common.view') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="executeStore.historyTotal"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadHistory"
          @current-change="loadHistory"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      :title="$t('execute.detail')"
      width="800px"
      destroy-on-close
    >
      <el-descriptions v-if="currentDetail" :column="1" border>
        <el-descriptions-item :label="$t('execute.command')">
          <pre>{{ getCommandFromDetails(currentDetail) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('execute.stdout')">
          <pre class="detail-output">{{ currentDetail.details?.output || 'N/A' }}</pre>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('execute.stderr')">
          <pre class="detail-output error">{{ currentDetail.details?.error_output || 'N/A' }}</pre>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('execute.exitCode')">
          {{ currentDetail.details?.exit_code }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('execute.executionTime')">
          {{ currentDetail.details?.execution_time?.toFixed(2) }}s
        </el-descriptions-item>
        <el-descriptions-item :label="$t('common.time')">
          {{ formatDate(currentDetail.created_at) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
  Terminal,
  VideoPlay,
  Check,
  Delete,
  Document,
  CopyDocument,
  Clock,
  Refresh,
} from '@element-plus/icons-vue'
import { useExecuteStore } from '@/stores/execute'
import { useServersStore } from '@/stores/servers'
import type { CommandExecuteRequest, CommandHistory } from '@/types/api'

const { t } = useI18n()
const executeStore = useExecuteStore()
const serversStore = useServersStore()

// Form data
const executeForm = ref<CommandExecuteRequest>({
  server_id: '',
  command: '',
  timeout: 30,
  working_directory: undefined,
  sudo: false,
})

const advancedOpen = ref<string[]>([])
const servers = computed(() => serversStore.servers)
const canExecute = computed(
  () => executeForm.value.server_id && executeForm.value.command.trim()
)

// Result display
const resultType = computed(() => {
  const exitCode = executeStore.currentResult?.exit_code
  if (exitCode === undefined) return 'info'
  return exitCode === 0 ? 'success' : 'danger'
})

// History
const currentPage = ref(1)
const pageSize = ref(20)
const detailVisible = ref(false)
const currentDetail = ref<CommandHistory | null>(null)

// Actions

const handleServerChange = () => {
  // 可以根据服务器加载默认工作目录等
}

const handleExecute = async () => {
  if (!canExecute.value) return

  const success = await executeStore.execute(executeForm.value)
  if (success) {
    loadHistory()
  }
}

const handleValidate = async () => {
  const isSafe = await executeStore.validate(
    executeForm.value.server_id,
    executeForm.value.command
  )

  if (isSafe) {
    ElMessage.success(t('execute.commandSafe'))
  }
}

const handleClear = () => {
  executeForm.value.command = ''
  executeStore.clearResult()
}

const loadHistory = async () => {
  await executeStore.fetchHistory(currentPage.value, pageSize.value)
}

const handleViewDetail = async (row: CommandHistory) => {
  const detail = await executeStore.fetchDetail(row.id)
  if (detail) {
    currentDetail.value = detail
    detailVisible.value = true
  }
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(t('common.copySuccess'))
  } catch {
    ElMessage.error(t('common.copyFailed'))
  }
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString()
}

const getCommandFromDetails = (row: CommandHistory) => {
  return row.details?.command || row.action || 'N/A'
}

const getServerNameFromDetails = (row: CommandHistory) => {
  return row.details?.server_name || 'N/A'
}

const getStatusType = (row: CommandHistory) => {
  const exitCode = row.details?.exit_code
  if (exitCode === undefined) return 'info'
  return exitCode === 0 ? 'success' : 'danger'
}

const getStatusText = (row: CommandHistory) => {
  const exitCode = row.details?.exit_code
  if (exitCode === undefined) return t('common.unknown')
  return exitCode === 0 ? t('common.success') : t('common.failed')
}

// Lifecycle
onMounted(async () => {
  await serversStore.fetchServers()
  await loadHistory()
})
</script>

<style scoped lang="scss">
.command-execute {
  padding: 20px;

  .execute-card,
  .result-card,
  .history-card {
    margin-bottom: 20px;
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    font-size: 16px;
  }

  .command-tips {
    margin-top: 8px;
  }

  .advanced-options {
    margin-bottom: 20px;
  }

  .result-content {
    .output-section {
      margin-bottom: 20px;

      .output-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        padding: 8px;
        background: var(--el-fill-color-lighter);
        border-radius: 4px;
      }

      .output-pre {
        padding: 12px;
        background: #1e1e1e;
        color: #d4d4d4;
        border-radius: 4px;
        overflow-x: auto;
        font-family: 'Courier New', Courier, monospace;
        font-size: 13px;
        line-height: 1.5;
        margin: 0;

        &.error {
          background: #2d1e1e;
          color: #f48771;
        }
      }
    }

    .result-meta {
      margin-top: 20px;
    }
  }

  .command-text {
    font-family: 'Courier New', Courier, monospace;
    font-size: 13px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .detail-output {
    max-height: 300px;
    overflow-y: auto;
    padding: 12px;
    background: #1e1e1e;
    color: #d4d4d4;
    border-radius: 4px;
    font-family: 'Courier New', Courier, monospace;
    font-size: 13px;
    line-height: 1.5;
    margin: 0;

    &.error {
      background: #2d1e1e;
      color: #f48771;
    }
  }
}
</style>
