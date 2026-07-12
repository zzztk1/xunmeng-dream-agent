// 晨间记梦提醒（尽力而为：标签页打开期间按时弹通知；后台推送需 Web Push 服务端，后续接入）。
const KEY = 'espoir_reminder'

export interface ReminderCfg { enabled: boolean; time: string } // time "HH:MM"

export function getReminder(): ReminderCfg {
  try {
    const c = JSON.parse(localStorage.getItem(KEY) || '')
    if (c && typeof c.enabled === 'boolean' && typeof c.time === 'string') return c
  } catch { /* ignore */ }
  return { enabled: false, time: '08:00' }
}

function save(cfg: ReminderCfg) { localStorage.setItem(KEY, JSON.stringify(cfg)) }

let timer: number | undefined

export function scheduleNext() {
  if (timer) { clearTimeout(timer); timer = undefined }
  const c = getReminder()
  if (!c.enabled || !('Notification' in window) || Notification.permission !== 'granted') return
  const [h, m] = c.time.split(':').map(Number)
  const now = new Date()
  const next = new Date()
  next.setHours(h || 8, m || 0, 0, 0)
  if (next <= now) next.setDate(next.getDate() + 1)
  const ms = Math.min(next.getTime() - now.getTime(), 2 ** 31 - 1)
  timer = window.setTimeout(() => {
    try {
      new Notification('寻梦 · 记一个梦', {
        body: '今早的梦还记得吗？趁还没散，记下来吧。',
        icon: '/icons/icon-192.png',
      })
    } catch { /* ignore */ }
    scheduleNext()
  }, ms)
}

export async function enableReminder(time = '08:00'): Promise<boolean> {
  if (!('Notification' in window)) return false
  let perm = Notification.permission
  if (perm === 'default') perm = await Notification.requestPermission()
  if (perm !== 'granted') return false
  save({ enabled: true, time })
  scheduleNext()
  return true
}

export function disableReminder() {
  save({ ...getReminder(), enabled: false })
  if (timer) { clearTimeout(timer); timer = undefined }
}
