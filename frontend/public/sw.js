// 寻梦 PWA service worker：静态资源 cache-first，导航 network-first(离线回退首页)，
// /api 与 /assets 不缓存（动态/私有）。
const CACHE = 'espoir-v1'

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.add('/')).catch(() => {}))
  self.skipWaiting()
})

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k !== CACHE) await caches.delete(k)
    await self.clients.claim()
  })())
})

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url)
  if (e.request.method !== 'GET' || url.origin !== self.location.origin) return
  if (url.pathname.startsWith('/api') || url.pathname.startsWith('/assets')) return

  if (url.pathname.startsWith('/static/')) {
    // 带哈希的构建产物，缓存优先
    e.respondWith(caches.open(CACHE).then(async (c) => {
      const hit = await c.match(e.request)
      if (hit) return hit
      const resp = await fetch(e.request)
      if (resp.ok) c.put(e.request, resp.clone())
      return resp
    }))
    return
  }

  if (e.request.mode === 'navigate') {
    e.respondWith(fetch(e.request).catch(() => caches.match('/')))
  }
})
