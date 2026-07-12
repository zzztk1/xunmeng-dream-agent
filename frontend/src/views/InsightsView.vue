<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api/client'
import type { Insights } from '../types'

const data = ref<Insights | null>(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try { data.value = await api.insights() } catch (e: any) { error.value = e?.message || '加载失败' } finally { loading.value = false }
})

const emoMax = computed(() => Math.max(1, ...(data.value?.emotions.map((e) => e.count) || [1])))
const monMax = computed(() => Math.max(1, ...(data.value?.by_month.map((m) => m.count) || [1])))
const imgMax = computed(() => Math.max(1, ...(data.value?.imagery.map((i) => i.count) || [1])))
const palette = ['#bfe3d0', '#9d7bd8', '#f0c08a', '#ffd1e0', '#aeb6e0', '#7fd1c4', '#e0a0c8', '#c8b0f0']
function imgSize(c: number) { return 13 + Math.round((c / imgMax.value) * 17) }

const stars = computed(() => {
  const n = Math.min(data.value?.total || 0, 80)
  const arr: { x: number; y: number; r: number }[] = []
  for (let i = 0; i < n; i++) {
    const a = i * 2.399963 // 黄金角
    const rad = 5 + (i / Math.max(n, 1)) * 44
    arr.push({ x: 50 + rad * Math.cos(a), y: 50 + rad * Math.sin(a) * 0.6, r: 0.7 + (i % 3) * 0.45 })
  }
  return arr
})
</script>

<template>
  <div class="page insights">
    <header class="head">
      <p class="eyebrow">洞察</p>
      <h1 class="title-lg">你的梦，慢慢长出形状</h1>
    </header>

    <p v-if="loading" class="muted">正在汇拢你的梦…</p>
    <p v-else-if="error" class="muted">{{ error }}</p>
    <div v-else-if="!data || data.total === 0" class="empty card">
      <p class="muted">还没有梦可以分析。</p>
      <RouterLink to="/capture" class="btn btn-primary">记录一个梦</RouterLink>
    </div>

    <template v-else>
      <section class="grid">
        <!-- 梦境星座 -->
        <div class="card panel constellation">
          <div class="panel-head"><span>梦境星座</span><b>{{ data.total }} 个梦</b></div>
          <svg viewBox="0 0 100 100" class="sky" preserveAspectRatio="xMidYMid meet">
            <circle v-for="(s, i) in stars" :key="i" :cx="s.x" :cy="s.y" :r="s.r"
                    fill="#fff" :opacity="0.5 + (i % 4) * 0.12" />
          </svg>
        </div>

        <!-- 情绪分布 -->
        <div class="card panel">
          <div class="panel-head"><span>情绪分布</span></div>
          <div class="bars">
            <div v-for="(e, i) in data.emotions" :key="e.label" class="bar-row">
              <span class="bar-label">{{ e.label }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: (e.count / emoMax * 100) + '%', background: palette[i % palette.length] }"></div>
              </div>
              <span class="bar-num">{{ e.count }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 高频意象 -->
      <section class="card panel">
        <div class="panel-head"><span>反复出现的意象</span></div>
        <div class="cloud">
          <span v-for="(w, i) in data.imagery" :key="w.word" class="word"
                :style="{ fontSize: imgSize(w.count) + 'px', color: palette[i % palette.length] }">{{ w.word }}</span>
          <span v-if="!data.imagery.length" class="faint">织几个梦，意象会在这里浮现。</span>
        </div>
      </section>

      <!-- 按月 -->
      <section v-if="data.by_month.length" class="card panel">
        <div class="panel-head"><span>每月记梦</span></div>
        <div class="months">
          <div v-for="m in data.by_month" :key="m.month" class="month">
            <div class="m-bar" :style="{ height: (m.count / monMax * 90 + 10) + '%' }"></div>
            <span class="m-num">{{ m.count }}</span>
            <span class="m-label">{{ m.month.slice(5) }}月</span>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.head { margin-bottom: 22px; }
.empty { padding: 48px 24px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 16px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)); gap: clamp(14px, 2vw, 20px); }
.panel { padding: clamp(18px, 2.4vw, 26px); margin-bottom: clamp(14px, 2vw, 20px); }
.panel-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 18px; color: var(--ink-dim); font-size: 14px; }
.panel-head b { color: var(--gold); font-family: var(--serif); font-size: 16px; }
.constellation .sky { width: 100%; height: 220px; display: block; }
.bars { display: flex; flex-direction: column; gap: 12px; }
.bar-row { display: flex; align-items: center; gap: 12px; }
.bar-label { width: 56px; font-size: 13.5px; color: var(--ink); flex: none; }
.bar-track { flex: 1; height: 10px; background: rgba(255,255,255,0.06); border-radius: 999px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 999px; transition: width 0.8s var(--ease); }
.bar-num { width: 24px; text-align: right; font-size: 13px; color: var(--ink-faint); flex: none; }
.cloud { display: flex; flex-wrap: wrap; gap: 10px 16px; align-items: center; line-height: 1.5; }
.word { font-family: var(--serif); opacity: 0.9; }
.months { display: flex; align-items: flex-end; gap: clamp(8px, 2vw, 18px); height: 150px; padding-top: 10px; }
.month { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; gap: 6px; }
.m-bar { width: min(40px, 70%); border-radius: 8px 8px 0 0; background: linear-gradient(180deg, var(--accent), rgba(176,90,154,0.6)); min-height: 8px; }
.m-num { font-size: 12px; color: var(--ink); }
.m-label { font-size: 11px; color: var(--ink-faint); }
</style>
