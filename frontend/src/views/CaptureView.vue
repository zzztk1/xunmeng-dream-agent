<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import FragmentInput from '../components/FragmentInput.vue'
import EmotionSelector from '../components/EmotionSelector.vue'
import LoadingDream from '../components/LoadingDream.vue'
import { api } from '../api/client'
import type { Fragment } from '../types'
import { todayLocal } from '../utils/cover'
import { useAuth } from '../stores/auth'

const router = useRouter()
const auth = useAuth()
const fragments = ref<Fragment[]>([])
const emotion = ref({ label: '平静', intensity: 0.5 })
const date = ref(todayLocal())
const loading = ref(false)
const error = ref('')
const createdId = ref<string | null>(null)

const canWeave = computed(() => fragments.value.length > 0)

async function weave() {
  if (!canWeave.value || loading.value) return
  loading.value = true
  error.value = ''
  try {
    let id = createdId.value
    if (!id) {
      const dream = await api.createDream({
        fragments: fragments.value.map((f) => ({ type: f.type, content: f.content })),
        emotion: emotion.value,
        dream_date: date.value,
      })
      id = dream.id
      createdId.value = id
      if (!auth.isAuthed) await auth.fetchMe()  // 游客建梦后刷新登录态，使受保护路由可达
    }
    const gen = await api.generate(id)
    router.push(`/dream/${gen.id}/play`)
  } catch (e: any) {
    error.value = e?.message || '编织失败了，请再试一次'
    loading.value = false
  }
}
</script>

<template>
  <div class="page page-narrow capture">
    <LoadingDream v-if="loading" />

    <template v-else>
      <header class="head float-in">
        <p class="eyebrow">记录</p>
        <h1 class="title-lg">说说你的梦</h1>
        <p class="muted">不用完整，碎片就好。一个画面、一种感觉、一句没头没尾的话，都可以。</p>
      </header>

      <section class="block">
        <h2 class="label">梦境碎片</h2>
        <FragmentInput v-model="fragments" />
      </section>

      <section class="block">
        <h2 class="label">此刻它给你的感觉</h2>
        <EmotionSelector v-model="emotion" />
      </section>

      <section class="block date-row">
        <h2 class="label">这是哪天的梦</h2>
        <input v-model="date" type="date" class="field date-field" />
      </section>

      <div v-if="error" class="error float-in">
        <span>{{ error }}</span>
        <button class="btn btn-ghost sm" @click="weave">重试</button>
      </div>

      <div class="actions">
        <button class="btn btn-primary lg" :disabled="!canWeave" @click="weave">
          ✶ 编织我的梦
        </button>
        <span v-if="!canWeave" class="faint hint">先丢一片梦进来吧</span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.capture { padding-top: 30px; }
.head { margin-bottom: 12px; }
.block { margin: 28px 0; }
.label { font-size: 14px; color: var(--ink-dim); font-weight: 500; margin: 0 0 14px; letter-spacing: 0.05em; }
.date-field { width: auto; color-scheme: dark; }
.actions { display: flex; align-items: center; gap: 14px; margin-top: 36px; }
.btn.lg { padding: 14px 30px; font-size: 16px; }
.btn.sm { padding: 6px 14px; font-size: 13px; }
.hint { font-size: 14px; }
.error {
  display: flex; align-items: center; gap: 14px; justify-content: space-between;
  background: rgba(255,107,139,0.12); border: 1px solid rgba(255,107,139,0.3);
  color: #ffc4ce; padding: 12px 16px; border-radius: 12px; font-size: 14px;
}
</style>
