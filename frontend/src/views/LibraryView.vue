<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api/client'
import type { Dream } from '../types'
import { coverStyle } from '../utils/cover'

const dreams = ref<Dream[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    dreams.value = await api.listDreams()
  } catch (e: any) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page library">
    <header class="head">
      <p class="eyebrow">梦境库</p>
      <h1 class="title-lg">你留下的梦</h1>
    </header>

    <p v-if="loading" class="muted">正在翻找那些梦…</p>
    <p v-else-if="error" class="muted">{{ error }}</p>

    <div v-else-if="!dreams.length" class="empty card">
      <p class="muted">这里还很空。</p>
      <RouterLink to="/capture" class="btn btn-primary">记录第一个梦</RouterLink>
    </div>

    <div v-else class="grid">
      <RouterLink v-for="d in dreams" :key="d.id" :to="`/dream/${d.id}`" class="dcard card">
        <div class="cover" :style="coverStyle(d)">
          <span v-if="d.status !== 'generated'" class="badge">{{ d.status === 'failed' ? '生成失败' : '未编织' }}</span>
        </div>
        <div class="meta">
          <span class="dtitle">{{ d.title }}</span>
          <div class="row">
            <span class="faint">{{ d.dream_date }}</span>
            <span v-if="d.primary_emotion" class="chip emo">{{ d.primary_emotion }}</span>
          </div>
        </div>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.head { margin-bottom: 22px; }
.empty { padding: 48px 24px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 18px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 18px; }
.dcard { overflow: hidden; }
.cover { height: 150px; position: relative; }
.badge {
  position: absolute; top: 10px; left: 10px; font-size: 11px; padding: 4px 9px; border-radius: 999px;
  background: rgba(0,0,0,0.5); color: #fff; backdrop-filter: blur(4px);
}
.meta { padding: 13px 15px; display: flex; flex-direction: column; gap: 8px; }
.dtitle { font-family: var(--serif); font-size: 16.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.row { display: flex; align-items: center; justify-content: space-between; }
.faint { font-size: 12.5px; }
.chip.emo { padding: 3px 10px; font-size: 12px; }
</style>
