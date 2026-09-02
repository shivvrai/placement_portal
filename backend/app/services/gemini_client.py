"""
Gemini API client wrapper with streaming support.
"""

import logging
from typing import AsyncGenerator
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def is_gemini_configured() -> bool:
    return bool(settings.GEMINI_API_KEY)

async def stream_chat(
    system_prompt: str,
    history: list[dict],
    user_message: str
) -> AsyncGenerator[str, None]:
    """
    Calls the Gemini API and yields chunks of the response as they arrive.
    """
    if not is_gemini_configured():
        yield "Gemini API key is not configured on the backend. Please add it to the .env file."
        return

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Initialize model with system instruction
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_prompt,
        )

        # Convert history format (skip the most recent user message if it's already in history, or just use history)
        # Assuming `history` contains all past messages, NOT including `user_message`
        chat_history = []
        for m in history:
            role = "model" if m["role"] == "assistant" else "user"
            chat_history.append({"role": role, "parts": [m["content"]]})

        chat = model.start_chat(history=chat_history)
        
        # Call generate_content with stream=True
        response = chat.send_message(user_message, stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        yield f"\n\n**Error:** An issue occurred while contacting the AI: {str(e)}"
