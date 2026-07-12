<script setup lang="ts">
import { onUnmounted, ref } from 'vue'

const props = defineProps<{ reflection: string }>()
const emit = defineEmits<{ settled: [] }>()

const progress = ref(0)
const done = ref(false)
const DURATION = 1400
let raf = 0
let startTs = 0

function tick(ts: number) {
  if (!startTs) startTs = ts
  progress.value = Math.min(1, (ts - startTs) / DURATION)
  if (progress.value < 1) raf = requestAnimationFrame(tick)
  else finish()
}
function press() {
  if (done.value) return
  startTs = 0
  raf = requestAnimationFrame(tick)
}
function release() {
  if (done.value || progress.value >= 1) return
  cancelAnimationFrame(raf)
  progress.value = 0
}
function finish() {
  done.value = true
  emit('settled')
}
onUnmounted(() => cancelAnimationFrame(raf))
</script>

<template>
  <div class="ritual">
    <p class="reflection float-in">{{ reflection }}</p>

    <div v-if="!done" class="hold-wrap">
      <button
        class="hold"
        :style="{ '--p': progress }"
        @pointerdown.prevent="press"
        @pointerup="release"
        @pointerleave="release"
        @pointercancel="release"
      >
        <span class="hold-fill"></span>
        <span class="hold-label">轻轻收好这个梦</span>
      </button>
      <p class="faint tip">长按一会儿，把它放下</p>
    </div>

    <div v-else class="done float-in">
      <span class="check">✦</span>
      <p class="done-text">已经替你好好收下了。<br />它会在这儿，等你下次想起。</p>
    </div>
  </div>
</template>

<style scoped>
.ritual { display: flex; flex-direction: column; align-items: center; gap: 26px; padding: 0 24px; text-align: center; }
.reflection {
  font-family: var(--serif); font-size: clamp(20px, 2.8vw, 28px); line-height: 1.8;
  color: #f3f1ff; max-width: 600px; text-shadow: 0 2px 24px rgba(0,0,0,0.6);
}
.hold-wrap { display: flex; flex-direction: column; align-items: center; gap: 12px; }
.hold {
  position: relative; width: 200px; height: 60px; border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.3); background: rgba(255,255,255,0.05);
  color: var(--ink); overflow: hidden; touch-action: none; user-select: none;
}
.hold-fill {
  position: absolute; inset: 0; transform-origin: left;
  transform: scaleX(var(--p, 0));
  background: linear-gradient(135deg, rgba(174,182,224,0.9), rgba(176,90,154,0.85));
}
.hold-label { position: relative; z-index: 1; font-size: 15px; mix-blend-mode: difference; }
.tip { font-size: 12.5px; margin: 0; }
.done { display: flex; flex-direction: column; align-items: center; gap: 14px; }
.check {
  font-size: 30px; color: #fff; width: 64px; height: 64px; border-radius: 50%;
  display: grid; place-items: center;
  background: radial-gradient(circle at 36% 32%, #fff, #aeb6e0 60%, #6a4aa0);
  box-shadow: 0 0 40px rgba(174,182,224,0.5);
}
.done-text { font-family: var(--serif); font-size: 18px; line-height: 1.8; color: var(--ink); margin: 0; }
</style>
