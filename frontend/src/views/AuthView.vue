<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuth()

const mode = ref<'login' | 'register'>(route.name === 'register' ? 'register' : 'login')
watch(() => route.name, (n) => { mode.value = n === 'register' ? 'register' : 'login' })
const isReg = computed(() => mode.value === 'register')

const username = ref('')
const password = ref('')
const displayName = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  if (loading.value) return
  error.value = ''
  if (username.value.trim().length < 3) { error.value = '用户名至少 3 个字符'; return }
  if (password.value.length < 6) { error.value = '密码至少 6 位'; return }
  loading.value = true
  try {
    if (isReg.value) await auth.register(username.value.trim(), password.value, displayName.value.trim() || undefined)
    else await auth.login(username.value.trim(), password.value)
    router.replace((route.query.redirect as string) || '/')
  } catch (e: any) {
    error.value = e?.message || '出错了，请重试'
  } finally {
    loading.value = false
  }
}
function switchMode() {
  router.replace({ name: isReg.value ? 'login' : 'register', query: route.query })
}
</script>

<template>
  <div class="auth-wrap">
    <div class="auth-card float-in">
      <div class="moon"></div>
      <p class="eyebrow">寻梦</p>
      <h1 class="auth-title">{{ isReg ? '在这里，留下第一个梦' : '欢迎回到寻梦' }}</h1>
      <p class="auth-sub">{{ isReg ? '创建一个属于你的梦境空间。' : '继续走进你留下的那些梦。' }}</p>

      <form class="form" @submit.prevent="submit">
        <label class="lbl">用户名
          <input v-model="username" class="field" autocomplete="username" placeholder="3-32 个字符" />
        </label>
        <label v-if="isReg" class="lbl">昵称（选填）
          <input v-model="displayName" class="field" placeholder="希望被怎么称呼" />
        </label>
        <label class="lbl">密码
          <input v-model="password" type="password" class="field" autocomplete="current-password" placeholder="至少 6 位" />
        </label>

        <p v-if="error" class="err">{{ error }}</p>

        <button class="btn btn-primary submit" :disabled="loading">
          {{ loading ? '请稍候…' : (isReg ? '创建账号' : '登录') }}
        </button>
      </form>

      <p class="switch">
        {{ isReg ? '已经有账号了？' : '还没有账号？' }}
        <a class="switch-link" @click="switchMode">{{ isReg ? '去登录' : '去注册' }}</a>
      </p>
      <RouterLink to="/" class="back faint">← 回到首页</RouterLink>
    </div>
  </div>
</template>

<style scoped>
.auth-wrap { min-height: 100vh; display: grid; place-items: center; padding: 40px 20px; }
.auth-card {
  width: 100%; max-width: 400px; padding: 40px 34px 28px; text-align: center;
  background: rgba(255, 255, 255, 0.05); border: 1px solid var(--line);
  border-radius: 24px; backdrop-filter: blur(16px);
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.45);
}
.moon {
  width: 46px; height: 46px; border-radius: 50%; margin: 0 auto 18px;
  background: radial-gradient(circle at 34% 32%, #fff, #aeb6e0 55%, #6a4aa0);
  box-shadow: 0 0 34px rgba(174, 182, 224, 0.55);
}
.auth-title { font-family: var(--serif); font-size: 25px; margin: 10px 0 6px; }
.auth-sub { color: var(--ink-dim); font-size: 14.5px; margin: 0 0 26px; }
.form { display: flex; flex-direction: column; gap: 14px; text-align: left; }
.lbl { display: flex; flex-direction: column; gap: 7px; font-size: 13px; color: var(--ink-dim); }
.submit { justify-content: center; margin-top: 8px; padding: 13px; font-size: 15.5px; }
.err {
  margin: 0; font-size: 13px; color: #ffc4ce; background: rgba(255, 107, 139, 0.12);
  border: 1px solid rgba(255, 107, 139, 0.3); padding: 9px 12px; border-radius: 10px;
}
.switch { margin: 22px 0 8px; font-size: 14px; color: var(--ink-dim); }
.switch-link { color: var(--accent); cursor: pointer; }
.switch-link:hover { text-decoration: underline; }
.back { display: inline-block; font-size: 13px; margin-top: 4px; }
</style>
