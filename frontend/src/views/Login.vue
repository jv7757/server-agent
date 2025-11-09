<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <el-icon :size="40" color="#409EFF">
            <Monitor />
          </el-icon>
          <h2>{{ $t('login.title') }}</h2>
        </div>
      </template>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-position="top"
        size="large"
      >
        <el-form-item :label="$t('login.username')" prop="username">
          <el-input
            v-model="loginForm.username"
            :placeholder="$t('login.usernamePlaceholder')"
            :prefix-icon="User"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item :label="$t('login.password')" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            :placeholder="$t('login.passwordPlaceholder')"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="handleLogin">
            {{ $t('login.loginButton') }}
          </el-button>
        </el-form-item>

        <div class="login-footer">
          <span>{{ $t('login.noAccount') }}</span>
          <el-link type="primary" @click="goToRegister">
            {{ $t('login.registerLink') }}
          </el-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Monitor } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 表单引用
const loginFormRef = ref<FormInstance>()

// 表单数据
const loginForm = reactive({
  username: '',
  password: '',
})

// 加载状态
const loading = ref(false)

// 表单验证规则
const loginRules: FormRules = {
  username: [
    {
      required: true,
      message: t('login.usernameRequired'),
      trigger: 'blur',
    },
  ],
  password: [
    {
      required: true,
      message: t('login.passwordRequired'),
      trigger: 'blur',
    },
    {
      min: 6,
      message: t('login.passwordMinLength'),
      trigger: 'blur',
    },
  ],
}

/**
 * 处理登录
 */
const handleLogin = async () => {
  if (!loginFormRef.value) {
    return
  }

  await loginFormRef.value.validate(async valid => {
    if (valid) {
      loading.value = true
      try {
        const success = await authStore.login({
          username: loginForm.username,
          password: loginForm.password,
        })

        if (success) {
          // 登录成功，跳转到目标页面或首页
          const redirect = (route.query.redirect as string) || '/'
          router.push(redirect)
        }
      } finally {
        loading.value = false
      }
    }
  })
}

/**
 * 跳转到注册页
 */
const goToRegister = () => {
  router.push('/register')
}
</script>

<style scoped lang="scss">
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .login-card {
    width: 420px;
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

    .login-footer {
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
