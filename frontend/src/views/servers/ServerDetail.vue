<template>
  <div class="server-detail">
    <el-page-header @back="goBack">
      <template #content>
        <span class="text-large font-600 mr-3">{{$t('servers.detailTitle')}}</span>
      </template>
    </el-page-header>

    <el-card style="margin-top: 20px" shadow="never" v-loading="loading">
      <h3>{{ $t('common.comingSoon') }}</h3>
      <p>{{ $t('common.featureInDevelopment') }}</p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const loading = ref(false)

const goBack = () => {
  router.back()
}

onMounted(() => {
  console.log('Server ID:', route.params.id)
})
</script>
