"""xAI Grok text client — OpenAI-compatible chat completions."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BACKEND_DIR / ".env")
load_dotenv()

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1").rstrip("/")
XAI_TEXT_MODEL = os.getenv("XAI_TEXT_MODEL", "grok-3")
REQUEST_TIMEOUT = float(os.getenv("XAI_REQUEST_TIMEOUT", "120"))


def has_api_key() -> bool:
    return bool(XAI_API_KEY.strip())


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def _headers() -> dict[str, str]:
    if not has_api_key():
        raise RuntimeError("XAI_API_KEY is not set")
    return {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json",
    }


async def chat(
    system_prompt: str,
    user_message: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 600,
) -> str:
    """Single-turn chat completion."""
    payload = {
        "model": XAI_TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.post(
            f"{XAI_BASE_URL}/chat/completions",
            headers=_headers(),
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Empty response from xAI chat completions")
    return content.strip()


async def chat_json(
    system_prompt: str,
    user_message: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 1200,
) -> dict:
    """Chat completion that returns parsed JSON."""
    payload = {
        "model": XAI_TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.post(
            f"{XAI_BASE_URL}/chat/completions",
            headers=_headers(),
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    return _parse_json_content(content)


def _parse_json_content(content: str) -> dict:
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        text = fence.group(1).strip()
    return json.loads(text)
