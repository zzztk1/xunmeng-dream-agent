import type { Dream } from '../types'

function dayKey(offset: number): string {
  const d = new Date()
  d.setDate(d.getDate() - offset)
  const z = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}`
}

export function recordedToday(dreams: Dream[]): boolean {
  return dreams.some((d) => d.dream_date === dayKey(0))
}

/** 连续记梦天数：今天记了从今天数；今天没记但昨天记了仍延续（从昨天数）；否则 0。 */
export function computeStreak(dreams: Dream[]): number {
  const set = new Set(dreams.map((d) => d.dream_date))
  let start: number
  if (set.has(dayKey(0))) start = 0
  else if (set.has(dayKey(1))) start = 1
  else return 0
  let streak = 0
  for (let i = start; ; i++) {
    if (set.has(dayKey(i))) streak++
    else break
  }
  return streak
}
