import { useEffect, useRef } from 'react'
import type { AgentLogEntry } from '../types'

interface VoiceTranscriptProps {
  events: AgentLogEntry[]
  status: string
}

export function VoiceTranscript({ events, status }: VoiceTranscriptProps) {
  const voiceEvents = events.filter(
    (e) => e.agent === 'voice' && (e.action === 'transcript' || e.action === 'calling' || e.action === 'response'),
  )
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [voiceEvents.length])

  const isActive = status === 'streaming' || status === 'connecting'
  const hasVoice = voiceEvents.length > 0

  if (!hasVoice && !isActive) return null

  return (
    <section className="voice-transcript">
      <header className="voice-header">
        <span className="voice-icon">📞</span>
        <h3>Voice Executor — Clinic Call</h3>
        {isActive && !hasVoice && <span className="voice-live">Dialing…</span>}
        {hasVoice && isActive && <span className="voice-live">Live</span>}
      </header>

      <div className="voice-messages" ref={scrollRef}>
        {!hasVoice && isActive && (
          <p className="voice-placeholder">Connecting to Northside Sleep Center…</p>
        )}
        {voiceEvents.map((entry, i) => (
          <VoiceBubble key={`${entry.timestamp}-${i}`} entry={entry} />
        ))}
      </div>
    </section>
  )
}

function VoiceBubble({ entry }: { entry: AgentLogEntry }) {
  const isApo =
    entry.action === 'calling' ||
    /^APO(\s+Voice Executor)?:/.test(entry.output)
  const speaker = isApo ? 'APO' : 'Clinic'
  const text = entry.output.replace(/^(APO(?: Voice Executor)?|Receptionist):\s*/, '')

  return (
    <div className={`voice-bubble voice-bubble--${isApo ? 'apo' : 'clinic'}`}>
      <span className="voice-speaker">{speaker}</span>
      <p>{text}</p>
    </div>
  )
}
