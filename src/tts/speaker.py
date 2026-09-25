import os
import sys
import time
import queue
import ctypes
import asyncio
import logging
import tempfile
import threading
import urllib.parse
import requests
from typing import Optional, Callable, Dict

logger = logging.getLogger(__name__)

class TextToSpeechService:
    """
    Dịch vụ chuyển văn bản thành giọng nói (Text-to-Speech) Tiếng Việt siêu tốc (Realtime Sub-Second).
    Hỗ trợ 2 động cơ:
    1. Google Fast TTS: Tải audio cực nhanh qua HTTP keep-alive (~0.18s), gần như tức thời.
    2. Microsoft Edge Neural TTS: Giọng đọc truyền cảm, chất lượng phòng thu (Hoài My, Nam Minh).
    Kiến trúc 2 luồng: Synthesizer Worker (tải trước) và Playback Worker (phát nối tiếp không khoảng lặng).
    """
    DEFAULT_VOICE = "google-fast"
    DEFAULT_RATE = "+15%"

    VOICE_OPTIONS = {
        "google-fast": "⚡ Siêu Tốc Realtime (Google Fast - 0.2s)",
        "vi-VN-HoaiMyNeural": "👩 Giọng Nữ (Hoài My - Microsoft Neural)",
        "vi-VN-NamMinhNeural": "👨 Giọng Nam (Nam Minh - Microsoft Neural)"
    }

    RATE_OPTIONS = {
        "+0%": "1.0x (Chuẩn)",
        "+15%": "1.15x (Nhanh vừa - Khuyên dùng)",
        "+25%": "1.25x (Nhanh)",
        "+35%": "1.35x (Rất nhanh)"
    }

    def __init__(
        self,
        voice: str = DEFAULT_VOICE,
        rate: str = DEFAULT_RATE,
        enabled: bool = False,
        on_start: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[str], None]] = None
    ):
        self.voice = voice if voice in self.VOICE_OPTIONS else self.DEFAULT_VOICE
        self.rate = rate
        self.enabled = enabled
        self.on_start = on_start
        self.on_finish = on_finish

        self.is_speaking = False
        self._text_queue = queue.Queue(maxsize=10)
        self._audio_queue = queue.Queue(maxsize=10)
        self._stop_event = threading.Event()
        self._current_alias = f"tts_player_{os.getpid()}"

        # Session keep-alive để tải âm thanh siêu tốc (~180ms)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })

        # Khởi chạy 2 luồng song song: Tổng hợp âm thanh & Phát âm thanh
        self._synth_thread = threading.Thread(target=self._synth_worker_loop, daemon=True)
        self._synth_thread.start()

        self._play_thread = threading.Thread(target=self._play_worker_loop, daemon=True)
        self._play_thread.start()

    @classmethod
    def get_available_voices(cls) -> Dict[str, str]:
        """Danh sách giọng đọc Tiếng Việt có sẵn"""
        return cls.VOICE_OPTIONS.copy()

    @classmethod
    def get_available_rates(cls) -> Dict[str, str]:
        """Danh sách tốc độ đọc"""
        return cls.RATE_OPTIONS.copy()

    def set_enabled(self, enabled: bool):
        """Bật hoặc tắt tính năng phát âm thanh tiếng Việt"""
        self.enabled = enabled
        if not enabled:
            self.stop()
        logger.info(f"TTS enabled set to: {self.enabled}")

    def toggle(self) -> bool:
        """Đảo trạng thái Bật/Tắt của TTS"""
        self.set_enabled(not self.enabled)
        return self.enabled

    def set_voice(self, voice: str):
        """Đổi giọng đọc / engine"""
        if voice in self.VOICE_OPTIONS or "vi-VN" in voice or "google" in voice:
            self.voice = voice
            logger.info(f"TTS voice changed to: {self.voice}")

    def set_rate(self, rate: str):
        """Đổi tốc độ đọc"""
        self.rate = rate
        logger.info(f"TTS rate changed to: {self.rate}")

    def queue_size(self) -> int:
        """Số câu đang chờ trong hàng đợi"""
        return self._text_queue.qsize() + self._audio_queue.qsize()

    def speak(self, text: str) -> bool:
        """
        Đưa câu tiếng Việt vào hàng đợi phát âm thanh.
        Tự động bỏ bớt câu cũ nếu bị dồn ứ để giữ độ trễ luôn realtime.
        """
        if not self.enabled:
            return False

        clean_text = text.strip()
        if not clean_text:
            return False

        # Anti-lag: Nếu hàng đợi đang có trên 3 câu, bỏ bớt câu cũ nhất để bắt kịp thời gian thực
        if self._text_queue.qsize() >= 3:
            try:
                self._text_queue.get_nowait()
                self._text_queue.task_done()
            except queue.Empty:
                pass

        try:
            self._text_queue.put_nowait(clean_text)
            return True
        except queue.Full:
            return False

    def stop(self):
        """Dừng ngay âm thanh đang phát và dọn sạch toàn bộ hàng đợi"""
        while not self._text_queue.empty():
            try:
                self._text_queue.get_nowait()
                self._text_queue.task_done()
            except queue.Empty:
                break

        while not self._audio_queue.empty():
            try:
                temp_file, _ = self._audio_queue.get_nowait()
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception:
                        pass
                self._audio_queue.task_done()
            except queue.Empty:
                break

        # Tắt âm thanh MCI đang phát
        try:
            ctypes.windll.winmm.mciSendStringW(f"stop {self._current_alias}", None, 0, None)
            ctypes.windll.winmm.mciSendStringW(f"close {self._current_alias}", None, 0, None)
        except Exception:
            pass

        self.is_speaking = False

    def _synth_worker_loop(self):
        """Luồng 1: Lấy text và tải file audio trước (Prefetch) để sẵn sàng phát ngay"""
        while not self._stop_event.is_set():
            try:
                text = self._text_queue.get(timeout=0.15)
            except queue.Empty:
                continue

            if not self.enabled:
                self._text_queue.task_done()
                continue

            temp_audio_file = None
            try:
                # 1. Thử tổng hợp nhanh
                if self.voice == "google-fast":
                    temp_audio_file = self._synthesize_google_fast(text)
                else:
                    temp_audio_file = self._synthesize_edge(text)

                # Fallback nếu lỗi
                if not temp_audio_file or not os.path.exists(temp_audio_file):
                    temp_audio_file = self._synthesize_google_fast(text)

                if temp_audio_file and os.path.exists(temp_audio_file):
                    self._audio_queue.put((temp_audio_file, text))
            except Exception as e:
                logger.error(f"Error synthesizing text: {e}")
            finally:
                self._text_queue.task_done()

    def _synthesize_google_fast(self, text: str) -> Optional[str]:
        """Tải âm thanh Tiếng Việt qua Google Fast endpoint với keep-alive session (~0.18s)"""
        try:
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"fast_tts_{int(time.time() * 1000)}.mp3")
            encoded_text = urllib.parse.quote(text)
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_text}&tl=vi&client=tw-ob"

            resp = self.session.get(url, timeout=2.5)
            if resp.status_code == 200 and len(resp.content) > 0:
                with open(temp_file, "wb") as f:
                    f.write(resp.content)
                return temp_file
        except Exception as e:
            logger.debug(f"Google fast TTS error: {e}")
        return None

    def _synthesize_edge(self, text: str) -> Optional[str]:
        """Tổng hợp âm thanh bằng Microsoft Edge Neural TTS"""
        try:
            import edge_tts
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"edge_tts_{int(time.time() * 1000)}.mp3")

            async def generate():
                communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
                await communicate.save(temp_file)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(generate())
            finally:
                loop.close()

            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                return temp_file
        except Exception as e:
            logger.debug(f"Edge TTS error: {e}")
        return None

    def _play_worker_loop(self):
        """Luồng 2: Lấy file audio đã sẵn sàng và phát ngay lập tức (không chờ tải)"""
        while not self._stop_event.is_set():
            try:
                temp_audio_file, text = self._audio_queue.get(timeout=0.15)
            except queue.Empty:
                continue

            if not self.enabled:
                if os.path.exists(temp_audio_file):
                    try:
                        os.remove(temp_audio_file)
                    except Exception:
                        pass
                self._audio_queue.task_done()
                continue

            try:
                self.is_speaking = True
                if self.on_start:
                    try:
                        self.on_start(text)
                    except Exception:
                        pass

                self._play_mci(temp_audio_file)
            except Exception as e:
                logger.error(f"Error playing audio: {e}")
            finally:
                self.is_speaking = False
                if self.on_finish:
                    try:
                        self.on_finish(text)
                    except Exception:
                        pass

                # Xóa file tạm sau khi phát xong
                if os.path.exists(temp_audio_file):
                    try:
                        os.remove(temp_audio_file)
                    except Exception:
                        pass
                self._audio_queue.task_done()

    def _play_mci(self, filepath: str):
        """Phát file âm thanh bằng Windows Media Control Interface (winmm.dll)"""
        abs_path = os.path.abspath(filepath)
        alias = self._current_alias

        try:
            ctypes.windll.winmm.mciSendStringW(f"close {alias}", None, 0, None)
            res_open = ctypes.windll.winmm.mciSendStringW(
                f'open "{abs_path}" type mpegvideo alias {alias}', None, 0, None
            )
            if res_open != 0:
                logger.error(f"MCI open error code: {res_open}")
                return

            ctypes.windll.winmm.mciSendStringW(f"play {alias} wait", None, 0, None)
        finally:
            try:
                ctypes.windll.winmm.mciSendStringW(f"close {alias}", None, 0, None)
            except Exception:
                pass
