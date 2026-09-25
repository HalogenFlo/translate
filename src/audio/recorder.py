import threading
import time
import logging
from typing import Callable, List, Dict, Optional
import numpy as np
import soundcard as sc

logger = logging.getLogger(__name__)

class AudioRecorder:
    def __init__(
        self,
        on_phrase_complete: Optional[Callable[[np.ndarray, int], None]] = None,
        on_phrase_interim: Optional[Callable[[np.ndarray, int], None]] = None,
        sample_rate: int = 16000,
        energy_threshold: float = 0.012,
        silence_timeout: float = 0.28, # Siêu nhạy 0.28s để phản hồi tức thì realtime
        min_phrase_len: float = 0.20,
        max_phrase_len: float = 12.0
    ):
        self.on_phrase_complete = on_phrase_complete
        self.on_phrase_interim = on_phrase_interim
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.silence_timeout = silence_timeout
        self.min_phrase_len = min_phrase_len
        self.max_phrase_len = max_phrase_len

        self.is_running = False
        self._record_thread: Optional[threading.Thread] = None
        self.selected_device_id: Optional[str] = None
        self.is_loopback: bool = True
        self.mic_enabled: bool = False # Mặc định TẮT micro để tránh thu tiếng ồn phòng
        self.is_suppressed: bool = False # Tạm dừng thu khi TTS đang phát để chống tiếng vọng (Echo Suppression)

    def set_suppressed(self, suppressed: bool):
        """Bật/tắt tạm dừng thu âm (dùng khi TTS đang phát tiếng dịch ra loa)"""
        self.is_suppressed = suppressed

    def set_mic_enabled(self, enabled: bool):
        """Bật hoặc tắt nhận micro"""
        self.mic_enabled = enabled
        logger.info(f"Microphone enabled state: {self.mic_enabled}")

    def toggle_mic(self) -> bool:
        """Đảo trạng thái Bật/Tắt của micro"""
        self.mic_enabled = not self.mic_enabled
        logger.info(f"Microphone toggled to: {self.mic_enabled}")
        return self.mic_enabled

    @staticmethod
    def get_available_devices() -> List[Dict[str, str]]:
        """
        Liệt kê tất cả các thiết bị âm thanh:
        - Loa hệ thống (Loopback để nghe Discord, Meet, Video Youtube...)
        - Microphone
        """
        device_list = []
        try:
            # 1. Danh sách Speakers (Loopback)
            speakers = sc.all_speakers()
            for spk in speakers:
                device_list.append({
                    "id": str(spk.id),
                    "name": f"🔊 [Hệ thống/Loa] {spk.name}",
                    "raw_name": spk.name,
                    "type": "loopback"
                })

            # 2. Danh sách Microphones
            mics = sc.all_microphones(include_loopback=False)
            for mic in mics:
                device_list.append({
                    "id": str(mic.id),
                    "name": f"🎙️ [Microphone] {mic.name}",
                    "raw_name": mic.name,
                    "type": "microphone"
                })
        except Exception as e:
            logger.error(f"Error enumerating sound devices: {e}")

        return device_list

    def calculate_rms(self, audio_data: np.ndarray) -> float:
        """Tính toán RMS năng lượng âm thanh của mảng dữ liệu"""
        if audio_data is None or len(audio_data) == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(audio_data))))

    def start(self, device_id: Optional[str] = None, is_loopback: bool = True):
        """Bắt đầu luồng ghi âm ngầm"""
        if self.is_running:
            return

        self.selected_device_id = device_id
        self.is_loopback = is_loopback
        self.is_running = True
        self._record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self._record_thread.start()

    def stop(self):
        """Dừng luồng ghi âm"""
        self.is_running = False
        if self._record_thread and self._record_thread.is_alive():
            self._record_thread.join(timeout=1.5)
        self._record_thread = None

    def _record_loop(self):
        """Vòng lặp thu thập âm thanh liên tục và nhận diện khoảng ngắt câu"""
        try:
            # Chọn thiết bị capture
            if self.is_loopback:
                if self.selected_device_id:
                    mic = sc.get_microphone(id=self.selected_device_id, include_loopback=True)
                else:
                    spk = sc.default_speaker()
                    mic = sc.get_microphone(id=str(spk.id), include_loopback=True)
            else:
                if self.selected_device_id:
                    mic = sc.get_microphone(id=self.selected_device_id, include_loopback=False)
                else:
                    mic = sc.default_microphone()

            block_size = int(self.sample_rate * 0.1) # 100ms mỗi block
            phrase_buffer: List[np.ndarray] = []
            speaking = False
            last_speech_time = 0.0
            last_interim_time = 0.0
            phrase_start_time = 0.0

            with mic.recorder(samplerate=self.sample_rate, channels=1, blocksize=block_size) as recorder:
                while self.is_running:
                    # Đọc frame âm thanh
                    data = recorder.record(numframes=block_size)

                    # Nếu là Microphone mà micro đang bị TẮT thì bỏ qua hoàn toàn
                    if not self.is_loopback and not self.mic_enabled:
                        time.sleep(0.05)
                        continue

                    # Chuyển thành mono 1D
                    if data.ndim > 1:
                        mono_data = np.mean(data, axis=1)
                    else:
                        mono_data = data.flatten()

                    rms = self.calculate_rms(mono_data)
                    current_time = time.time()

                    if rms >= self.energy_threshold:
                        if not speaking:
                            speaking = True
                            phrase_start_time = current_time
                            last_interim_time = current_time
                            phrase_buffer = []
                        last_speech_time = current_time
                        phrase_buffer.append(mono_data)

                        # Định kỳ phát interim chunk để "nói tới đâu ra chữ tới đó"
                        if self.on_phrase_interim and (current_time - last_interim_time >= 0.35):
                            phrase_duration = current_time - phrase_start_time
                            if phrase_duration >= self.min_phrase_len and phrase_buffer:
                                interim_audio = np.concatenate(phrase_buffer)
                                self.on_phrase_interim(interim_audio, self.sample_rate)
                                last_interim_time = current_time
                    else:
                        if speaking:
                            # Đang trong câu thoại nhưng rơi vào khoảng nghỉ giữa các từ
                            phrase_buffer.append(mono_data)
                            silence_elapsed = current_time - last_speech_time
                            phrase_duration = current_time - phrase_start_time

                            # Nếu khoảng lặng đủ dài hoặc câu nói đã quá dài -> Chốt câu
                            if silence_elapsed >= self.silence_timeout or phrase_duration >= self.max_phrase_len:
                                if phrase_duration >= self.min_phrase_len and phrase_buffer:
                                    full_phrase = np.concatenate(phrase_buffer)
                                    if self.on_phrase_complete:
                                        self.on_phrase_complete(full_phrase, self.sample_rate)

                                speaking = False
                                phrase_buffer = []

        except Exception as e:
            logger.error(f"Error in audio record loop: {e}")
            self.is_running = False
