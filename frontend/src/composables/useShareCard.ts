// 把一个梦渲染成可分享的精美图卡（Canvas），支持 Web Share / 下载。
import type { Dream } from '../types'

function loadImg(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = reject
    img.src = src
  })
}

function drawCover(ctx: CanvasRenderingContext2D, img: HTMLImageElement,
                   x: number, y: number, w: number, h: number) {
  const ir = img.width / img.height
  const rr = w / h
  let sw = img.width, sh = img.height, sx = 0, sy = 0
  if (ir > rr) { sw = img.height * rr; sx = (img.width - sw) / 2 }
  else { sh = img.width / rr; sy = (img.height - sh) / 2 }
  ctx.drawImage(img, sx, sy, sw, sh, x, y, w, h)
}

function wrapText(ctx: CanvasRenderingContext2D, text: string, maxW: number, maxLines: number): string[] {
  const lines: string[] = []
  let cur = ''
  for (const ch of text) {
    if (ctx.measureText(cur + ch).width > maxW) {
      lines.push(cur); cur = ch
      if (lines.length === maxLines - 1) break
    } else cur += ch
  }
  const used = lines.join('')
  let rest = text.slice(used.length)
  if (rest) {
    while (ctx.measureText(rest).width > maxW) rest = rest.slice(0, -1)
    if (rest.length < text.length - used.length) rest = rest.slice(0, -1) + '…'
    lines.push(rest)
  }
  return lines.slice(0, maxLines)
}

export async function buildShareCard(dream: Dream): Promise<Blob> {
  const W = 1080, H = 1350
  const canvas = document.createElement('canvas')
  canvas.width = W; canvas.height = H
  const ctx = canvas.getContext('2d')!
  const colors = dream.palette?.colors || ['#1e2235', '#3a4060', '#8a93c0']
  const accent = dream.palette?.accent || '#b9c0ec'

  // 底色
  const bg = ctx.createLinearGradient(0, 0, 0, H)
  bg.addColorStop(0, colors[0]); bg.addColorStop(1, '#06070f')
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H)

  // 封面图
  const cover = dream.cover_image_url || dream.narrative?.scenes?.find((s) => s.image_url)?.image_url
  const imgH = Math.round(H * 0.64)
  if (cover) {
    try {
      const img = await loadImg(cover)
      drawCover(ctx, img, 0, 0, W, imgH)
    } catch { /* 用底色 */ }
  }
  // 图底渐隐到深色
  const fade = ctx.createLinearGradient(0, imgH - 360, 0, imgH + 40)
  fade.addColorStop(0, 'rgba(6,7,15,0)'); fade.addColorStop(1, '#06070f')
  ctx.fillStyle = fade; ctx.fillRect(0, imgH - 360, W, 400)

  const PAD = 84
  let y = imgH + 16

  // eyebrow + 月亮
  ctx.fillStyle = accent
  ctx.beginPath(); ctx.arc(PAD + 9, y + 2, 9, 0, Math.PI * 2); ctx.fill()
  ctx.font = '500 26px "PingFang SC", sans-serif'
  ctx.fillStyle = 'rgba(255,255,255,0.6)'
  ctx.fillText('寻梦', PAD + 30, y + 11)
  y += 64

  // 标题
  ctx.font = '600 58px "Songti SC", "Noto Serif SC", serif'
  ctx.fillStyle = '#f3f1ff'
  for (const line of wrapText(ctx, dream.title || '一个梦', W - PAD * 2, 2)) {
    y += 66; ctx.fillText(line, PAD, y)
  }
  y += 26

  // 情绪
  if (dream.primary_emotion) {
    ctx.font = '400 28px "PingFang SC", sans-serif'
    const label = `· ${dream.primary_emotion} ·`
    const w = ctx.measureText(label).width
    ctx.fillStyle = 'rgba(185,192,236,0.16)'
    roundRect(ctx, PAD, y, w + 44, 50, 25); ctx.fill()
    ctx.fillStyle = accent
    ctx.fillText(label, PAD + 22, y + 34)
    y += 84
  }

  // 叙事金句（结尾安放语）
  const quote = dream.narrative?.closing_reflection || dream.narrative?.scenes?.[0]?.text || ''
  if (quote) {
    ctx.font = '400 34px "Songti SC", "Noto Serif SC", serif'
    ctx.fillStyle = 'rgba(236,236,246,0.85)'
    for (const line of wrapText(ctx, quote, W - PAD * 2, 3)) {
      y += 52; ctx.fillText(line, PAD, y)
    }
  }

  // 页脚
  ctx.font = '400 24px "PingFang SC", sans-serif'
  ctx.fillStyle = 'rgba(255,255,255,0.4)'
  ctx.fillText('把说不清的梦，轻轻接住', PAD, H - 60)

  return await new Promise<Blob>((resolve) => canvas.toBlob((b) => resolve(b!), 'image/png', 0.95))
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.arcTo(x + w, y, x + w, y + h, r)
  ctx.arcTo(x + w, y + h, x, y + h, r)
  ctx.arcTo(x, y + h, x, y, r)
  ctx.arcTo(x, y, x + w, y, r)
  ctx.closePath()
}

/** 分享或下载梦境图卡。 */
export async function shareDream(dream: Dream): Promise<'shared' | 'downloaded'> {
  const blob = await buildShareCard(dream)
  const file = new File([blob], `寻梦-${(dream.title || 'dream').slice(0, 20)}.png`, { type: 'image/png' })
  const nav = navigator as any
  if (nav.canShare && nav.canShare({ files: [file] })) {
    try {
      await nav.share({ files: [file], title: '寻梦', text: `我做了一个梦：${dream.title}` })
      return 'shared'
    } catch { /* 用户取消或失败 → 下载 */ }
  }
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = file.name; a.click()
  setTimeout(() => URL.revokeObjectURL(url), 2000)
  return 'downloaded'
}
