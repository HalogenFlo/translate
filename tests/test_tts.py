import pytest
import time
from unittest.mock import MagicMock, patch
from src.tts.speaker import TextToSpeechService

def test_tts_initialization():
    service = TextToSpeechService()
    assert service.enabled is False # Mặc định tắt để người dùng chủ động bật
    assert "google" in service.voice or "vi-VN" in service.voice
    assert service.rate in ["+0%", "+15%", "+20%", "+25%"]
    assert service.is_speaking is False

def test_tts_available_voices():
    voices = TextToSpeechService.get_available_voices()
    assert isinstance(voices, dict)
    assert len(voices) >= 3
    # Phải có Google Fast và giọng Neural Hoài My, Nam Minh
    assert "google-fast" in voices
    assert any("HoaiMy" in k for k in voices.keys())
    assert any("NamMinh" in k for k in voices.keys())

def test_tts_toggle_and_set_enabled():
    service = TextToSpeechService()
    assert service.enabled is False
    new_state = service.toggle()
    assert new_state is True
    assert service.enabled is True
    service.set_enabled(False)
    assert service.enabled is False

def test_tts_set_voice_and_rate():
    service = TextToSpeechService()
    service.set_voice("vi-VN-NamMinhNeural")
    assert service.voice == "vi-VN-NamMinhNeural"
    service.set_rate("+20%")
    assert service.rate == "+20%"

def test_tts_speak_when_disabled():
    service = TextToSpeechService()
    service.set_enabled(False)
    # Khi disabled, gọi speak không đưa vào hàng đợi xử lý
    success = service.speak("Xin chào bạn")
    assert success is False
    assert service.queue_size() == 0

def test_tts_speak_empty_text():
    service = TextToSpeechService()
    service.set_enabled(True)
    assert service.speak("") is False
    assert service.speak("   ") is False
    assert service.queue_size() == 0

def test_tts_speak_queueing():
    service = TextToSpeechService()
    service.set_enabled(True)
    with patch.object(service, '_synthesize_google_fast', return_value=None):
        success = service.speak("Xin chào các bạn")
        assert success is True
        service.stop()

def test_tts_stop_and_clear():
    service = TextToSpeechService()
    service.set_enabled(True)
    service.stop()
    assert service.is_speaking is False
    assert service.queue_size() == 0
