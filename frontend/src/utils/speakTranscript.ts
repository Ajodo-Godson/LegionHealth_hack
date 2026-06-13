/** Fallback browser TTS when Grok audio chunks are unavailable. */

let voicesReady: Promise<SpeechSynthesisVoice[]> | null = null

function loadVoices(): Promise<SpeechSynthesisVoice[]> {
  if (voicesReady) return voicesReady
  voicesReady = new Promise((resolve) => {
    const synth = window.speechSynthesis
    const voices = synth.getVoices()
    if (voices.length) {
      resolve(voices)
      return
    }
    synth.onvoiceschanged = () => resolve(synth.getVoices())
    setTimeout(() => resolve(synth.getVoices()), 250)
  })
  return voicesReady
}

function pickVoice(voices: SpeechSynthesisVoice[], speaker: 'apo' | 'clinic'): SpeechSynthesisVoice | null {
  const prefer = speaker === 'apo'
    ? [/samantha/i, /daniel/i, /alex/i, /google.*english.*male/i, /microsoft.*david/i]
    : [/karen/i, /victoria/i, /samantha/i, /google.*english.*female/i, /microsoft.*zira/i]

  for (const pattern of prefer) {
    const match = voices.find((v) => pattern.test(v.name))
    if (match) return match
  }
  return voices.find((v) => v.lang.startsWith('en')) ?? voices[0] ?? null
}

export function parseVoiceLine(raw: string): { speaker: 'apo' | 'clinic' | 'system'; text: string } {
  if (/^APO Voice Executor:/.test(raw)) {
    return { speaker: 'system', text: raw.replace(/^APO Voice Executor:\s*/, '') }
  }
  if (/^APO:/.test(raw)) {
    return { speaker: 'apo', text: raw.replace(/^APO:\s*/, '') }
  }
  if (/^Receptionist:/.test(raw)) {
    return { speaker: 'clinic', text: raw.replace(/^Receptionist:\s*/, '') }
  }
  return { speaker: 'system', text: raw }
}

export function cancelSpeech(): void {
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    window.speechSynthesis.cancel()
  }
}

export async function speakLine(speaker: 'apo' | 'clinic', text: string): Promise<void> {
  if (typeof window === 'undefined' || !window.speechSynthesis || !text.trim()) return

  const voices = await loadVoices()
  const voice = pickVoice(voices, speaker)

  return new Promise((resolve) => {
    const utterance = new SpeechSynthesisUtterance(text)
    if (voice) utterance.voice = voice
    utterance.rate = speaker === 'apo' ? 0.95 : 1.02
    utterance.pitch = speaker === 'apo' ? 0.9 : 1.08
    utterance.onend = () => resolve()
    utterance.onerror = () => resolve()
    window.speechSynthesis.speak(utterance)
  })
}
