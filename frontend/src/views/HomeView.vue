<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api/client'
import type { Dream } from '../types'
import { coverStyle } from '../utils/cover'
import { useAuth } from '../stores/auth'
import { computeStreak, recordedToday } from '../utils/streak'
import { getReminder, enableReminder, disableReminder } from '../composables/useReminder'

const auth = useAuth()
const recent = ref<Dream[]>([])
const streak = ref(0)
const didToday = ref(true)
const reminderOn = ref(getReminder().enabled)

const steps = [
  { n: '01', t: '留下碎片', d: '文字或语音，丢进梦里记得的片段，不必完整。' },
  { n: '02', t: 'AI 织梦', d: '保留你的意象与情绪，编织成有画面、有声音的梦。' },
  { n: '03', t: '被接住', d: '回看时用氛围与一句温柔的话，接住你的情绪。' },
]

onMounted(async () => {
  if (!auth.isAuthed) return
  try {
    const all = await api.listDreams()
    recent.value = all.slice(0, 4)
    streak.value = computeStreak(all)
    didToday.value = recordedToday(all)
  } catch { /* 首页不阻断 */ }
})
async function toggleReminder() {
  if (reminderOn.value) { disableReminder(); reminderOn.value = false }
  else { reminderOn.value = await enableReminder() }
}
</script>

<template>
  <div class="home">
    <section class="hero">
      <div class="hero-img" :style="{ backgroundImage: 'url(/img/hero.png)' }"></div>
      <div class="hero-scrim"></div>
      <div class="hero-inner">
        <p class="eyebrow float-in">寻梦</p>
        <h1 class="hero-title float-in">把说不清的梦，<br />轻轻接住。</h1>
        <p class="hero-sub float-in">
          梦来得快，消失得也快。在这里留下那些碎片，寻梦把它们织成一段
          能重新走进去的梦，也在你回看时，接住那一点说不清的情绪。
        </p>
        <div class="cta float-in">
          <template v-if="auth.isAuthed">
            <RouterLink to="/capture" class="btn btn-primary lg">记录一个梦</RouterLink>
            <RouterLink to="/library" class="btn btn-ghost lg">翻看旧梦</RouterLink>
          </template>
          <template v-else>
            <RouterLink to="/capture" class="btn btn-primary lg">✦ 免登录 · 记录一个梦</RouterLink>
            <RouterLink to="/showcase" class="btn btn-ghost lg">▶ 看一个梦</RouterLink>
          </template>
        </div>
      </div>
    </section>

    <div class="page">
      <div v-if="auth.user?.is_guest" class="guest-banner card">
        你正在以<b>游客</b>身份体验：
        <RouterLink to="/register" class="gb-link">注册</RouterLink>，刚才做的梦就会被永久保留 ✦
      </div>

      <section v-if="auth.isAuthed" class="habit card">
        <div class="streak">
          <span class="moon-emo">🌙</span>
          <span v-if="streak > 0">已连续记梦 <b>{{ streak }}</b> 天</span>
          <span v-else class="muted">开始你的记梦之旅</span>
        </div>
        <div class="habit-right">
          <RouterLink v-if="!didToday" to="/capture" class="nudge">今早的梦记下了吗？去记录 →</RouterLink>
          <button class="rem-btn" :class="{ on: reminderOn }" @click="toggleReminder">
            {{ reminderOn ? '🔔 晨间提醒已开' : '🔕 开启晨间提醒' }}
          </button>
        </div>
      </section>

      <section v-if="recent.length" class="recent">
        <div class="sec-head">
          <span class="muted">最近的梦</span>
          <RouterLink to="/library" class="faint more">全部 →</RouterLink>
        </div>
        <div class="grid">
          <RouterLink v-for="d in recent" :key="d.id" :to="`/dream/${d.id}`" class="dcard card">
            <div class="cover" :style="coverStyle(d)"></div>
            <div class="meta">
              <span class="dtitle">{{ d.title }}</span>
              <span class="faint sub">{{ d.dream_date }} · {{ d.primary_emotion || '未标注' }}</span>
            </div>
          </RouterLink>
        </div>
      </section>

      <section class="steps">
        <h2 class="steps-title">寻梦如何接住你的梦</h2>
        <div class="steps-grid">
          <div v-for="s in steps" :key="s.n" class="step card">
            <span class="step-n">{{ s.n }}</span>
            <h3 class="step-t">{{ s.t }}</h3>
            <p class="step-d">{{ s.d }}</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
/* HERO —— 全幅自适应主视觉 */
.hero {
  position: relative;
  min-height: clamp(440px, 86svh, 820px);
  display: flex; align-items: flex-end; justify-content: center;
  overflow: hidden;
}
.hero-img {
  position: absolute; inset: 0;
  background-size: cover; background-position: 50% 26%;
  animation: drift 40s var(--ease) infinite;
}
.hero-scrim {
  position: absolute; inset: 0;
  background:
    radial-gradient(120% 80% at 50% 18%, transparent 40%, rgba(10,12,22,0.25) 100%),
    linear-gradient(180deg, rgba(10,12,22,0.35) 0%, transparent 26%, rgba(10,12,22,0.55) 66%, var(--bg) 100%);
}
.hero-inner {
  position: relative; z-index: 1; text-align: center;
  width: min(680px, 92%); padding: 0 0 clamp(40px, 8vh, 88px);
}
.hero-title {
  font-family: var(--serif); font-weight: 600;
  font-size: clamp(32px, 7vw, 60px); line-height: 1.22; margin: 14px 0 18px;
  text-shadow: 0 4px 40px rgba(0,0,0,0.6);
}
.hero-sub {
  color: var(--ink-dim); font-size: clamp(15px, 1.6vw, 17px); line-height: 1.9;
  width: min(520px, 100%); margin: 0 auto 30px; text-shadow: 0 2px 16px rgba(0,0,0,0.6);
}
.cta { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }

/* 游客提示 */
.guest-banner { padding: 13px 18px; margin-bottom: 16px; font-size: 14px; color: var(--ink-dim); }
.guest-banner b { color: var(--gold); }
.gb-link { color: var(--accent); text-decoration: underline; }

/* 习惯条：连续打卡 + 晨间提醒 */
.habit {
  display: flex; align-items: center; justify-content: space-between; gap: 14px;
  padding: 14px 18px; margin-bottom: 20px; flex-wrap: wrap;
}
.streak { display: flex; align-items: center; gap: 10px; font-size: 15px; }
.streak b { color: var(--gold); font-size: 18px; font-family: var(--serif); }
.moon-emo { font-size: 18px; }
.habit-right { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.nudge { font-size: 13.5px; color: var(--accent); }
.nudge:hover { text-decoration: underline; }
.rem-btn {
  font-size: 13px; color: var(--ink-dim); background: rgba(255,255,255,0.05);
  border: 1px solid var(--line); border-radius: 999px; padding: 7px 14px; transition: all 0.2s var(--ease);
}
.rem-btn:hover { color: var(--ink); background: rgba(255,255,255,0.1); }
.rem-btn.on { color: var(--gold); border-color: rgba(244,217,166,0.4); background: rgba(244,217,166,0.1); }

/* 最近的梦 */
.sec-head { display: flex; justify-content: space-between; align-items: baseline; margin: 8px 0 16px; }
.more { font-size: 13px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 200px), 1fr)); gap: clamp(12px, 1.6vw, 18px); }
.dcard { overflow: hidden; }
.cover { aspect-ratio: 16 / 10; background-size: cover; background-position: center; }
.meta { padding: 13px 15px; display: flex; flex-direction: column; gap: 4px; }
.dtitle { font-family: var(--serif); font-size: 16px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sub { font-size: 12.5px; }

/* 三步 */
.steps { margin-top: clamp(40px, 7vh, 80px); }
.steps-title { font-family: var(--serif); font-weight: 500; font-size: clamp(20px, 2.4vw, 26px); text-align: center; margin: 0 0 clamp(22px, 3vw, 34px); }
.steps-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); gap: clamp(14px, 2vw, 20px); }
.step { padding: clamp(22px, 3vw, 30px); }
.step-n { font-family: var(--serif); font-size: 26px; color: var(--accent); opacity: 0.7; }
.step-t { font-family: var(--serif); font-size: 19px; margin: 12px 0 8px; }
.step-d { color: var(--ink-dim); font-size: 14.5px; line-height: 1.8; margin: 0; }
</style>
