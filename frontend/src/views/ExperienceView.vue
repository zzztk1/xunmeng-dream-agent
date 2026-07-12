<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import DreamScene from '../components/DreamScene.vue'
import SettlingRitual from '../components/SettlingRitual.vue'
import { api } from '../api/client'
import type { Dream } from '../types'
import { createAmbient } from '../composables/useAmbient'
import { shareDream } from '../composables/useShareCard'

const route = useRoute()
const router = useRouter()
const isShowcase = computed(() => !!route.meta.showcase)
const dream = ref<Dream | null>(null)
const loading = ref(true)
const error = ref('')
const index = ref(0)
const settled = ref(false)
const soundOn = ref(false)
const narrationOn = ref(false)
const sharing = ref(false)
const autoplay = ref(true)
let ambient: ReturnType<typeof createAmbient> | null = null
let pollTimer: number | undefined
let advTimer: number | undefined
const id = String(route.params.id || '')

const scenes = computed(() => dream.value?.narrative?.scenes ?? [])
const total = computed(() => scenes.value.length)
const onSettling = computed(() => total.value > 0 && index.value >= total.value)
const developing = computed(() => !!dream.value && !['generated', 'failed'].includes(dream.value.status))
const readyCount = computed(() => scenes.value.filter((s) => s.image_url).length)
const bgStyle = computed(() => {
  const p = dream.value?.palette
  return p ? { background: `radial-gradient(140% 120% at 50% 28%, ${p.colors[0]}, ${p.bg})` } : {}
})

const speechOK = typeof window !== 'undefined' && 'speechSynthesis' in window
function speak(text: string) {
  if (!narrationOn.value || !speechOK || !text) return
  window.speechSynthesis.cancel()
  const u = new SpeechSynthesisUtterance(text)
  u.lang = 'zh-CN'
  u.rate = 0.9
  window.speechSynthesis.speak(u)
}
function toggleNarration() {
  narrationOn.value = !narrationOn.value
  if (narrationOn.value) {
    speak(onSettling.value ? (dream.value?.narrative?.closing_reflection || '') : (scenes.value[index.value]?.text || ''))
  } else if (speechOK) window.speechSynthesis.cancel()
}

// 自动轮播：按叙事长度停留；显影中则等当前/下一幕出图再前进；末幕等全部出图后进入收束
function autoDur(text: string) { return Math.min(11000, Math.max(4500, (text?.length || 20) * 200)) }
function tick() {
  if (!autoplay.value || onSettling.value || !dream.value) return
  const i = index.value
  const cur = scenes.value[i]
  if (developing.value && cur && !cur.image_url) { schedule(1500); return }
  if (i < total.value - 1) {
    const nxt = scenes.value[i + 1]
    if (developing.value && nxt && !nxt.image_url) { schedule(1500); return }
    index.value = i + 1
  } else {
    if (developing.value && readyCount.value < total.value) { schedule(1500); return }
    index.value = total.value
  }
}
function schedule(ms?: number) {
  if (advTimer) clearTimeout(advTimer)
  if (!autoplay.value || onSettling.value || !dream.value) return
  advTimer = window.setTimeout(tick, ms ?? autoDur(scenes.value[index.value]?.text || ''))
}
function toggleAutoplay() {
  autoplay.value = !autoplay.value
  if (autoplay.value) schedule()
  else if (advTimer) clearTimeout(advTimer)
}
watch(index, (i) => { if (!onSettling.value) { speak(scenes.value[i]?.text || ''); schedule() } })
watch(onSettling, (v) => { if (v) { if (advTimer) clearTimeout(advTimer); speak(dream.value?.narrative?.closing_reflection || '') } })

async function poll() {
  try {
    const d = await api.getDream(id)
    dream.value = d
    if (['generated', 'failed'].includes(d.status) && pollTimer) { clearInterval(pollTimer); pollTimer = undefined }
  } catch { /* ignore */ }
}

onMounted(async () => {
  try {
    const d = isShowcase.value ? await api.showcase() : await api.getDream(id)
    if (!d) { router.replace('/'); return }
    dream.value = d
    if (!d.narrative || !d.narrative.scenes?.length) {
      router.replace(isShowcase.value ? '/' : `/dream/${d.id}`); return
    }
    ambient = createAmbient(d.palette?.ambient || 'airy')
    if (!isShowcase.value && developing.value) pollTimer = window.setInterval(poll, 4000)
  } catch (e: any) {
    error.value = e?.message || '这个梦走丢了'
  } finally {
    loading.value = false
  }
  window.addEventListener('keydown', onKey)
  schedule()  // 启动自动轮播
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  if (pollTimer) clearInterval(pollTimer)
  if (advTimer) clearTimeout(advTimer)
  ambient?.stop()
  if (speechOK) window.speechSynthesis.cancel()
})

function next() { if (index.value < total.value) index.value++ }
function prev() { if (index.value > 0) index.value-- }
function replay() { settled.value = false; index.value = 0 }
function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowRight') next()
  else if (e.key === 'ArrowLeft') prev()
  else if (e.key === 'Escape') exit()
}
function toggleSound() { soundOn.value = !soundOn.value; if (soundOn.value) ambient?.start(); else ambient?.stop() }
function exit() {
  if (isShowcase.value) router.push('/')
  else router.push(dream.value ? `/dream/${dream.value.id}` : '/library')
}
async function doShare() {
  if (!dream.value) return
  sharing.value = true
  try { await shareDream(dream.value) } finally { sharing.value = false }
}
</script>

<template>
  <div class="stage" :style="bgStyle">
    <div v-if="loading" class="center muted">正在唤醒这个梦…</div>

    <div v-else-if="error" class="center col">
      <p class="muted">{{ error }}</p>
      <button class="btn" @click="router.push('/')">回到首页</button>
    </div>

    <template v-else>
      <DreamScene
        v-for="(s, i) in scenes"
        :key="i"
        :scene="s"
        :active="i === index && !onSettling"
        :palette="dream?.palette"
      />

      <div v-if="onSettling" class="settle-layer">
        <SettlingRitual
          :reflection="dream?.narrative?.closing_reflection || '这个梦，已经被好好收下了。'"
          @settled="settled = true"
        />
        <div v-if="settled" class="after float-in">
          <template v-if="isShowcase">
            <RouterLink class="btn btn-primary" to="/register">✦ 注册，记录你自己的梦</RouterLink>
            <button class="btn btn-ghost" @click="replay">再看一遍</button>
          </template>
          <template v-else>
            <button class="btn btn-primary" :disabled="sharing" @click="doShare">{{ sharing ? '生成中…' : '↗ 分享这个梦' }}</button>
            <button class="btn btn-ghost" @click="replay">再走一遍</button>
            <RouterLink class="btn btn-ghost" :to="`/dream/${dream!.id}`">看看这个梦</RouterLink>
          </template>
        </div>
      </div>

      <div class="topbar">
        <button class="icon-btn" title="退出" @click="exit">←</button>
        <span class="dtitle">{{ dream?.title }}<span v-if="isShowcase" class="sample"> · 样例</span></span>
        <div class="tb-right">
          <button class="icon-btn" :title="autoplay ? '暂停自动播放' : '自动播放'" @click="toggleAutoplay">
            {{ autoplay ? '⏸' : '▶' }}
          </button>
          <button v-if="speechOK" class="icon-btn" :title="narrationOn ? '关闭旁白' : '朗读旁白'" @click="toggleNarration">
            {{ narrationOn ? '🗣' : '💬' }}
          </button>
          <button class="icon-btn" :title="soundOn ? '关闭氛围音' : '开启氛围音'" @click="toggleSound">
            {{ soundOn ? '🔊' : '🔈' }}
          </button>
        </div>
      </div>

      <div v-if="developing" class="dev-pill">梦境显影中 {{ readyCount }}/{{ total }}</div>

      <div v-if="!onSettling" class="controls">
        <button class="nav-btn" :disabled="index === 0" @click="prev">‹</button>
        <div class="dots">
          <span v-for="(s, i) in scenes" :key="i" class="dot" :class="{ on: i === index }" @click="index = i"></span>
        </div>
        <button class="nav-btn" :title="index === total - 1 ? '进入收束' : '下一幕'" @click="next">
          {{ index === total - 1 ? '✦' : '›' }}
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.stage { position: fixed; inset: 0; z-index: 1; overflow: hidden; }
.center { position: absolute; inset: 0; display: grid; place-items: center; }
.col { grid-auto-flow: row; gap: 16px; align-content: center; }
.topbar {
  position: absolute; top: 0; left: 0; right: 0; z-index: 20;
  display: flex; align-items: center; justify-content: space-between; padding: 16px 18px;
  background: linear-gradient(180deg, rgba(0,0,0,0.45), transparent);
}
.tb-right { display: flex; gap: 10px; }
.dtitle { font-family: var(--serif); font-size: 16px; color: #fff; opacity: 0.9; text-shadow: 0 2px 12px rgba(0,0,0,0.6); }
.sample { color: var(--accent); font-family: var(--sans); font-size: 12px; }
.icon-btn {
  width: 40px; height: 40px; border-radius: 50%; border: 1px solid rgba(255,255,255,0.2);
  background: rgba(0,0,0,0.25); color: #fff; font-size: 16px; backdrop-filter: blur(8px); transition: background 0.2s;
}
.icon-btn:hover { background: rgba(0,0,0,0.4); }
.dev-pill {
  position: absolute; top: 70px; left: 50%; transform: translateX(-50%); z-index: 20;
  font-size: 12.5px; letter-spacing: 0.12em; color: rgba(255,255,255,0.85);
  background: rgba(0,0,0,0.35); border: 1px solid rgba(255,255,255,0.16);
  padding: 5px 14px; border-radius: 999px; backdrop-filter: blur(8px);
}
.controls {
  position: absolute; bottom: 0; left: 0; right: 0; z-index: 20;
  display: flex; align-items: center; justify-content: center; gap: 22px; padding: 26px;
  background: linear-gradient(0deg, rgba(0,0,0,0.5), transparent);
}
.nav-btn {
  width: 48px; height: 48px; border-radius: 50%; border: 1px solid rgba(255,255,255,0.25);
  background: rgba(255,255,255,0.06); color: #fff; font-size: 22px; line-height: 1;
  backdrop-filter: blur(8px); transition: all 0.2s var(--ease);
}
.nav-btn:hover:not(:disabled) { background: rgba(255,255,255,0.16); transform: scale(1.05); }
.nav-btn:disabled { opacity: 0.3; }
.dots { display: flex; gap: 10px; }
.dots .dot { width: 9px; height: 9px; border-radius: 50%; background: rgba(255,255,255,0.3); cursor: pointer; transition: all 0.3s var(--ease); }
.dots .dot.on { background: #fff; transform: scale(1.3); box-shadow: 0 0 10px rgba(255,255,255,0.7); }
.settle-layer {
  position: absolute; inset: 0; z-index: 15; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 34px;
  background: rgba(7,7,15,0.55); backdrop-filter: blur(3px);
}
.after { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; }
</style>
