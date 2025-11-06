<template>
  <div class="server-list">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <h3>{{ $t('servers.title') }}</h3>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            {{ $t('servers.create') }}
          </el-button>
        </div>
      </template>

      <!-- 搜索和筛选 -->
      <div class="filter-bar">
        <el-input
          v-model="searchKeyword"
          :placeholder="$t('servers.searchPlaceholder')"
          style="width: 300px"
          clearable
          @clear="loadServers"
          @keyup.enter="loadServers"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="statusFilter"
          :placeholder="$t('servers.statusFilter')"
          style="width: 150px"
          clearable
          @change="loadServers"
        >
          <el-option label="Online" value="online" />
          <el-option label="Offline" value="offline" />
          <el-option label="Error" value="error" />
          <el-option label="Unknown" value="unknown" />
        </el-select>

        <el-button @click="loadServers">
          <el-icon><Refresh /></el-icon>
          {{ $t('common.refresh') }}
        </el-button>
      </div>

      <!-- 服务器列表 -->
      <el-table
        v-loading="serversStore.isLoading"
        :data="serversStore.servers"
        style="width: 100%; margin-top: 20px"
      >
        <el-table-column prop="name" :label="$t('servers.name')" min-width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="goToDetail(row.id)">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column prop="host" :label="$t('servers.host')" min-width="150" />

        <el-table-column prop="port" :label="$t('servers.port')" width="80" />

        <el-table-column prop="status" :label="$t('servers.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="tags" :label="$t('servers.tags')" min-width="150">
          <template #default="{ row }">
            <el-tag
              v-for="tag in row.tags"
              :key="tag"
              size="small"
              style="margin-right: 5px"
            >
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          prop="created_at"
          :label="$t('servers.createdAt')"
          width="180"
        >
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column :label="$t('common.actions')" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="testConnection(row)">
              <el-icon><Link /></el-icon>
              {{ $t('servers.test') }}
            </el-button>
            <el-button size="small" type="primary" @click="editServer(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-popconfirm
              :title="$t('servers.deleteConfirm')"
              @confirm="deleteServer(row)"
            >
              <template #reference>
                <el-button size="small" type="danger">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="serversStore.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadServers"
          @current-change="loadServers"
        />
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? $t('servers.edit') : $t('servers.create')"
      width="600px"
    >
      <el-form
        ref="serverFormRef"
        :model="serverForm"
        :rules="serverRules"
        label-width="120px"
      >
        <el-form-item :label="$t('servers.name')" prop="name">
          <el-input v-model="serverForm.name" />
        </el-form-item>

        <el-form-item :label="$t('servers.host')" prop="host">
          <el-input v-model="serverForm.host" />
        </el-form-item>

        <el-form-item :label="$t('servers.port')" prop="port">
          <el-input-number v-model="serverForm.port" :min="1" :max="65535" />
        </el-form-item>

        <el-form-item :label="$t('servers.sshUsername')" prop="ssh_username">
          <el-input v-model="serverForm.ssh_username" />
        </el-form-item>

        <el-form-item :label="$t('servers.sshPassword')" prop="ssh_password">
          <el-input v-model="serverForm.ssh_password" type="password" show-password />
        </el-form-item>

        <el-form-item :label="$t('servers.description')" prop="description">
          <el-input v-model="serverForm.description" type="textarea" :rows="3" />
        </el-form-item>

        <el-form-item :label="$t('servers.tags')" prop="tags">
          <el-select
            v-model="serverForm.tags"
            multiple
            filterable
            allow-create
            default-first-option
            :placeholder="$t('servers.tagsPlaceholder')"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useServersStore } from '@/stores/servers'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  Plus,
  Search,
  Refresh,
  Link,
  Edit,
  Delete,
} from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import type { Server } from '@/types/api'

const { t } = useI18n()
const router = useRouter()
const serversStore = useServersStore()

// 搜索和筛选
const searchKeyword = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const serverFormRef = ref<FormInstance>()

// 表单数据
const serverForm = reactive({
  id: '',
  name: '',
  host: '',
  port: 22,
  ssh_username: '',
  ssh_password: '',
  description: '',
  tags: [] as string[],
})

// 表单验证规则
const serverRules: FormRules = {
  name: [{ required: true, message: t('servers.nameRequired'), trigger: 'blur' }],
  host: [{ required: true, message: t('servers.hostRequired'), trigger: 'blur' }],
  port: [{ required: true, message: t('servers.portRequired'), trigger: 'blur' }],
  ssh_username: [{ required: true, message: t('servers.sshUsernameRequired'), trigger: 'blur' }],
}

/**
 * 加载服务器列表
 */
const loadServers = async () => {
  await serversStore.fetchServers({
    page: currentPage.value,
    size: pageSize.value,
    search: searchKeyword.value || undefined,
    status: statusFilter.value || undefined,
  })
}

/**
 * 显示创建对话框
 */
const showCreateDialog = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

/**
 * 编辑服务器
 */
const editServer = (server: Server) => {
  isEdit.value = true
  Object.assign(serverForm, {
    id: server.id,
    name: server.name,
    host: server.host,
    port: server.port,
    ssh_username: server.ssh_username,
    description: server.description || '',
    tags: server.tags || [],
    ssh_password: '',
  })
  dialogVisible.value = true
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  if (!serverFormRef.value) return

  await serverFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (isEdit.value) {
          await serversStore.updateServer(serverForm.id, {
            name: serverForm.name,
            host: serverForm.host,
            port: serverForm.port,
            ssh_username: serverForm.ssh_username,
            ssh_password: serverForm.ssh_password || undefined,
            description: serverForm.description,
            tags: serverForm.tags,
          })
        } else {
          await serversStore.createServer({
            name: serverForm.name,
            host: serverForm.host,
            port: serverForm.port,
            ssh_username: serverForm.ssh_username,
            ssh_password: serverForm.ssh_password,
            description: serverForm.description,
            tags: serverForm.tags,
          })
        }
        dialogVisible.value = false
        loadServers()
      } finally {
        submitting.value = false
      }
    }
  })
}

/**
 * 删除服务器
 */
const deleteServer = async (server: Server) => {
  await serversStore.deleteServer(server.id)
  loadServers()
}

/**
 * 测试连接
 */
const testConnection = async (server: Server) => {
  await serversStore.testConnection(server.id)
}

/**
 * 跳转到详情页
 */
const goToDetail = (id: string) => {
  router.push(`/servers/${id}`)
}

/**
 * 重置表单
 */
const resetForm = () => {
  Object.assign(serverForm, {
    id: '',
    name: '',
    host: '',
    port: 22,
    ssh_username: '',
    ssh_password: '',
    description: '',
    tags: [],
  })
  serverFormRef.value?.clearValidate()
}

/**
 * 获取状态标签类型
 */
const getStatusType = (status: string) => {
  const typeMap: Record<string, any> = {
    online: 'success',
    offline: 'info',
    error: 'danger',
    unknown: 'warning',
  }
  return typeMap[status] || 'info'
}

/**
 * 格式化日期
 */
const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

// 挂载时加载数据
onMounted(() => {
  loadServers()
})
</script>

<style scoped lang="scss">
.server-list {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h3 {
      margin: 0;
      font-size: 18px;
    }
  }

  .filter-bar {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }

  .pagination {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }
}
</style>
