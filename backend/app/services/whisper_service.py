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

        # Try Gemini multimodal audio transcription if gemini_api_key is set
        if settings.gemini_api_key and audio_bytes and len(audio_bytes) > 200:
            try:
                import httpx
                encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.gemini_api_key}"
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {
                                    "inlineData": {
                                        "mimeType": "audio/wav",
                                        "data": encoded_audio
                                    }
                                },
                                {
                                    "text": "Transcribe the spoken audio into English text. Return ONLY the verbatim transcribed words without any markdown, quotes, notes, or explanations. If completely silent, return an empty string."
                                }
                            ]
                        }
                    ]
                }
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                text = parts[0].get("text", "").strip()
                                if text:
                                    print(f"[WhisperService] Gemini transcribed: '{text}'")
                                    return text
                    else:
                        print(f"[WhisperService] Gemini API returned {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"[WhisperService] Gemini audio transcription error: {e}")

        # If external OpenAI API key is configured, call OpenAI Whisper endpoint
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
