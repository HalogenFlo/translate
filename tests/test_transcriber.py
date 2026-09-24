import pytest
import numpy as np
from src.stt.transcriber import SpeechTranscriber

def test_transcriber_initialization():
    transcriber = SpeechTranscriber(default_lang="en-US")
    assert transcriber.language == "en-US"
    transcriber.set_language("ja-JP")
    assert transcriber.language == "ja-JP"

def test_transcribe_silence():
    transcriber = SpeechTranscriber(default_lang="en-US")
    # Tạo một mảng âm thanh im lặng 1 giây ở sample_rate 16000
    silence = np.zeros(16000, dtype=np.int16)
    result = transcriber.transcribe_numpy(silence, sample_rate=16000)
    # Âm thanh im lặng phải trả về None hoặc chuỗi rỗng
    assert result is None or result == ""

def test_supported_languages():
    languages = SpeechTranscriber.get_supported_languages()
    assert isinstance(languages, dict)
    assert "en-US" in languages
    assert any("Anh" in name for name in languages.values())
