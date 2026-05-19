from groq import Groq
import io

def transcribe(audio_bytes: bytes) -> str:
    client = Groq()
    transcription = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=("audio.ogg",audio_bytes) ,
        language="hi",
        response_format="text",
    )
    return transcription