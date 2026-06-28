import os
import pytest
from src.services.audio.transcriber import transcribe

@pytest.mark.integration
def test_transcriber_integration():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    audio_path = os.path.join(base_dir, "q_audio.ogg")
    
    if not os.path.exists(audio_path):
        pytest.skip("Audio file q_audio.ogg not found, skipping transcription integration test")
        
    with open(audio_path, "rb") as f:
        text = transcribe(f.read())
    
    assert text is not None
    assert len(text) > 0