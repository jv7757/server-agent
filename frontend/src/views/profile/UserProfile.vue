<template>
  <div class="user-profile">
    <el-card shadow="never">
      <template #header>
        <h3>{{ $t('profile.title') }}</h3>
      </template>
      <div style="text-align: center; padding: 40px">
        <h3>{{ $t('common.comingSoon') }}</h3>
        <p>{{ $t('profile.description') }}</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// Coming soon
</script>
