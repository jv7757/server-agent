<template>
  <div class="register-container">
    <el-card class="register-card">
      <template #header>
        <div class="card-header">
          <el-icon :size="40" color="#409EFF">
            <UserFilled />
          </el-icon>
          <h2>{{ $t('register.title') }}</h2>
        </div>
      </template>

      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-position="top"
        size="large"
      >
        <el-form-item :label="$t('register.username')" prop="username">
          <el-input
            v-model="registerForm.username"
            :placeholder="$t('register.usernamePlaceholder')"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item :label="$t('register.email')" prop="email">
          <el-input
            v-model="registerForm.email"
            :placeholder="$t('register.emailPlaceholder')"
            :prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item :label="$t('register.password')" prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            :placeholder="$t('register.passwordPlaceholder')"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item :label="$t('register.confirmPassword')" prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            :placeholder="$t('register.confirmPasswordPlaceholder')"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            style="width: 100%"
            @click="handleRegister"
          >
            {{ $t('register.registerButton') }}
          </el-button>
        </el-form-item>

        <div class="register-footer">
          <span>{{ $t('register.hasAccount') }}</span>
          <el-link type="primary" @click="goToLogin">
            {{ $t('register.loginLink') }}
          </el-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Message, UserFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

// 表单引用
const registerFormRef = ref<FormInstance>()

// 表单数据
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

// 加载状态
const loading = ref(false)

// 自定义验证器：确认密码
const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value === '') {
    callback(new Error(t('register.confirmPasswordRequired')))
  } else if (value !== registerForm.password) {
    callback(new Error(t('register.passwordMismatch')))
  } else {
    callback()
  }
}

// 表单验证规则
const registerRules: FormRules = {
  username: [
    {
      required: true,
      message: t('register.usernameRequired'),
      trigger: 'blur',
    },
    {
      min: 3,
      max: 20,
      message: t('register.usernameLength'),
      trigger: 'blur',
    },
  ],
  email: [
    {
      required: true,
      message: t('register.emailRequired'),
      trigger: 'blur',
    },
    {
      type: 'email',
      message: t('register.emailInvalid'),
      trigger: 'blur',
    },
  ],
  password: [
    {
      required: true,
      message: t('register.passwordRequired'),
      trigger: 'blur',
    },
    {
      min: 8,
      message: t('register.passwordMinLength'),
      trigger: 'blur',
    },
  ],
  confirmPassword: [
    {
      required: true,
      validator: validateConfirmPassword,
      trigger: 'blur',
    },
  ],
}

/**
 * 处理注册
 */
const handleRegister = async () => {
  if (!registerFormRef.value) return

  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const success = await authStore.register({
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password,
        })

        if (success) {
          // 注册成功，跳转到登录页
          router.push('/login')
        }
      } finally {
        loading.value = false
      }
    }
  })
}

/**
 * 跳转到登录页
 */
const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped lang="scss">
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .register-card {
    width: 450px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);

    :deep(.el-card__header) {
      padding: 30px 20px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }

    .card-header {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 15px;

      h2 {
        margin: 0;
        font-size: 24px;
        font-weight: 500;
      }
    }

    :deep(.el-card__body) {
      padding: 30px;
    }

    .register-footer {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 8px;
      margin-top: 20px;
      font-size: 14px;
      color: #606266;
    }
  }
}
</style>
