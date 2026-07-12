<script setup lang="ts">
// 全局梦境背景：星云图 + 缓慢漂移极光辉光 + 闪烁星点 + 可读性遮罩。固定最底层。
</script>

<template>
  <div class="bg-root" aria-hidden="true">
    <div class="nebula"></div>
    <div class="aurora aurora-a"></div>
    <div class="aurora aurora-b"></div>
    <div class="aurora aurora-c"></div>
    <div class="stars stars-1"></div>
    <div class="stars stars-2"></div>
    <div class="veil"></div>
  </div>
</template>

<style scoped>
.bg-root {
  position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden;
  background: #06070f;
}
.nebula {
  position: absolute; inset: -8%;
  background: url(/img/nebula.png) center / cover no-repeat;
  opacity: 0.6;
  transform: scale(1.05);
  animation: bgdrift 70s var(--ease) infinite;
}
.aurora {
  position: absolute; border-radius: 50%; filter: blur(100px);
  opacity: 0.35; mix-blend-mode: screen;
}
.aurora-a { width: 62vw; height: 62vw; left: -12vw; top: -14vw; background: radial-gradient(circle, #285f70, transparent 68%); animation: bgdrift 52s var(--ease) infinite; }
.aurora-b { width: 54vw; height: 54vw; right: -14vw; top: 28vh; background: radial-gradient(circle, #426c78, transparent 68%); animation: bgdrift 62s var(--ease) infinite reverse; }
.aurora-c { width: 46vw; height: 46vw; left: 30vw; bottom: -18vw; background: radial-gradient(circle, #2f7e75, transparent 70%); animation: bgdrift 58s var(--ease) infinite; }

.stars { position: absolute; inset: 0; }
.stars-1 {
  background-image:
    radial-gradient(1.6px 1.6px at 12% 18%, #fff, transparent),
    radial-gradient(1.4px 1.4px at 28% 62%, rgba(255,255,255,0.85), transparent),
    radial-gradient(1.8px 1.8px at 47% 33%, #fff, transparent),
    radial-gradient(1.3px 1.3px at 66% 72%, rgba(255,255,255,0.8), transparent),
    radial-gradient(1.5px 1.5px at 82% 22%, #fff, transparent),
    radial-gradient(1.3px 1.3px at 91% 58%, rgba(255,255,255,0.8), transparent);
  background-repeat: no-repeat;
  animation: twinkle 5.5s ease-in-out infinite;
}
.stars-2 {
  background-image:
    radial-gradient(1.2px 1.2px at 18% 82%, rgba(255,255,255,0.9), transparent),
    radial-gradient(1.1px 1.1px at 38% 12%, rgba(255,255,255,0.7), transparent),
    radial-gradient(1.3px 1.3px at 55% 88%, rgba(255,255,255,0.85), transparent),
    radial-gradient(1.1px 1.1px at 73% 44%, rgba(255,255,255,0.7), transparent),
    radial-gradient(1.4px 1.4px at 96% 80%, #fff, transparent);
  background-repeat: no-repeat;
  opacity: 0.7;
  animation: twinkle 7.5s ease-in-out infinite 1.6s;
}
.veil {
  position: absolute; inset: 0;
  background:
    radial-gradient(140% 100% at 50% 4%, transparent 30%, rgba(6,7,15,0.55) 100%),
    linear-gradient(180deg, rgba(6,7,15,0.42) 0%, rgba(6,7,15,0.22) 34%, rgba(6,7,15,0.58) 100%);
}

@keyframes bgdrift {
  0% { transform: translate(0, 0) scale(1.05); }
  50% { transform: translate(-2.2%, 2%) scale(1.12); }
  100% { transform: translate(0, 0) scale(1.05); }
}
@keyframes twinkle { 0%, 100% { opacity: 0.45; } 50% { opacity: 1; } }

@media (prefers-reduced-motion: reduce) {
  .nebula, .aurora, .stars { animation: none; }
}
</style>
