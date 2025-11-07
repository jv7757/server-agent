<template>
  <div class="user-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">用户管理</span>
          <div class="actions">
            <el-button :icon="Refresh" @click="loadUsers">刷新</el-button>
            <el-button type="primary" :icon="Plus" @click="handleCreate">
              新建用户
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选表单 -->
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="搜索">
          <el-input
            v-model="filters.search"
            placeholder="用户名/邮箱"
            clearable
            style="width: 240px"
            @clear="handleSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="角色">
          <el-select
            v-model="filters.role"
            placeholder="所有角色"
            clearable
            style="width: 140px"
            @change="handleSearch"
          >
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
            <el-option label="查看者" value="viewer" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select
            v-model="filters.is_active"
            placeholder="所有状态"
            clearable
            style="width: 140px"
            @change="handleSearch"
          >
            <el-option label="已启用" :value="true" />
            <el-option label="已禁用" :value="false" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 用户表格 -->
      <el-table v-loading="loading" :data="users" stripe style="width: 100%">
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="email" label="邮箱" width="220" />
        <el-table-column prop="full_name" label="全名" width="140">
          <template #default="{ row }">
            {{ row.full_name || '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)" size="small">
              {{ formatRole(row.role) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '已启用' : '已禁用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" fixed="right" width="260">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="warning" @click="handleChangeRole(row)">
              修改角色
            </el-button>
            <el-button
              link
              :type="row.is_active ? 'warning' : 'success'"
              @click="handleToggleStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
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

    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '新建用户'"
      width="600px"
      destroy-on-close
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            :disabled="isEdit"
            placeholder="请输入用户名（3-50字符）"
          />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" placeholder="请输入邮箱地址" />
        </el-form-item>

        <el-form-item label="全名" prop="full_name">
          <el-input v-model="formData.full_name" placeholder="请输入全名（可选）" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            show-password
            :placeholder="isEdit ? '留空表示不修改' : '请输入密码（至少8字符）'"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 修改角色对话框 -->
    <el-dialog
      v-model="roleDialogVisible"
      title="修改用户角色"
      width="400px"
      destroy-on-close
    >
      <el-form label-width="80px">
        <el-form-item label="当前用户">
          <span>{{ currentUser?.username }}</span>
        </el-form-item>

        <el-form-item label="当前角色">
          <el-tag :type="getRoleType(currentUser?.role || '')" size="small">
            {{ formatRole(currentUser?.role || '') }}
          </el-tag>
        </el-form-item>

        <el-form-item label="新角色">
          <el-select v-model="newRole" placeholder="选择角色" style="width: 100%">
            <el-option label="管理员 (admin)" value="admin" />
            <el-option label="普通用户 (user)" value="user" />
            <el-option label="查看者 (viewer)" value="viewer" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleConfirmRoleChange"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Refresh, Search, Plus } from '@element-plus/icons-vue'
import * as usersApi from '@/api/users'
import type { User } from '@/api/users'

// State
const loading = ref(false)
const submitting = ref(false)
const users = ref<User[]>([])
const dialogVisible = ref(false)
const roleDialogVisible = ref(false)
const isEdit = ref(false)
const currentUser = ref<User | null>(null)
const newRole = ref('')
const formRef = ref<FormInstance>()

const filters = reactive({
  search: '',
  role: '',
  is_active: undefined as boolean | undefined,
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0,
})

const formData = reactive({
  username: '',
  email: '',
  full_name: '',
  password: '',
})

const formRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ],
  password: [
    {
      validator: (rule, value, callback) => {
        if (!isEdit.value && !value) {
          callback(new Error('请输入密码'))
        } else if (value && value.length < 8) {
          callback(new Error('密码至少8字符'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// Methods
const loadUsers = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      size: pagination.size,
      search: filters.search || undefined,
      role: filters.role || undefined,
    }

    if (filters.is_active !== undefined) {
      params.is_active = filters.is_active
    }

    const response = await usersApi.getUsers(params)
    users.value = response.items
    pagination.total = response.total
  } catch (error: any) {
    console.error('加载用户列表失败:', error)
    ElMessage.error(error.response?.data?.detail || '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadUsers()
}

const handleReset = () => {
  filters.search = ''
  filters.role = ''
  filters.is_active = undefined
  pagination.page = 1
  loadUsers()
}

const handlePageChange = () => {
  loadUsers()
}

const handleSizeChange = () => {
  pagination.page = 1
  loadUsers()
}

const handleCreate = () => {
  isEdit.value = false
  currentUser.value = null
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (user: User) => {
  isEdit.value = true
  currentUser.value = user
  formData.username = user.username
  formData.email = user.email
  formData.full_name = user.full_name || ''
  formData.password = ''
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value && currentUser.value) {
        // 编辑用户
        const updateData: any = {
          email: formData.email,
          full_name: formData.full_name || null,
        }
        if (formData.password) {
          updateData.password = formData.password
        }

        await usersApi.updateUser(currentUser.value.id, updateData)
        ElMessage.success('用户信息已更新')
      } else {
        // 创建用户
        await usersApi.createUser({
          username: formData.username,
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name || undefined,
        })
        ElMessage.success('用户创建成功')
      }

      dialogVisible.value = false
      loadUsers()
    } catch (error: any) {
      console.error('操作失败:', error)
      ElMessage.error(error.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

const handleChangeRole = (user: User) => {
  currentUser.value = user
  newRole.value = user.role
  roleDialogVisible.value = true
}

const handleConfirmRoleChange = async () => {
  if (!currentUser.value || !newRole.value) return

  if (newRole.value === currentUser.value.role) {
    ElMessage.warning('角色未改变')
    return
  }

  submitting.value = true
  try {
    await usersApi.updateUserRole(currentUser.value.id, { role: newRole.value })
    ElMessage.success('用户角色已更新')
    roleDialogVisible.value = false
    loadUsers()
  } catch (error: any) {
    console.error('修改角色失败:', error)
    ElMessage.error(error.response?.data?.detail || '修改角色失败')
  } finally {
    submitting.value = false
  }
}

const handleToggleStatus = async (user: User) => {
  const action = user.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(
      `确定要${action}用户 ${user.username} 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await usersApi.updateUserStatus(user.id, { is_active: !user.is_active })
    ElMessage.success(`用户已${action}`)
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('操作失败:', error)
      ElMessage.error(error.response?.data?.detail || '操作失败')
    }
  }
}

const handleDelete = async (user: User) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 ${user.username} 吗？此操作将同时删除该用户的所有相关数据（服务器、聊天记录等），且无法恢复！`,
      '警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error',
        confirmButtonClass: 'el-button--danger',
      }
    )

    await usersApi.deleteUser(user.id)
    ElMessage.success('用户已删除')
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const resetForm = () => {
  formData.username = ''
  formData.email = ''
  formData.full_name = ''
  formData.password = ''
  formRef.value?.clearValidate()
}

const getRoleType = (role: string): string => {
  const roleMap: Record<string, string> = {
    admin: 'danger',
    user: 'success',
    viewer: 'info',
  }
  return roleMap[role] || ''
}

const formatRole = (role: string): string => {
  const roleMap: Record<string, string> = {
    admin: '管理员',
    user: '普通用户',
    viewer: '查看者',
  }
  return roleMap[role] || role
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Lifecycle
onMounted(() => {
  loadUsers()
})
</script>

<style scoped lang="scss">
.user-manage {
  padding: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .title {
      font-size: 18px;
      font-weight: 600;
    }

    .actions {
      display: flex;
      gap: 10px;
    }
  }

  .filter-form {
    margin-bottom: 20px;
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
