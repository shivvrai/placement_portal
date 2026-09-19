"""
Gemini API client wrapper with streaming support.
"""

import asyncio
import logging
from typing import AsyncGenerator
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def is_gemini_configured() -> bool:
    return bool(settings.GEMINI_API_KEY)


def _sync_stream_chat(system_prompt: str, history: list[dict], user_message: str) -> list[str]:
    """
    Synchronous helper that calls Gemini and collects all chunks.
    Runs in a thread to avoid blocking the async event loop.
    """
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt,
    )

    chat_history = []
    for m in history:
        role = "model" if m["role"] == "assistant" else "user"
        chat_history.append({"role": role, "parts": [m["content"]]})

    chat = model.start_chat(history=chat_history)
    response = chat.send_message(user_message, stream=True)

    chunks = []
    for chunk in response:
        if chunk.text:
            chunks.append(chunk.text)
    return chunks


async def stream_chat(
    system_prompt: str,
    history: list[dict],
    user_message: str
) -> AsyncGenerator[str, None]:
    """
    Calls the Gemini API in a background thread and yields chunks.
    This avoids blocking the async event loop with synchronous I/O.
    """
    if not is_gemini_configured():
        yield "Gemini API key is not configured on the backend. Please add it to the .env file."
        return

    try:
        chunks = await asyncio.to_thread(
            _sync_stream_chat, system_prompt, history, user_message
        )
        for chunk in chunks:
            yield chunk
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        yield f"\n\n**Error:** An issue occurred while contacting the AI: {str(e)}"


# ======== TASK 1: Curriculum Proposal ========

def _sync_generate_content(system_prompt: str, prompt: str) -> str:
    """Synchronous helper for single generation."""
    try:
        import google.generativeai as genai
    except ImportError:
        logger.warning("google-generativeai is not installed.")
        raise RuntimeError("google-generativeai is not installed.")
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt,
    )
    
    response = model.generate_content(prompt)
    return response.text


async def generate_curriculum_proposal(system_prompt: str, prompt: str) -> str:
    """Async wrapper to call Gemini non-streaming for a JSON output."""
    if not is_gemini_configured():
        raise Exception("Gemini API key is not configured.")
        
    response = await asyncio.to_thread(_sync_generate_content, system_prompt, prompt)
    return response
