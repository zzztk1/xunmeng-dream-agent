// 用 Web Audio 合成柔和的氛围音垫（无需音频文件）。需用户手势后启动。
const FREQS: Record<string, number[]> = {
  water_pad: [110.0, 164.81, 220.0],
  low_drone: [82.41, 110.0, 123.47],
  piano_wind: [130.81, 196.0, 261.63],
  chime: [261.63, 329.63, 392.0],
  airy: [146.83, 220.0, 293.66],
}

export function createAmbient(kind: string) {
  let ctx: AudioContext | null = null
  const stoppables: { stop: (t?: number) => void }[] = []

  function start() {
    if (ctx) return
    const AC = window.AudioContext || window.webkitAudioContext
    if (!AC) return
    ctx = new AC()
    const master = ctx.createGain()
    master.gain.value = 0
    master.connect(ctx.destination)
    master.gain.linearRampToValueAtTime(0.06, ctx.currentTime + 3)

    const list = FREQS[kind] || FREQS.airy
    list.forEach((f, i) => {
      const osc = ctx!.createOscillator()
      osc.type = i === 0 ? 'sine' : 'triangle'
      osc.frequency.value = f
      const g = ctx!.createGain()
      g.gain.value = 0.5 / (i + 1)
      // 慢速 LFO 让声音缓缓起伏
      const lfo = ctx!.createOscillator()
      lfo.frequency.value = 0.07 + i * 0.03
      const lfoGain = ctx!.createGain()
      lfoGain.gain.value = 0.25 / (i + 1)
      lfo.connect(lfoGain)
      lfoGain.connect(g.gain)
      osc.connect(g)
      g.connect(master)
      osc.start()
      lfo.start()
      stoppables.push(osc, lfo)
    })
  }

  function stop() {
    if (!ctx) return
    try { stoppables.forEach((n) => n.stop()) } catch { /* ignore */ }
    ctx.close()
    ctx = null
    stoppables.length = 0
  }

  return { start, stop }
}
