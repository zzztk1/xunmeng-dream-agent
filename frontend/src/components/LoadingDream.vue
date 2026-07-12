<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

const steps = ['正在听你的梦…', '正在打捞那些碎片…', '正在把它们轻轻编织…', '正在让画面慢慢显影…']
const i = ref(0)
let timer: number | undefined

onMounted(() => {
  timer = window.setInterval(() => { i.value = (i.value + 1) % steps.length }, 2200)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="loader">
    <div class="orb"></div>
    <transition name="fade" mode="out-in">
      <p :key="i" class="step">{{ steps[i] }}</p>
    </transition>
    <p class="faint sub">编织需要一点点时间，像梦本身那样。</p>
  </div>
</template>

<style scoped>
.loader { display: flex; flex-direction: column; align-items: center; gap: 22px; padding: 60px 0; }
.orb {
  width: 96px; height: 96px; border-radius: 50%;
  background: radial-gradient(circle at 36% 32%, #fff, #aeb6e0 45%, #6a4aa0 80%);
  box-shadow: 0 0 60px rgba(174,182,224,0.5);
  animation: breathe 3.4s ease-in-out infinite;
}
.step { font-family: var(--serif); font-size: 19px; color: var(--ink); margin: 0; }
.sub { font-size: 13px; margin: 0; }
</style>
