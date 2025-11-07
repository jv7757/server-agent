<template>
  <div class="permission-manage">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <h3>权限管理</h3>
          <el-button type="primary" @click="handleAddPermission" v-if="selectedServerId">
            <el-icon><Plus /></el-icon>
            授予权限
          </el-button>
        </div>
      </template>

      <!-- 服务器选择 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="选择服务器">
          <el-select
            v-model="selectedServerId"
            placeholder="请选择服务器"
            style="width: 300px"
            filterable
            @change="handleServerChange"
          >
            <el-option
              v-for="server in servers"
              :key="server.id"
              :label="`${server.name} (${server.host})`"
              :value="server.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <!-- 权限列表 -->
      <el-table
        v-if="selectedServerId"
        :data="permissions"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column label="权限" min-width="300">
          <template #default="{ row }">
            <el-tag
              v-for="perm in row.permissions"
              :key="perm"
              :type="getPermissionTagType(perm)"
              style="margin-right: 5px"
            >
              {{ getPermissionLabel(perm) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="授予时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              link
              @click="handleRevokePermission(row)"
            >
              撤销
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-if="selectedServerId && total > 0"
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="fetchPermissions"
        @size-change="fetchPermissions"
        style="margin-top: 20px; justify-content: flex-end"
      />

      <!-- 提示信息 -->
      <el-empty
        v-if="!selectedServerId"
        description="请先选择一个服务器"
        :image-size="150"
      />
    </el-card>

    <!-- 授予权限对话框 -->
    <el-dialog
      v-model="grantDialogVisible"
      title="授予权限"
      width="500px"
      @close="resetGrantForm"
    >
      <el-form :model="grantForm" :rules="grantRules" ref="grantFormRef" label-width="80px">
        <el-form-item label="用户" prop="target_user_id">
          <el-select
            v-model="grantForm.target_user_id"
            placeholder="请选择用户"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="`${user.username} (${user.email})`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="权限" prop="permissions">
          <el-checkbox-group v-model="grantForm.permissions">
            <el-checkbox label="read">
              读取 <el-text type="info" size="small">(查看服务器信息和指标)</el-text>
            </el-checkbox>
            <el-checkbox label="write">
              写入 <el-text type="info" size="small">(修改服务器配置)</el-text>
            </el-checkbox>
            <el-checkbox label="execute">
              执行 <el-text type="info" size="small">(执行命令)</el-text>
            </el-checkbox>
            <el-checkbox label="admin">
              管理 <el-text type="info" size="small">(授予/撤销权限)</el-text>
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="grantDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleGrantSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getServerPermissions, grantPermission, revokePermission } from '@/api/permissions'
import { getServers } from '@/api/servers'
import { getUsers } from '@/api/users'
import type { Server, ServerPermissionItem, User } from '@/types/api'

// 数据
const servers = ref<Server[]>([])
const users = ref<User[]>([])
const permissions = ref<ServerPermissionItem[]>([])
const selectedServerId = ref<string>('')
const loading = ref(false)
const total = ref(0)

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
})

// 授予权限对话框
const grantDialogVisible = ref(false)
const submitting = ref(false)
const grantFormRef = ref<FormInstance>()
const grantForm = reactive({
  target_user_id: '',
  permissions: [] as string[],
})

const grantRules: FormRules = {
  target_user_id: [{ required: true, message: '请选择用户', trigger: 'change' }],
  permissions: [
    {
      type: 'array',
      required: true,
      message: '请至少选择一个权限',
      trigger: 'change',
    },
  ],
}

// 格式化日期
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 获取权限标签类型
const getPermissionTagType = (permission: string) => {
  const types: Record<string, any> = {
    read: '',
    write: 'success',
    execute: 'warning',
    admin: 'danger',
  }
  return types[permission] || ''
}

// 获取权限标签文本
const getPermissionLabel = (permission: string) => {
  const labels: Record<string, string> = {
    read: '读取',
    write: '写入',
    execute: '执行',
    admin: '管理',
  }
  return labels[permission] || permission
}

// 获取服务器列表
const fetchServers = async () => {
  try {
    const response = await getServers({ page: 1, size: 1000 })
    servers.value = response.items
  } catch (error: any) {
    ElMessage.error('获取服务器列表失败: ' + (error.message || '未知错误'))
  }
}

// 获取用户列表
const fetchUsers = async () => {
  try {
    const response = await getUsers({ page: 1, size: 1000 })
    users.value = response.items
  } catch (error: any) {
    // 不是管理员可能无法获取用户列表，静默失败
    console.error('获取用户列表失败:', error)
  }
}

// 获取权限列表
const fetchPermissions = async () => {
  if (!selectedServerId.value) return

  loading.value = true
  try {
    const response = await getServerPermissions(selectedServerId.value, {
      page: pagination.page,
      size: pagination.size,
    })
    permissions.value = response.items
    total.value = response.total
  } catch (error: any) {
    ElMessage.error('获取权限列表失败: ' + (error.message || '未知错误'))
    permissions.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 服务器选择变化
const handleServerChange = () => {
  pagination.page = 1
  fetchPermissions()
}

// 打开授予权限对话框
const handleAddPermission = () => {
  grantDialogVisible.value = true
}

// 重置授予权限表单
const resetGrantForm = () => {
  grantFormRef.value?.resetFields()
  grantForm.target_user_id = ''
  grantForm.permissions = []
}

// 提交授予权限
const handleGrantSubmit = async () => {
  if (!grantFormRef.value) return

  await grantFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      await grantPermission({
        server_id: selectedServerId.value,
        target_user_id: grantForm.target_user_id,
        permissions: grantForm.permissions as ('read' | 'write' | 'execute' | 'admin')[],
      })

      ElMessage.success('权限授予成功')
      grantDialogVisible.value = false
      fetchPermissions()
    } catch (error: any) {
      ElMessage.error('授予权限失败: ' + (error.message || '未知错误'))
    } finally {
      submitting.value = false
    }
  })
}

// 撤销权限
const handleRevokePermission = async (row: ServerPermissionItem) => {
  try {
    await ElMessageBox.confirm(`确定要撤销用户 ${row.username} 的权限吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    await revokePermission({
      server_id: selectedServerId.value,
      target_user_id: row.user_id,
    })

    ElMessage.success('权限已撤销')
    fetchPermissions()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('撤销权限失败: ' + (error.message || '未知错误'))
    }
  }
}

// 初始化
onMounted(() => {
  fetchServers()
  fetchUsers()
})
</script>

<style scoped lang="scss">
.permission-manage {
  padding: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h3 {
      margin: 0;
      font-size: 18px;
    }
  }

  .filter-form {
    margin-bottom: 20px;
  }

  :deep(.el-checkbox) {
    display: flex;
    align-items: flex-start;
    margin-bottom: 10px;

    .el-checkbox__label {
      display: flex;
      flex-direction: column;
      white-space: normal;
      line-height: 1.5;
    }
  }
}
</style>
