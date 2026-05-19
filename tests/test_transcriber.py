import os
from src.transcriber import transcribe

# Resolve paths relative to this script
base_dir = os.path.dirname(os.path.abspath(__file__))
audio_path = os.path.join(base_dir, "q_audio.ogg")
transcript_path = os.path.join(base_dir, "q_transcript.txt")

with open(audio_path, "rb") as f, open(transcript_path, "w") as n:
    text = transcribe(f.read())
    n.write(text)

print(f"Transcript: {text}")