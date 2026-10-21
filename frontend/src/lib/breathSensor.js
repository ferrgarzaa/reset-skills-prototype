// Optional microphone breath sensing.
// The audio is analyzed only in this browser, a few times per second, to get a
// loudness level. Nothing is recorded, stored, or sent anywhere.
//
// How it works: an exhale makes a soft, wide "whoosh" sound. During the intro
// (3 s) we measure the room's background level. During each exhale phase, if
// the level stays clearly above that background for long enough, we count that
// breath as heard.
//
// Limits: noisy rooms, fans, or music can look like breath; quiet breathers or
// mics far away may not be heard. It is a gentle cue, never a score.

export class BreathSensor {
  constructor() {
    this.stream = null
    this.ctx = null
    this.analyser = null
    this.buf = null
    this.floor = null
    this.samples = []
  }

  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false },
    })
    const Ctx = window.AudioContext || window.webkitAudioContext
    this.ctx = new Ctx()
    const src = this.ctx.createMediaStreamSource(this.stream)
    // High-pass so voice hum and low rumble count less than breath noise.
    const hp = this.ctx.createBiquadFilter()
    hp.type = 'highpass'
    hp.frequency.value = 500
    this.analyser = this.ctx.createAnalyser()
    this.analyser.fftSize = 1024
    this.buf = new Float32Array(this.analyser.fftSize)
    src.connect(hp)
    hp.connect(this.analyser)
  }

  level() {
    if (!this.analyser) return 0
    this.analyser.getFloatTimeDomainData(this.buf)
    let sum = 0
    for (let i = 0; i < this.buf.length; i++) sum += this.buf[i] * this.buf[i]
    return Math.sqrt(sum / this.buf.length)
  }

  // Call repeatedly during the intro.
  calibrateSample() {
    this.samples.push(this.level())
  }

  finishCalibration() {
    const s = [...this.samples].sort((a, b) => a - b)
    // Median is robust to a cough or a click during calibration.
    this.floor = s.length ? s[Math.floor(s.length / 2)] : 0.002
    this.samples = []
  }

  threshold() {
    const f = this.floor ?? 0.002
    return Math.max(f * 2.5, f + 0.004)
  }

  // 0..1 value for the visual ring.
  intensity() {
    const t = this.threshold()
    return Math.max(0, Math.min(1, (this.level() - (this.floor ?? 0)) / (t * 2)))
  }

  isBreathing() {
    return this.level() > this.threshold()
  }

  stop() {
    this.stream?.getTracks().forEach((t) => t.stop())
    this.ctx?.close()
    this.stream = this.ctx = this.analyser = null
  }
}
