<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import EmotionSelector from '../components/EmotionSelector.vue'
import LoadingDream from '../components/LoadingDream.vue'
import { api } from '../api/client'
import type { Dream } from '../types'
import { coverStyle } from '../utils/cover'
import { shareDream } from '../composables/useShareCard'

const route = useRoute()
const router = useRouter()
const id = String(route.params.id)

const dream = ref<Dream | null>(null)
const loading = ref(true)
const error = ref('')
const busy = ref(false)
const confirmDelete = ref(false)
const editingEmotion = ref(false)
const emotionDraft = ref({ label: '平静', intensity: 0.5 })

const generated = computed(() => dream.value?.status === 'generated' && !!dream.value?.narrative)
const hasNarrative = computed(() => !!dream.value?.narrative)
const developing = computed(() => !!dream.value && ['weaving', 'imaging'].includes(dream.value.status))
const aiEmotions = computed(() => dream.value?.emotions.filter((e) => e.source === 'ai') || [])
const userEmotions = computed(() => dream.value?.emotions.filter((e) => e.source === 'user') || [])
const phStyle = computed(() => {
  const c = dream.value?.palette?.colors || ['#1e2235', '#3a4060', '#8a93c0']
  return { background: `linear-gradient(135deg, ${c[0]}, ${c[2]})` }
})

let pollTimer: number | undefined
function startPoll() {
  if (pollTimer) return
  pollTimer = window.setInterval(async () => {
    try {
      dream.value = await api.getDream(id)
      if (!developing.value && pollTimer) { clearInterval(pollTimer); pollTimer = undefined }
    } catch { /* ignore */ }
  }, 4000)
}

async function load() {
  loading.value = true
  try {
    dream.value = await api.getDream(id)
    if (developing.value) startPoll()
  } catch (e: any) {
    error.value = e?.message || '这个梦不见了'
  } finally {
    loading.value = false
  }
}
async function regenerate() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    dream.value = await api.regenerate(id)
    if (developing.value) startPoll()
  } catch (e: any) {
    error.value = e?.message || '重新编织失败'
  } finally {
    busy.value = false
  }
}
function startEditEmotion() {
  const u = userEmotions.value[0]
  emotionDraft.value = { label: u?.label || dream.value?.primary_emotion || '平静', intensity: u?.intensity ?? 0.5 }
  editingEmotion.value = true
}
async function saveEmotion() {
  busy.value = true
  try {
    dream.value = await api.patchDream(id, { emotions: [emotionDraft.value] })
    editingEmotion.value = false
  } finally {
    busy.value = false
  }
}
async function doDelete() {
  await api.deleteDream(id)
  router.push('/library')
}
const sharing = ref(false)
async function doShare() {
  if (!dream.value) return
  sharing.value = true
  try { await shareDream(dream.value) } finally { sharing.value = false }
}
onMounted(load)
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })
</script>

<template>
  <div class="page detail">
    <p v-if="loading" class="muted">正在取回这个梦…</p>
    <p v-else-if="error && !dream" class="muted">{{ error }}</p>

    <template v-else-if="dream">
      <div v-if="busy" class="busy-layer"><LoadingDream /></div>

      <RouterLink to="/library" class="back faint">← 梦境库</RouterLink>

      <header class="hero card" :style="coverStyle(dream)">
        <div class="hero-shade"></div>
        <div class="hero-content">
          <span class="faint date">{{ dream.dream_date }}</span>
          <h1 class="hero-title">{{ dream.title }}</h1>
          <div class="emos">
            <span v-for="(e, i) in aiEmotions" :key="'a' + i" class="chip emo ai">{{ e.label }}</span>
            <span v-for="(e, i) in userEmotions" :key="'u' + i" class="chip emo user">{{ e.label }} · 你</span>
          </div>
        </div>
      </header>

      <div class="actions">
        <RouterLink v-if="hasNarrative" :to="`/dream/${dream.id}/play`" class="btn btn-primary">✶ 进入这个梦</RouterLink>
        <button v-if="hasNarrative" class="btn" :disabled="sharing" @click="doShare">{{ sharing ? '生成中…' : '↗ 分享' }}</button>
        <button class="btn" @click="regenerate">↻ 重新编织</button>
        <button class="btn btn-ghost" @click="startEditEmotion">♥ 编辑情绪</button>
        <button v-if="!confirmDelete" class="btn btn-ghost danger" @click="confirmDelete = true">删除</button>
        <template v-else>
          <button class="btn danger-solid" @click="doDelete">确认删除</button>
          <button class="btn btn-ghost" @click="confirmDelete = false">取消</button>
        </template>
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <section v-if="editingEmotion" class="edit-emo card">
        <h2 class="label">这个梦，你想怎么标注它？</h2>
        <EmotionSelector v-model="emotionDraft" />
        <div class="edit-actions">
          <button class="btn btn-primary" @click="saveEmotion">保存</button>
          <button class="btn btn-ghost" @click="editingEmotion = false">取消</button>
        </div>
      </section>

      <!-- 叙事场景 -->
      <section v-if="hasNarrative" class="scenes">
        <h2 class="sec-label">这个梦被编织成了：<span v-if="developing" class="dev-tag">显影中…</span></h2>
        <article v-for="(s, i) in dream.narrative!.scenes" :key="i" class="scene-card card">
          <div class="sc-img" :style="s.image_url ? { backgroundImage: `url(${s.image_url})` } : phStyle">
            <span v-if="!s.image_url" class="sc-dev">显影中…</span>
          </div>
          <div class="sc-body">
            <span class="sc-no">场景 {{ i + 1 }}<span v-if="s.ambient"> · {{ s.ambient }}</span></span>
            <p class="sc-text">{{ s.text }}</p>
          </div>
        </article>
        <p class="closing">{{ dream.narrative!.closing_reflection }}</p>
      </section>
      <section v-else class="ungenerated card">
        <p class="muted">这个梦还没有被编织。</p>
        <button class="btn btn-primary" @click="regenerate">现在编织它</button>
      </section>

      <!-- 原始碎片 -->
      <section class="fragments">
        <h2 class="sec-label faint">你最初留下的碎片</h2>
        <ul class="frag-list">
          <li v-for="f in dream.fragments" :key="f.id" class="frag-li">
            <span class="ic">{{ f.type === 'voice' ? '🎙' : f.type === 'tag' ? '✦' : '✎' }}</span>
            <span>{{ f.content }}</span>
          </li>
        </ul>
      </section>
    </template>
  </div>
</template>

<style scoped>
.detail { position: relative; }
.busy-layer { position: fixed; inset: 0; z-index: 60; background: rgba(7,7,15,0.8); display: grid; place-items: center; }
.back { display: inline-block; margin-bottom: 14px; font-size: 14px; }
.hero { position: relative; height: 260px; border-radius: var(--radius); overflow: hidden; display: flex; align-items: flex-end; }
.hero-shade { position: absolute; inset: 0; background: linear-gradient(180deg, transparent 30%, rgba(7,7,15,0.85)); }
.hero-content { position: relative; padding: 24px; z-index: 1; }
.date { font-size: 13px; }
.hero-title { font-family: var(--serif); font-size: 30px; margin: 6px 0 12px; color: #fff; text-shadow: 0 2px 16px rgba(0,0,0,0.6); }
.emos { display: flex; gap: 8px; flex-wrap: wrap; }
.chip.emo { padding: 4px 11px; font-size: 12.5px; }
.chip.emo.ai { background: rgba(174,182,224,0.18); color: #dfe2ff; border-color: rgba(174,182,224,0.3); }
.chip.emo.user { background: rgba(255,209,224,0.14); color: #ffd9e6; border-color: rgba(255,209,224,0.3); }
.actions { display: flex; gap: 10px; flex-wrap: wrap; margin: 22px 0 8px; }
.danger { color: #ff95a6; }
.danger-solid { background: rgba(255,90,110,0.85); border-color: transparent; color: #fff; }
.error { color: #ffc4ce; background: rgba(255,107,139,0.12); border: 1px solid rgba(255,107,139,0.3); padding: 10px 14px; border-radius: 10px; font-size: 14px; }
.edit-emo { padding: 20px; margin: 16px 0; }
.label { font-size: 14px; color: var(--ink-dim); margin: 0 0 14px; }
.edit-actions { display: flex; gap: 10px; margin-top: 16px; }
.sec-label { font-family: var(--serif); font-size: 18px; margin: 34px 0 16px; font-weight: 500; }
.scene-card { display: flex; gap: 0; overflow: hidden; margin-bottom: 14px; }
.sc-img { width: 160px; flex: none; background-size: cover; background-position: center; background-color: #1a1d30; min-height: 130px; position: relative; display: grid; place-items: center; }
.sc-dev { font-size: 11px; letter-spacing: 0.15em; color: rgba(255,255,255,0.75); background: rgba(0,0,0,0.32); padding: 3px 9px; border-radius: 999px; }
.dev-tag { font-size: 12px; color: var(--accent); font-family: var(--sans); margin-left: 8px; letter-spacing: 0.1em; }
.sc-body { padding: 16px 18px; }
.sc-no { font-size: 12px; color: var(--ink-faint); letter-spacing: 0.1em; }
.sc-text { font-family: var(--serif); font-size: 16px; line-height: 1.85; color: var(--ink); margin: 8px 0 0; }
.closing { font-family: var(--serif); font-size: 17px; line-height: 1.8; color: var(--accent); text-align: center; margin: 26px auto; max-width: 520px; }
.ungenerated { padding: 32px; text-align: center; display: flex; flex-direction: column; gap: 16px; align-items: center; }
.frag-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.frag-li { display: flex; gap: 11px; background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 12px 15px; color: var(--ink-dim); }
.frag-li .ic { color: var(--accent); opacity: 0.8; }
@media (max-width: 560px) {
  .sc-img { width: 110px; min-height: 110px; }
  .hero { height: 220px; }
}
</style>
