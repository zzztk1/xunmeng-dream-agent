<script setup lang="ts">
import { computed } from 'vue'
import type { Palette, Scene } from '../types'

const props = defineProps<{ scene: Scene; active: boolean; palette?: Palette | null }>()

const loading = computed(() => !props.scene.image_url)
const phStyle = computed(() => {
  const p = props.palette
  const c = p?.colors || ['#1e2235', '#3a4060', '#8a93c0']
  return { background: `radial-gradient(120% 100% at 50% 38%, ${c[2]}, ${c[0]} 58%, ${p?.bg || '#0a0c16'})` }
})
</script>

<template>
  <div class="scene" :class="{ active }">
    <div
      v-if="scene.image_url"
      class="img"
      :style="{ backgroundImage: `url(${scene.image_url})` }"
    ></div>
    <div v-else class="img placeholder" :style="phStyle">
      <span class="shimmer"></span>
    </div>
    <div class="shade"></div>
    <div class="text-wrap">
      <p v-if="active" class="text float-in">{{ scene.text }}</p>
      <span v-if="active && loading" class="developing">
        <span class="dot"></span>正在显影…
      </span>
      <span v-else-if="active && scene.ambient" class="ambient float-in">{{ scene.ambient }}</span>
    </div>
  </div>
</template>

<style scoped>
.scene { position: absolute; inset: 0; opacity: 0; transition: opacity 1.1s var(--ease); pointer-events: none; }
.scene.active { opacity: 1; pointer-events: auto; }
.img {
  position: absolute; inset: 0; background-size: cover; background-position: center;
  transform: scale(1.05); animation: drift 26s var(--ease) infinite;
}
.img.placeholder { animation: none; }
.shimmer {
  position: absolute; inset: 0;
  background: linear-gradient(110deg, transparent 30%, rgba(255,255,255,0.08) 50%, transparent 70%);
  background-size: 220% 100%; animation: shimmer 2.4s linear infinite;
}
@keyframes shimmer { 0% { background-position: 130% 0; } 100% { background-position: -130% 0; } }
.shade {
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(7,7,15,0.45) 0%, rgba(7,7,15,0.05) 32%, rgba(7,7,15,0.55) 78%, rgba(7,7,15,0.9) 100%);
}
.text-wrap {
  position: absolute; left: 0; right: 0; bottom: 16vh;
  display: flex; flex-direction: column; align-items: center; gap: 14px; padding: 0 24px;
}
.text {
  font-family: var(--serif); font-size: clamp(19px, 2.6vw, 27px); line-height: 1.85;
  color: #f3f1ff; max-width: 680px; text-align: center; letter-spacing: 0.02em;
  text-shadow: 0 2px 24px rgba(0,0,0,0.7);
}
.ambient { font-size: 12px; letter-spacing: 0.4em; color: rgba(255,255,255,0.55); text-transform: uppercase; animation-delay: 0.4s; }
.developing { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; letter-spacing: 0.2em; color: rgba(255,255,255,0.65); }
.developing .dot { width: 7px; height: 7px; border-radius: 50%; background: #fff; animation: breathe 1.3s infinite; }
@media (prefers-reduced-motion: reduce) { .img { animation: none; } }
</style>
