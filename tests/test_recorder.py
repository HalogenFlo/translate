import pytest
import numpy as np
from src.audio.recorder import AudioRecorder

def test_list_audio_devices():
    devices = AudioRecorder.get_available_devices()
    assert isinstance(devices, list)
    # Máy tính ít nhất phải có thiết bị output hoặc microphone
    assert len(devices) > 0
    # Phải có device type 'loopback' hoặc 'microphone'
    types = [d["type"] for d in devices]
    assert "loopback" in types or "microphone" in types

def test_calculate_rms():
    # Kiểm tra hàm tính RMS năng lượng âm thanh
    recorder = AudioRecorder()
    silence = np.zeros(1000, dtype=np.float32)
    assert recorder.calculate_rms(silence) == 0.0

    loud = np.ones(1000, dtype=np.float32) * 0.5
    assert recorder.calculate_rms(loud) > 0.4

def test_recorder_callbacks():
    received_chunks = []
    def on_audio_chunk(audio_data, sr):
        received_chunks.append((audio_data, sr))

    recorder = AudioRecorder(on_phrase_complete=on_audio_chunk)
    assert recorder.is_running is False

def test_mic_toggle():
    recorder = AudioRecorder()
    # Mặc định mic_enabled là False (ưu tiên nghe Loa máy tính / Discord / Meet)
    assert recorder.mic_enabled is False

    # Bật micro
    recorder.set_mic_enabled(True)
    assert recorder.mic_enabled is True

    # Toggle micro
    new_state = recorder.toggle_mic()
    assert new_state is False
    assert recorder.mic_enabled is False

def test_recorder_interim_callback():
    interim_calls = []
    def on_interim(audio_data, sr):
        interim_calls.append(audio_data)

    recorder = AudioRecorder(on_phrase_interim=on_interim)
    assert recorder.on_phrase_interim is not None
    assert recorder.silence_timeout <= 0.4 # Độ trễ thấp

def test_recorder_suppress_echo():
    recorder = AudioRecorder()
    assert recorder.is_suppressed is False
    recorder.set_suppressed(True)
    assert recorder.is_suppressed is True
    recorder.set_suppressed(False)
    assert recorder.is_suppressed is False


