from groq import Groq
from typing import cast
import io

def transcribe(audio_bytes: bytes) -> str:
    client = Groq()
    transcription = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=("audio.ogg",audio_bytes) ,
        language="hi",
        response_format="text",
    )
    # whisper say it return object, type checker mad. me cast to string make type checker happy.
    return cast(str, transcription)