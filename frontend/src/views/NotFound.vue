<template>
  <div class="not-found">
    <div class="content">
      <h1>404</h1>
      <p>{{ $t('notFound.message') }}</p>
      <el-button type="primary" @click="goHome">
        {{ $t('notFound.goHome') }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<style scoped lang="scss">
.not-found {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;

  .content {
    text-align: center;

    h1 {
      font-size: 120px;
      margin: 0 0 20px;
      font-weight: bold;
      text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }

    p {
      font-size: 24px;
      margin: 0 0 40px;
    }
  }
}
</style>
