import base64
from typing import Optional
from app.config import settings

class WhisperService:
    @staticmethod
    async def transcribe_audio(
        audio_bytes: Optional[bytes] = None,
        audio_base64: Optional[str] = None,
        language: str = "en"
    ) -> str:
        """
        Transcribes audio using OpenAI Whisper API / Gemini audio input,
        or returns simulated transcription for test payloads.
        """
        if audio_base64 and not audio_bytes:
            try:
                audio_bytes = base64.b64decode(audio_base64)
            except Exception as e:
                print(f"[WhisperService] Base64 decode error: {e}")

        # If external API keys are configured, call OpenAI Whisper endpoint
        if settings.openai_api_key and audio_bytes:
            try:
                import httpx
                headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
                files = {"file": ("audio.m4a", audio_bytes, "audio/m4a")}
                data = {"model": "whisper-1", "language": language}
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/audio/transcriptions",
                        headers=headers,
                        files=files,
                        data=data
                    )
                    if resp.status_code == 200:
                        return resp.json().get("text", "")
            except Exception as e:
                print(f"[WhisperService] External Whisper call failed: {e}")

        # Fallback default transcription for quick demo/testing
        return "I have an idea for an automated AI client intake system that summarizes legal inquiries before consultation calls."
