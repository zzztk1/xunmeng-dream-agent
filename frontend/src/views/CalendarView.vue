<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api/client'
import type { CalendarData, Dream } from '../types'

const today = new Date()
const year = ref(today.getFullYear())
const month = ref(today.getMonth()) // 0-based
const data = ref<CalendarData | null>(null)
const allDreams = ref<Dream[]>([])
const selected = ref<string | null>(null)
const loading = ref(true)

const weekdays = ['一', '二', '三', '四', '五', '六', '日']
const monthStr = computed(() => `${year.value}-${String(month.value + 1).padStart(2, '0')}`)
const monthLabel = computed(() => `${year.value} 年 ${month.value + 1} 月`)
const days = computed(() => data.value?.days || {})

const cells = computed(() => {
  const first = new Date(year.value, month.value, 1)
  const startDow = (first.getDay() + 6) % 7 // 周一为 0
  const daysInMonth = new Date(year.value, month.value + 1, 0).getDate()
  const arr: ({ day: number; date: string } | null)[] = []
  for (let i = 0; i < startDow; i++) arr.push(null)
  for (let d = 1; d <= daysInMonth; d++) {
    arr.push({ day: d, date: `${monthStr.value}-${String(d).padStart(2, '0')}` })
  }
  return arr
})

const selectedDreams = computed(() =>
  selected.value ? allDreams.value.filter((d) => d.dream_date === selected.value) : []
)

function pad(n: number) { return String(n).padStart(2, '0') }
function isToday(date: string) {
  return date === `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`
}
function selectDay(date: string) { if (days.value[date]) selected.value = date }
function prevMonth() { if (month.value === 0) { month.value = 11; year.value-- } else month.value-- }
function nextMonth() { if (month.value === 11) { month.value = 0; year.value++ } else month.value++ }

async function load() {
  loading.value = true
  selected.value = null
  try {
    const [cal, list] = await Promise.all([api.calendar(monthStr.value), api.listDreams()])
    data.value = cal
    allDreams.value = list
  } catch { /* ignore */ } finally {
    loading.value = false
  }
}

watch(monthStr, load)
onMounted(load)
</script>

<template>
  <div class="page calendar">
    <header class="head">
      <p class="eyebrow">日历</p>
      <h1 class="title-lg">哪天，做了哪些梦</h1>
    </header>

    <div class="cal-bar">
      <button class="icon-btn" @click="prevMonth">‹</button>
      <span class="month-label">{{ monthLabel }}</span>
      <button class="icon-btn" @click="nextMonth">›</button>
    </div>

    <div class="weekrow">
      <span v-for="w in weekdays" :key="w" class="wd">{{ w }}</span>
    </div>

    <div class="grid">
      <div
        v-for="(c, i) in cells"
        :key="i"
        class="cell"
        :class="{ empty: !c, has: c && days[c.date], today: c && isToday(c.date), sel: c && selected === c.date }"
        :style="c && days[c.date]?.cover_image_url ? { backgroundImage: `url(${days[c.date].cover_image_url})` } : {}"
        @click="c && selectDay(c.date)"
      >
        <template v-if="c">
          <span class="num">{{ c.day }}</span>
          <span v-if="days[c.date]" class="cnt">{{ days[c.date].count }}</span>
        </template>
      </div>
    </div>

    <p v-if="loading" class="muted center-tip">正在翻日历…</p>

    <transition name="fade">
      <section v-if="selected && selectedDreams.length" class="day-panel">
        <h2 class="panel-title">{{ selected }} 的梦</h2>
        <RouterLink
          v-for="d in selectedDreams"
          :key="d.id"
          :to="`/dream/${d.id}`"
          class="day-item card"
        >
          <span class="di-emo" :style="{ background: d.palette?.accent || '#aeb6e0' }"></span>
          <span class="di-title">{{ d.title }}</span>
          <span class="faint">{{ d.primary_emotion || '未标注' }}</span>
        </RouterLink>
      </section>
    </transition>
  </div>
</template>

<style scoped>
.head { margin-bottom: 18px; }
.cal-bar { display: flex; align-items: center; justify-content: center; gap: 24px; margin-bottom: 16px; }
.month-label { font-family: var(--serif); font-size: 19px; min-width: 140px; text-align: center; }
.icon-btn {
  width: 38px; height: 38px; border-radius: 50%; border: 1px solid var(--line);
  background: var(--card); color: var(--ink); font-size: 18px; transition: background 0.2s;
}
.icon-btn:hover { background: var(--card-hover); }
.weekrow { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin-bottom: 8px; }
.wd { text-align: center; font-size: 12px; color: var(--ink-faint); }
.grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; }
.cell {
  aspect-ratio: 1 / 1; border-radius: 12px; position: relative;
  background-size: cover; background-position: center;
  border: 1px solid var(--line); display: flex; align-items: flex-start; justify-content: flex-end;
  padding: 7px; transition: all 0.2s var(--ease);
}
.cell.empty { border: none; background: transparent; }
.cell.has { cursor: pointer; box-shadow: inset 0 0 0 100px rgba(7,7,15,0.32); }
.cell.has:hover { transform: translateY(-2px); box-shadow: inset 0 0 0 100px rgba(7,7,15,0.18); }
.cell.today { border-color: rgba(174,182,224,0.7); }
.cell.sel { outline: 2px solid var(--accent); outline-offset: 1px; }
.num { font-size: 13px; color: var(--ink-dim); }
.cell.has .num { color: #fff; text-shadow: 0 1px 6px rgba(0,0,0,0.7); }
.cnt {
  position: absolute; left: 7px; bottom: 7px; font-size: 11px; color: #fff;
  background: rgba(0,0,0,0.45); border-radius: 999px; padding: 1px 7px; backdrop-filter: blur(3px);
}
.center-tip { text-align: center; margin-top: 20px; }
.day-panel { margin-top: 26px; display: flex; flex-direction: column; gap: 10px; }
.panel-title { font-family: var(--serif); font-size: 17px; color: var(--ink-dim); font-weight: 500; margin: 0 0 4px; }
.day-item { display: flex; align-items: center; gap: 12px; padding: 13px 16px; }
.di-emo { width: 12px; height: 12px; border-radius: 50%; flex: none; box-shadow: 0 0 8px currentColor; }
.di-title { flex: 1; font-family: var(--serif); font-size: 15.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
@media (max-width: 560px) { .grid, .weekrow { gap: 5px; } .cell { padding: 4px; border-radius: 9px; } }
</style>
