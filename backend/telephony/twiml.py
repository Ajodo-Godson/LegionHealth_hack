"""Generate TwiML for Twilio outbound calls."""

from __future__ import annotations


def outbound_twiml(run_id: str, public_base_url: str) -> str:
    """Simple TwiML — connects call; full Grok bridge can attach to media stream URL."""
    stream_url = public_base_url.replace("https://", "wss://").replace("http://", "ws://")
    stream_url = f"{stream_url}/api/twilio/media/{run_id}"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna">This is A P O calling on behalf of a patient to verify insurance coverage.</Say>
  <Pause length="1"/>
  <Say voice="Polly.Joanna">Connecting verification agent.</Say>
  <Connect>
    <Stream url="{stream_url}" />
  </Connect>
</Response>"""
