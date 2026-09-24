import logging
import io
import wave
from typing import Optional, Dict
import numpy as np
import speech_recognition as sr

logger = logging.getLogger(__name__)

class SpeechTranscriber:
    SUPPORTED_LANGUAGES = {
        "en-US": "Tiếng Anh (US)",
        "en-GB": "Tiếng Anh (UK)",
        "ja-JP": "Tiếng Nhật (Japanese)",
        "zh-CN": "Tiếng Trung (Chinese)",
        "ko-KR": "Tiếng Hàn (Korean)",
        "fr-FR": "Tiếng Pháp (French)",
        "de-DE": "Tiếng Đức (German)",
        "es-ES": "Tiếng Tây Ban Nha (Spanish)",
        "ru-RU": "Tiếng Nga (Russian)",
        "vi-VN": "Tiếng Việt (Vietnamese)"
    }

    def __init__(self, default_lang: str = "en-US"):
        self.language = default_lang
        self.recognizer = sr.Recognizer()
        # Cấu hình tối ưu độ nhạy âm thanh
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

    @classmethod
    def get_supported_languages(cls) -> Dict[str, str]:
        return cls.SUPPORTED_LANGUAGES.copy()

    def set_language(self, lang_code: str):
        if lang_code in self.SUPPORTED_LANGUAGES:
            self.language = lang_code
        else:
            self.language = lang_code

    def transcribe_numpy(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[str]:
        """
        Nhận mảng numpy (int16 hoặc float32) và chuyển đổi thành văn bản bằng Google Speech API.
        """
        try:
            if audio_data is None or len(audio_data) == 0:
                return None

            # Đảm bảo int16 mono
            if audio_data.dtype != np.int16:
                if np.issubdtype(audio_data.dtype, np.floating):
                    # Giới hạn trong [-1.0, 1.0] rồi nhân 32767
                    audio_data = np.clip(audio_data, -1.0, 1.0)
                    audio_data = (audio_data * 32767).astype(np.int16)
                else:
                    audio_data = audio_data.astype(np.int16)

            if audio_data.ndim > 1:
                # Chuyển stereo/multi-channel thành mono bằng trung bình cộng
                audio_data = np.mean(audio_data, axis=1).astype(np.int16)

            # Đóng gói dữ liệu thành AudioData
            raw_bytes = audio_data.tobytes()
            sr_audio = sr.AudioData(raw_bytes, sample_rate, 2) # 2 bytes = 16-bit

            text = self.recognizer.recognize_google(sr_audio, language=self.language)
            return text.strip() if text else None
        except sr.UnknownValueError:
            # Im lặng hoặc không có tiếng người nói rõ ràng
            return None
        except sr.RequestError as e:
            logger.warning(f"Google Speech Recognition Service request error: {e}")
            return None
        except Exception as e:
            logger.debug(f"Transcribe error: {e}")
            return None
