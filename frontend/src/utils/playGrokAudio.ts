/** Play Grok Voice PCM audio streamed from the backend. */

let audioCtx: AudioContext | null = null
let playQueue: Promise<void> = Promise.resolve()

function getAudioContext(sampleRate: number): AudioContext {
  if (!audioCtx || audioCtx.state === 'closed') {
    audioCtx = new AudioContext({ sampleRate })
  }
  return audioCtx
}

function pcmBase64ToFloat32(pcmB64: string): Float32Array {
  const binary = atob(pcmB64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  const int16 = new Int16Array(bytes.buffer)
  const float32 = new Float32Array(int16.length)
  for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768
  return float32
}

export function playGrokPcm(pcmB64: string, sampleRate = 24000): Promise<void> {
  playQueue = playQueue.then(async () => {
    const ctx = getAudioContext(sampleRate)
    if (ctx.state === 'suspended') await ctx.resume()

    const samples = pcmBase64ToFloat32(pcmB64)
    if (samples.length === 0) return

    const buffer = ctx.createBuffer(1, samples.length, sampleRate)
    buffer.copyToChannel(samples, 0)

    await new Promise<void>((resolve) => {
      const source = ctx.createBufferSource()
      source.buffer = buffer
      source.connect(ctx.destination)
      source.onended = () => resolve()
      source.start(0)
    })
  })
  return playQueue
}

export function stopGrokAudio(): void {
  playQueue = Promise.resolve()
  if (audioCtx && audioCtx.state !== 'closed') {
    void audioCtx.close()
    audioCtx = null
  }
}

export interface VoiceAudioPayload {
  speaker: 'apo' | 'clinic'
  pcm_b64: string
  sample_rate: number
}

export function parseVoiceAudio(output: string): VoiceAudioPayload | null {
  try {
    const data = JSON.parse(output) as VoiceAudioPayload
    if (data.pcm_b64 && data.speaker) return data
  } catch {
    /* not audio json */
  }
  return null
}
