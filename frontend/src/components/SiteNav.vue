<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'

const auth = useAuth()
const router = useRouter()

async function doLogout() {
  await auth.logout()
  router.push('/')
}
</script>

<template>
  <header class="nav">
    <RouterLink to="/" class="brand">
      <span class="moon"></span>
      <span class="brand-text">寻梦</span>
    </RouterLink>
    <nav class="links">
      <template v-if="auth.isAuthed">
        <RouterLink to="/capture" class="lnk">记录</RouterLink>
        <RouterLink to="/library" class="lnk">梦境库</RouterLink>
        <RouterLink to="/calendar" class="lnk">日历</RouterLink>
        <RouterLink to="/insights" class="lnk">洞察</RouterLink>
        <RouterLink v-if="auth.user?.is_guest" to="/register" class="lnk reg">注册保存</RouterLink>
        <span v-else class="who" :title="auth.user?.username">{{ auth.user?.display_name }}</span>
        <button class="lnk logout" @click="doLogout">登出</button>
      </template>
      <template v-else>
        <RouterLink to="/login" class="lnk">登录</RouterLink>
        <RouterLink to="/register" class="lnk reg">注册</RouterLink>
      </template>
    </nav>
  </header>
</template>

<style scoped>
.nav {
  position: sticky; top: 0; z-index: 50;
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 22px;
  backdrop-filter: blur(10px);
  background: linear-gradient(180deg, rgba(11,13,24,0.7), rgba(11,13,24,0));
}
.brand { display: flex; align-items: center; gap: 9px; }
.moon {
  width: 16px; height: 16px; border-radius: 50%;
  background: radial-gradient(circle at 32% 32%, #fff, #aeb6e0 60%, #6f7197);
  box-shadow: 0 0 14px rgba(174,182,224,0.6);
}
.brand-text { font-family: var(--serif); font-size: 19px; letter-spacing: 0.16em; }
.links { display: flex; gap: 6px; align-items: center; }
.lnk {
  color: var(--ink-dim); font-size: 14px; padding: 7px 13px; border-radius: 999px;
  transition: all 0.2s var(--ease); border: none; background: transparent;
}
.lnk:hover { color: var(--ink); background: rgba(255,255,255,0.06); }
.router-link-active.lnk { color: var(--ink); background: rgba(255,255,255,0.08); }
.reg { color: var(--ink); background: rgba(174,182,224,0.16); }
.reg:hover { background: rgba(174,182,224,0.26); }
.who { color: var(--ink); font-size: 14px; padding: 0 6px 0 10px; opacity: 0.9; }
.logout { color: var(--ink-faint); }
.logout:hover { color: #ff95a6; background: rgba(255,107,139,0.1); }
@media (max-width: 480px) {
  .nav { padding: 12px 14px; }
  .lnk { padding: 6px 9px; font-size: 13px; }
  .who { display: none; }
}
</style>
