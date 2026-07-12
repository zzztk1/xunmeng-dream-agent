import type { Dream } from '../types'

/** 卡片封面样式：优先用首图，否则用情绪色板渐变。 */
export function coverStyle(d: Dream): Record<string, string> {
  if (d.cover_image_url) {
    return { backgroundImage: `url(${d.cover_image_url})`, backgroundSize: 'cover', backgroundPosition: 'center' }
  }
  const p = d.palette
  if (p && p.colors?.length >= 3) {
    return { background: `linear-gradient(135deg, ${p.colors[0]}, ${p.colors[2]})` }
  }
  return { background: 'linear-gradient(135deg,#1e2235,#3a4060)' }
}

export function todayLocal(): string {
  const d = new Date()
  const z = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}`
}
