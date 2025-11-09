<template>
  <div class="audit-logs">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">审计日志</span>
          <el-button :icon="Refresh" @click="loadLogs">刷新</el-button>
        </div>
      </template>

      <!-- 筛选表单 -->
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="搜索">
          <el-input
            v-model="filters.search"
            placeholder="用户名/服务器名/操作"
            clearable
            style="width: 240px"
            @clear="handleSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="操作类型">
          <el-select
            v-model="filters.action"
            placeholder="所有操作"
            clearable
            style="width: 180px"
            @change="handleSearch"
          >
            <el-option label="执行命令" value="execute_command" />
            <el-option label="创建服务器" value="create_server" />
            <el-option label="更新服务器" value="update_server" />
            <el-option label="删除服务器" value="delete_server" />
            <el-option label="授予权限" value="grant_permission" />
            <el-option label="撤销权限" value="revoke_permission" />
          </el-select>
        </el-form-item>

        <el-form-item label="资源类型">
          <el-select
            v-model="filters.resource_type"
            placeholder="所有资源"
            clearable
            style="width: 160px"
            @change="handleSearch"
          >
            <el-option label="服务器" value="server" />
            <el-option label="用户" value="user" />
            <el-option label="权限" value="permission" />
            <el-option label="命令" value="command" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 日志表格 -->
      <el-table
        v-loading="loading"
        :data="logs"
        stripe
        style="width: 100%"
        @row-click="handleRowClick"
      >
        <el-table-column prop="id" label="ID" width="80" />

        <el-table-column prop="username" label="用户" width="140">
          <template #default="{ row }">
            <el-tag v-if="row.username" size="small">
              {{ row.username }}
            </el-tag>
            <span v-else class="text-muted">未知</span>
          </template>
        </el-table-column>

        <el-table-column prop="action" label="操作" width="160">
          <template #default="{ row }">
            <el-tag :type="getActionType(row.action)" size="small">
              {{ formatAction(row.action) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="resource_type" label="资源类型" width="120">
          <template #default="{ row }">
            <span v-if="row.resource_type">{{ row.resource_type }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="server_name" label="服务器" width="180">
          <template #default="{ row }">
            <span v-if="row.server_name">{{ row.server_name }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="ip_address" label="IP 地址" width="140">
          <template #default="{ row }">
            <span v-if="row.ip_address">{{ row.ip_address }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="handleViewDetail(row)"> 详情 </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="审计日志详情" width="700px" destroy-on-close>
      <el-descriptions v-if="selectedLog" :column="2" border>
        <el-descriptions-item label="日志 ID">
          {{ selectedLog.id }}
        </el-descriptions-item>

        <el-descriptions-item label="用户">
          {{ selectedLog.username || '未知' }}
        </el-descriptions-item>

        <el-descriptions-item label="操作类型">
          <el-tag :type="getActionType(selectedLog.action)" size="small">
            {{ formatAction(selectedLog.action) }}
          </el-tag>
        </el-descriptions-item>

        <el-descriptions-item label="资源类型">
          {{ selectedLog.resource_type || '-' }}
        </el-descriptions-item>

        <el-descriptions-item label="服务器">
          {{ selectedLog.server_name || '-' }}
        </el-descriptions-item>

        <el-descriptions-item label="IP 地址">
          {{ selectedLog.ip_address || '-' }}
        </el-descriptions-item>

        <el-descriptions-item label="时间" :span="2">
          {{ formatDate(selectedLog.created_at) }}
        </el-descriptions-item>

        <el-descriptions-item label="详细信息" :span="2">
          <el-scrollbar max-height="300px">
            <pre class="details-content">{{ formatDetails(selectedLog.details) }}</pre>
          </el-scrollbar>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import * as auditApi from '@/api/audit'
import type { AuditLog } from '@/api/audit'

// State
const loading = ref(false)
const logs = ref<AuditLog[]>([])
const detailVisible = ref(false)
const selectedLog = ref<AuditLog | null>(null)

const filters = reactive({
  search: '',
  action: '',
  resource_type: '',
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0,
})

// Methods
const loadLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      search: filters.search || undefined,
      action: filters.action || undefined,
      resource_type: filters.resource_type || undefined,
    }

    const response = await auditApi.getAuditLogs(params)
    logs.value = response.items
    pagination.total = response.total
  } catch (error: any) {
    console.error('加载审计日志失败:', error)
    ElMessage.error(error.response?.data?.detail || '加载审计日志失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadLogs()
}

const handleReset = () => {
  filters.search = ''
  filters.action = ''
  filters.resource_type = ''
  pagination.page = 1
  loadLogs()
}

const handlePageChange = () => {
  loadLogs()
}

const handleSizeChange = () => {
  pagination.page = 1
  loadLogs()
}

const handleRowClick = (row: AuditLog) => {
  handleViewDetail(row)
}

const handleViewDetail = (row: AuditLog) => {
  selectedLog.value = row
  detailVisible.value = true
}

const getActionType = (action: string): string => {
  const actionMap: Record<string, string> = {
    execute_command: 'warning',
    create_server: 'success',
    update_server: 'info',
    delete_server: 'danger',
    grant_permission: 'success',
    revoke_permission: 'warning',
  }
  return actionMap[action] || ''
}

const formatAction = (action: string): string => {
  const actionMap: Record<string, string> = {
    execute_command: '执行命令',
    create_server: '创建服务器',
    update_server: '更新服务器',
    delete_server: '删除服务器',
    grant_permission: '授予权限',
    revoke_permission: '撤销权限',
  }
  return actionMap[action] || action
}

const formatDate = (dateString: string): string =>
  new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })

const formatDetails = (details: Record<string, any> | null): string => {
  if (!details) {
    return '无'
  }
  return JSON.stringify(details, null, 2)
}

// Lifecycle
onMounted(() => {
  loadLogs()
})
</script>

<style scoped lang="scss">
.audit-logs {
  padding: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .title {
      font-size: 18px;
      font-weight: 600;
    }
  }

  .filter-form {
    margin-bottom: 20px;
  }

  .text-muted {
    color: #909399;
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .details-content {
    font-size: 13px;
    line-height: 1.5;
    margin: 0;
    padding: 10px;
    background: #f5f7fa;
    border-radius: 4px;
    overflow-x: auto;
  }
}
</style>
