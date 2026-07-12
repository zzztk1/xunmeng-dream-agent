<script setup lang="ts">
interface EmotionValue { label: string; intensity: number }

const props = defineProps<{ modelValue: EmotionValue }>()
const emit = defineEmits<{ 'update:modelValue': [EmotionValue] }>()

const moods = [
  { label: '平静', color: '#bfe3d0' },
  { label: '害怕', color: '#9d7bd8' },
  { label: '留恋', color: '#f0c08a' },
  { label: '喜悦', color: '#ffd1e0' },
  { label: '迷茫', color: '#aeb6e0' },
]

function pick(label: string) {
  emit('update:modelValue', { ...props.modelValue, label })
}
function setIntensity(e: Event) {
  const v = Number((e.target as HTMLInputElement).value)
  emit('update:modelValue', { ...props.modelValue, intensity: v })
}
</script>

<template>
  <div class="emo">
    <div class="moods">
      <button
        v-for="m in moods"
        :key="m.label"
        class="mood"
        :class="{ on: props.modelValue.label === m.label }"
        :style="{ '--c': m.color }"
        @click="pick(m.label)"
      >
        <span class="swatch"></span>{{ m.label }}
      </button>
    </div>
    <div class="slider-row">
      <span class="faint">轻</span>
      <input
        class="slider"
        type="range" min="0" max="1" step="0.05"
        :value="props.modelValue.intensity"
        @input="setIntensity"
      />
      <span class="faint">浓</span>
    </div>
    <p class="faint hint">这只是个起点，寻梦会再听一遍你的梦，给出它读到的情绪。</p>
  </div>
</template>

<style scoped>
.emo { display: flex; flex-direction: column; gap: 14px; }
.moods { display: flex; gap: 9px; flex-wrap: wrap; }
.mood {
  display: inline-flex; align-items: center; gap: 8px;
  background: var(--card); border: 1px solid var(--line); color: var(--ink-dim);
  padding: 9px 15px; border-radius: 999px; font-size: 14px; transition: all 0.22s var(--ease);
}
.mood .swatch { width: 11px; height: 11px; border-radius: 50%; background: var(--c); box-shadow: 0 0 8px var(--c); }
.mood:hover { color: var(--ink); }
.mood.on { color: var(--ink); border-color: var(--c); background: color-mix(in srgb, var(--c) 16%, transparent); }
.slider-row { display: flex; align-items: center; gap: 12px; }
.slider {
  flex: 1; -webkit-appearance: none; appearance: none; height: 4px; border-radius: 4px;
  background: linear-gradient(90deg, rgba(174,182,224,0.25), rgba(176,90,154,0.7));
}
.slider::-webkit-slider-thumb {
  -webkit-appearance: none; width: 18px; height: 18px; border-radius: 50%;
  background: #fff; box-shadow: 0 0 10px rgba(255,255,255,0.6); cursor: pointer;
}
.hint { font-size: 12.5px; margin: 0; }
</style>
