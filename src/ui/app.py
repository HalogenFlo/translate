import os
import sys
import time
import threading
import queue
from datetime import datetime
from typing import Optional, Dict, List
import customtkinter as ctk
import pyperclip

from src.audio.recorder import AudioRecorder
from src.stt.transcriber import SpeechTranscriber
from src.translator.service import TranslatorService

# Thiết lập theme mặc định hiện đại
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SubtitleCard(ctk.CTkFrame):
    """Component hiển thị một khối phụ đề song ngữ với các nút copy nhanh"""
    def __init__(self, master, original_text: str, translated_text: str, timestamp_str: str, **kwargs):
        super().__init__(master, corner_radius=10, fg_color="#1e222d", border_width=1, border_color="#2e384d", **kwargs)
        self.original_text = original_text
        self.translated_text = translated_text

        # Layout trong card
        self.grid_columnconfigure(0, weight=1)

        # Header: Timestamp
        self.lbl_time = ctk.CTkLabel(
            self,
            text=f"⏱️ {timestamp_str}",
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color="#8b9bb4",
            anchor="w"
        )
        self.lbl_time.grid(row=0, column=0, padx=12, pady=(8, 2), sticky="w")

        # Original Text (Tiếng gốc)
        self.lbl_original = ctk.CTkLabel(
            self,
            text=f"🌐 {original_text}",
            font=ctk.CTkFont(size=14, weight="normal"),
            text_color="#d1d9e6",
            wraplength=520,
            justify="left",
            anchor="w"
        )
        self.lbl_original.grid(row=1, column=0, padx=12, pady=2, sticky="w")

        # Translated Text (Tiếng Việt)
        self.lbl_translated = ctk.CTkLabel(
            self,
            text=f"🇻🇳 {translated_text}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#4ade80", # Xanh lá hiện đại nổi bật
            wraplength=520,
            justify="left",
            anchor="w"
        )
        self.lbl_translated.grid(row=2, column=0, padx=12, pady=4, sticky="w")

        # Action Buttons bar
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=3, column=0, padx=12, pady=(4, 8), sticky="w")

        self.btn_copy_orig = ctk.CTkButton(
            self.btn_frame,
            text="📋 Copy Gốc",
            width=95,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#2d3748",
            hover_color="#3b4a62",
            command=self._copy_original
        )
        self.btn_copy_orig.pack(side="left", padx=(0, 6))

        self.btn_copy_trans = ctk.CTkButton(
            self.btn_frame,
            text="📋 Copy Tiếng Việt",
            width=120,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#15803d",
            hover_color="#16a34a",
            command=self._copy_translated
        )
        self.btn_copy_trans.pack(side="left", padx=6)

        self.btn_copy_both = ctk.CTkButton(
            self.btn_frame,
            text="📋 Copy Cả 2",
            width=95,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#475569",
            hover_color="#64748b",
            command=self._copy_both
        )
        self.btn_copy_both.pack(side="left", padx=6)

    def _flash_button(self, button, original_text: str):
        button.configure(text="✓ Đã Copy!", fg_color="#059669")
        self.after(1000, lambda: button.configure(
            text=original_text,
            fg_color="#2d3748" if "Gốc" in original_text else ("#15803d" if "Việt" in original_text else "#475569")
        ))

    def _copy_original(self):
        pyperclip.copy(self.original_text)
        self._flash_button(self.btn_copy_orig, "📋 Copy Gốc")

    def _copy_translated(self):
        pyperclip.copy(self.translated_text)
        self._flash_button(self.btn_copy_trans, "📋 Copy Tiếng Việt")

    def _copy_both(self):
        content = f"{self.original_text}\n{self.translated_text}"
        pyperclip.copy(content)
        self._flash_button(self.btn_copy_both, "📋 Copy Cả 2")


class ToolListenApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ToolListen - Live Audio Subtitle & Fast Translator")
        self.geometry("680x780")
        self.minsize(500, 480)

        # Trạng thái & Services
        self.transcriber = SpeechTranscriber(default_lang="en-US")
        self.translator = TranslatorService()
        self.audio_queue = queue.Queue()
        self.interim_queue = queue.Queue(maxsize=1)
        self.result_queue = queue.Queue()
        self.interim_result_queue = queue.Queue()

        self.is_listening = False
        self.is_always_on_top = True

        # Câu nói mới nhất để phục vụ Copy tức thì
        self.latest_original = ""
        self.latest_translated = ""

        # Thiết lập cửa sổ luôn trên cùng mặc định
        self.attributes("-topmost", True)

        # Lịch sử lưu trữ
        self.history: List[Dict[str, str]] = []
        self.audio_devices: List[Dict[str, str]] = []

        # Khởi tạo recorder với độ trễ thấp & hỗ trợ interim streaming
        self.recorder = AudioRecorder(
            on_phrase_complete=self._on_phrase_complete,
            on_phrase_interim=self._on_phrase_interim,
            sample_rate=16000,
            energy_threshold=0.012,
            silence_timeout=0.35, # Dứt câu 0.35s là chốt ngay
            min_phrase_len=0.25
        )

        # Xây dựng giao diện
        self._build_ui()

        # Đăng ký phím tắt Copy siêu tốc
        self.bind("<F2>", lambda e: self._copy_latest_original())
        self.bind("<F3>", lambda e: self._copy_latest_translated())
        self.bind("<F4>", lambda e: self._copy_all_history())

        # Tải danh sách thiết bị
        self._load_devices()

        # Bắt đầu worker threads
        self.worker_thread = threading.Thread(target=self._process_audio_worker, daemon=True)
        self.worker_thread.start()

        self.interim_thread = threading.Thread(target=self._process_interim_worker, daemon=True)
        self.interim_thread.start()

        # Bắt đầu UI update loops
        self.after(50, self._check_queues)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) # Khu vực scrollable subtitles

        # 1. Top Bar: Header & Always on Top Toggle
        self.top_frame = ctk.CTkFrame(self, fg_color="#181b22", corner_radius=0, height=48)
        self.top_frame.grid(row=0, column=0, sticky="ew")
        self.top_frame.grid_columnconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(
            self.top_frame,
            text="🎧 ToolListen Live Subtitle",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#38bdf8"
        )
        self.lbl_title.grid(row=0, column=0, padx=16, pady=8, sticky="w")

        # Nút Ghim Always on Top
        self.btn_pin = ctk.CTkButton(
            self.top_frame,
            text="📌 Ghim trên cùng: BẬT",
            width=140,
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self._toggle_always_on_top
        )
        self.btn_pin.grid(row=0, column=1, padx=12, pady=8, sticky="e")

        # 2. Control Panel
        self.ctrl_frame = ctk.CTkFrame(self, fg_color="#13161c", corner_radius=10)
        self.ctrl_frame.grid(row=1, column=0, padx=12, pady=(6, 4), sticky="ew")
        self.ctrl_frame.grid_columnconfigure(1, weight=1)

        # Hàng 1: Nguồn âm thanh
        lbl_dev = ctk.CTkLabel(self.ctrl_frame, text="Nguồn âm thanh:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_dev.grid(row=0, column=0, padx=12, pady=5, sticky="w")

        self.device_combo = ctk.CTkComboBox(
            self.ctrl_frame,
            values=["Đang quét thiết bị..."],
            width=380,
            command=self._on_device_changed
        )
        self.device_combo.grid(row=0, column=1, padx=12, pady=5, sticky="ew")

        # Hàng 2: Ngôn ngữ nguồn
        lbl_lang = ctk.CTkLabel(self.ctrl_frame, text="Ngôn ngữ nói:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_lang.grid(row=1, column=0, padx=12, pady=5, sticky="w")

        self.lang_map = SpeechTranscriber.get_supported_languages()
        lang_names = list(self.lang_map.values())
        self.lang_combo = ctk.CTkComboBox(
            self.ctrl_frame,
            values=lang_names,
            width=380,
            command=self._on_language_changed
        )
        self.lang_combo.set("Tiếng Anh (US)")
        self.lang_combo.grid(row=1, column=1, padx=12, pady=5, sticky="ew")

        # Hàng 3: Động cơ Dịch thuật (Local AI vs Cloud)
        lbl_engine = ctk.CTkLabel(self.ctrl_frame, text="Động cơ AI:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_engine.grid(row=2, column=0, padx=12, pady=5, sticky="w")

        self.engine_combo = ctk.CTkComboBox(
            self.ctrl_frame,
            values=["🤖 Model AI Cục Bộ (Offline 100% trên máy)", "🌐 Cloud API (MyMemory / Google)"],
            width=380,
            command=self._on_engine_changed
        )
        self.engine_combo.set("🤖 Model AI Cục Bộ (Offline 100% trên máy)")
        self.engine_combo.grid(row=2, column=1, padx=12, pady=5, sticky="ew")

        # Hàng 4: Trạng thái Micro
        self.lbl_mic_info = ctk.CTkLabel(
            self.ctrl_frame,
            text="🔒 Trạng thái Micro: Đã TẮT (Chỉ nghe âm thanh máy tính từ Discord/Meet/Video, không lẫn tiếng phòng)",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8"
        )
        self.lbl_mic_info.grid(row=3, column=0, columnspan=2, padx=12, pady=(1, 4), sticky="w")

        # Hàng 5: Các nút điều khiển chính
        self.action_frame = ctk.CTkFrame(self.ctrl_frame, fg_color="transparent")
        self.action_frame.grid(row=4, column=0, columnspan=2, padx=12, pady=(4, 8), sticky="ew")

        self.btn_listen = ctk.CTkButton(
            self.action_frame,
            text="▶ BẮT ĐẦU NGHE",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=34,
            command=self._toggle_listening
        )
        self.btn_listen.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_mic = ctk.CTkButton(
            self.action_frame,
            text="🎙️ Micro: TẮT",
            width=105,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#475569",
            hover_color="#334155",
            command=self._toggle_mic
        )
        self.btn_mic.pack(side="left", padx=4)

        self.btn_clear = ctk.CTkButton(
            self.action_frame,
            text="🗑️ Xóa",
            width=70,
            height=34,
            font=ctk.CTkFont(size=12),
            fg_color="#374151",
            hover_color="#4b5563",
            command=self._clear_subtitles
        )
        self.btn_clear.pack(side="left", padx=4)

        self.btn_export = ctk.CTkButton(
            self.action_frame,
            text="💾 Xuất TXT",
            width=85,
            height=34,
            font=ctk.CTkFont(size=12),
            fg_color="#374151",
            hover_color="#4b5563",
            command=self._export_history
        )
        self.btn_export.pack(side="left", padx=(4, 0))

        # 3. Quick Instant-Copy Bar (Bấm 1 nút hoặc F2/F3 là copy ngay lập tức!)
        self.quick_bar = ctk.CTkFrame(self, fg_color="#1a1e29", corner_radius=8, border_width=1, border_color="#2a3347")
        self.quick_bar.grid(row=2, column=0, padx=12, pady=(2, 6), sticky="ew")
        self.quick_bar.grid_columnconfigure(0, weight=1)

        # Hàng nút Copy siêu tốc
        self.quick_btn_frame = ctk.CTkFrame(self.quick_bar, fg_color="transparent")
        self.quick_btn_frame.pack(fill="x", padx=8, pady=6)

        self.btn_quick_orig = ctk.CTkButton(
            self.quick_btn_frame,
            text="⚡ COPY GỐC VỪA NÓI [F2]",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            height=32,
            command=self._copy_latest_original
        )
        self.btn_quick_orig.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_quick_trans = ctk.CTkButton(
            self.quick_btn_frame,
            text="⚡ COPY DỊCH TIẾNG VIỆT [F3]",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=32,
            command=self._copy_latest_translated
        )
        self.btn_quick_trans.pack(side="left", fill="x", expand=True, padx=4)

        # Hàng nút Copy Tất Cả Lịch Sử (F4)
        self.all_copy_frame = ctk.CTkFrame(self.quick_bar, fg_color="transparent")
        self.all_copy_frame.pack(fill="x", padx=8, pady=(0, 6))

        self.btn_copy_all = ctk.CTkButton(
            self.all_copy_frame,
            text="📑 COPY TẤT CẢ (LỊCH SỬ) [F4]",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#7c3aed", # Màu tím nổi bật
            hover_color="#6d28d9",
            height=30,
            command=self._copy_all_history
        )
        self.btn_copy_all.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_copy_all_vi = ctk.CTkButton(
            self.all_copy_frame,
            text="🇻🇳 CHỈ COPY TOÀN BỘ TIẾNG VIỆT",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0d9488", # Xanh ngọc
            hover_color="#0f766e",
            height=30,
            command=self._copy_all_vietnamese
        )
        self.btn_copy_all_vi.pack(side="left", fill="x", expand=True, padx=4)

        # Checkbox Auto-Copy to Clipboard
        self.auto_copy_var = ctk.BooleanVar(value=False)
        self.chk_auto_copy = ctk.CTkCheckBox(
            self.quick_bar,
            text="⚡ Tự động đưa câu dịch vào Clipboard ngay khi nói xong (chỉ cần Ctrl+V)",
            variable=self.auto_copy_var,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38bdf8",
            checkmark_color="#ffffff",
            fg_color="#0284c7"
        )
        self.chk_auto_copy.pack(anchor="w", padx=10, pady=(0, 6))

        # Khung Phụ Đề Trực Tiếp Live (Nói tới đâu xuất chữ tới đó!)
        self.live_frame = ctk.CTkFrame(self.quick_bar, fg_color="#11141c", corner_radius=6, border_width=1, border_color="#3b4252")
        self.live_frame.pack(fill="x", padx=8, pady=(0, 8))

        self.lbl_live_title = ctk.CTkLabel(
            self.live_frame,
            text="🔴 Đang nói trực tiếp (Live Stream):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#ef4444",
            anchor="w"
        )
        self.lbl_live_title.pack(anchor="w", padx=10, pady=(4, 0))

        self.lbl_live_orig = ctk.CTkLabel(
            self.live_frame,
            text="🎧 Chờ âm thanh từ video / cuộc gọi...",
            font=ctk.CTkFont(size=13, weight="normal"),
            text_color="#cbd5e1",
            anchor="w",
            justify="left",
            wraplength=600
        )
        self.lbl_live_orig.pack(fill="x", padx=10, pady=2)

        self.lbl_live_trans = ctk.CTkLabel(
            self.live_frame,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#4ade80",
            anchor="w",
            justify="left",
            wraplength=600
        )
        self.lbl_live_trans.pack(fill="x", padx=10, pady=(0, 4))

        # 4. Subtitles Display Area (Scrollable History)
        self.subtitles_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="#0f1117",
            label_text="Lịch sử phụ đề & bản dịch:",
            label_font=ctk.CTkFont(size=12, weight="bold"),
            label_text_color="#94a3b8"
        )
        self.subtitles_scroll.grid(row=3, column=0, padx=12, pady=(0, 6), sticky="nsew")
        self.subtitles_scroll.grid_columnconfigure(0, weight=1)

        self.placeholder_lbl = ctk.CTkLabel(
            self.subtitles_scroll,
            text="👉 Bấm '▶ BẮT ĐẦU NGHE' rồi mở Video YouTube, Discord hoặc Meet.\nChữ sẽ xuất hiện trực tiếp ngay khi nói và lưu vào danh sách bên dưới.",
            font=ctk.CTkFont(size=13),
            text_color="#64748b",
            justify="center"
        )
        self.placeholder_lbl.pack(pady=35)

        # 5. Status Bar
        self.status_bar = ctk.CTkFrame(self, fg_color="#181b22", corner_radius=0, height=28)
        self.status_bar.grid(row=4, column=0, sticky="ew")
        self.status_bar.grid_columnconfigure(0, weight=1)

        self.lbl_status = ctk.CTkLabel(
            self.status_bar,
            text="Trạng thái: 🔴 Đang dừng",
            font=ctk.CTkFont(size=11),
            text_color="#9ca3af"
        )
        self.lbl_status.grid(row=0, column=0, padx=12, pady=4, sticky="w")

        self.lbl_count = ctk.CTkLabel(
            self.status_bar,
            text="Tổng câu: 0 | Phím tắt: F2 (Gốc), F3 (Dịch), F4 (Tất cả)",
            font=ctk.CTkFont(size=11),
            text_color="#9ca3af"
        )
        self.lbl_count.grid(row=0, column=1, padx=12, pady=4, sticky="e")

    def _copy_latest_original(self):
        """Sao chép ngay lập tức câu gốc mới nhất"""
        text = self.latest_original.strip()
        if not text:
            # Nếu chưa có câu chốt, thử lấy câu đang nói dở từ Live Banner
            live_txt = self.lbl_live_orig.cget("text")
            if live_txt and not live_txt.startswith("🎧"):
                text = live_txt.strip()

        if text:
            pyperclip.copy(text)
            self._flash_quick_button(self.btn_quick_orig, "⚡ COPY GỐC VỪA NÓI [F2]")
            self.lbl_status.configure(text=f"✓ Đã copy câu gốc: \"{text[:30]}...\"", text_color="#38bdf8")

    def _copy_latest_translated(self):
        """Sao chép ngay lập tức bản dịch tiếng Việt mới nhất"""
        text = self.latest_translated.strip()
        if not text:
            live_txt = self.lbl_live_trans.cget("text")
            if live_txt:
                text = live_txt.strip()

        if text:
            pyperclip.copy(text)
            self._flash_quick_button(self.btn_quick_trans, "⚡ COPY DỊCH TIẾNG VIỆT [F3]")
            self.lbl_status.configure(text=f"✓ Đã copy tiếng Việt: \"{text[:30]}...\"", text_color="#4ade80")

    @staticmethod
    def format_history_text(history: List[Dict[str, str]], mode: str = "both") -> str:
        """Định dạng toàn bộ lịch sử để copy vào Clipboard"""
        if not history:
            return ""

        if mode == "vi_only":
            lines = [item["translated"].strip() for item in history if item.get("translated") and item["translated"].strip()]
            return "\n".join(lines)

        # Mode both: song ngữ kèm mốc thời gian
        blocks = []
        for item in history:
            t = item.get("time", "")
            orig = item.get("original", "").strip()
            trans = item.get("translated", "").strip()
            blocks.append(f"[{t}]\nGốc: {orig}\nDịch: {trans}")
        return "\n\n".join(blocks)

    def _copy_all_history(self):
        """Sao chép toàn bộ lịch sử phụ đề song ngữ vào Clipboard"""
        if not self.history:
            self.lbl_status.configure(text="⚠️ Chưa có phụ đề nào trong lịch sử để copy!", text_color="#f59e0b")
            return

        text = self.format_history_text(self.history, mode="both")
        pyperclip.copy(text)
        self.btn_copy_all.configure(text=f"✓ ĐÃ COPY TẤT CẢ ({len(self.history)} CÂU)!", fg_color="#10b981")
        self.after(1200, lambda: self.btn_copy_all.configure(text="📑 COPY TẤT CẢ (LỊCH SỬ) [F4]", fg_color="#7c3aed"))
        self.lbl_status.configure(text=f"✓ Đã copy toàn bộ {len(self.history)} câu song ngữ vào Clipboard!", text_color="#38bdf8")

    def _copy_all_vietnamese(self):
        """Sao chép toàn bộ phần dịch Tiếng Việt vào Clipboard"""
        if not self.history:
            self.lbl_status.configure(text="⚠️ Chưa có phụ đề nào trong lịch sử để copy!", text_color="#f59e0b")
            return

        text = self.format_history_text(self.history, mode="vi_only")
        pyperclip.copy(text)
        self.btn_copy_all_vi.configure(text="✓ ĐÃ COPY TOÀN BỘ TIẾNG VIỆT!", fg_color="#10b981")
        self.after(1200, lambda: self.btn_copy_all_vi.configure(text="🇻🇳 CHỈ COPY TOÀN BỘ TIẾNG VIỆT", fg_color="#0d9488"))
        self.lbl_status.configure(text=f"✓ Đã copy toàn bộ {len(self.history)} câu tiếng Việt vào Clipboard!", text_color="#4ade80")

    def _flash_quick_button(self, btn, orig_text: str):
        btn.configure(text="✓ ĐÃ COPY VÀO CLIPBOARD!", fg_color="#10b981")
        self.after(900, lambda: btn.configure(
            text=orig_text,
            fg_color="#2563eb" if "F2" in orig_text else "#059669"
        ))

    def _load_devices(self):
        self.audio_devices = AudioRecorder.get_available_devices()
        display_names = [d["name"] for d in self.audio_devices]

        if display_names:
            self.device_combo.configure(values=display_names)
            default_index = 0
            for i, d in enumerate(self.audio_devices):
                if d["type"] == "loopback":
                    default_index = i
                    break
            self.device_combo.set(display_names[default_index])
        else:
            self.device_combo.configure(values=["Không tìm thấy thiết bị"])

    def _get_selected_device(self) -> Optional[Dict[str, str]]:
        current_name = self.device_combo.get()
        for d in self.audio_devices:
            if d["name"] == current_name:
                return d
        return None

    def _on_device_changed(self, choice):
        dev = self._get_selected_device()
        if dev and dev["type"] == "microphone":
            self.recorder.set_mic_enabled(True)
            self.btn_mic.configure(text="🎙️ Micro: BẬT", fg_color="#059669", hover_color="#047857")
            self.lbl_mic_info.configure(text="🟢 Micro ĐANG BẬT: Đang nhận giọng nói từ Microphone của bạn", text_color="#4ade80")
        else:
            self.recorder.set_mic_enabled(False)
            self.btn_mic.configure(text="🎙️ Micro: TẮT", fg_color="#475569", hover_color="#334155")
            self.lbl_mic_info.configure(text="🔒 Micro ĐÃ TẮT: Chỉ nghe âm thanh máy tính (Discord, Meet, Video)", text_color="#94a3b8")

        if self.is_listening:
            self._stop_listening()
            self._start_listening()

    def _on_engine_changed(self, choice):
        use_local = "Local AI" in choice or "Cục Bộ" in choice
        self.translator.set_engine_mode(use_local_ai=use_local)
        if use_local:
            self.lbl_status.configure(text="Đã kích hoạt: 🤖 Model AI Cục Bộ (Dịch Offline 100% trên máy)", text_color="#38bdf8")
        else:
            self.lbl_status.configure(text="Đã chuyển sang: 🌐 Cloud API (MyMemory / Google)", text_color="#fbbf24")

    def _toggle_mic(self):
        new_state = self.recorder.toggle_mic()
        dev = self._get_selected_device()
        is_mic_selected = dev and dev["type"] == "microphone"

        if new_state:
            self.btn_mic.configure(text="🎙️ Micro: BẬT", fg_color="#059669", hover_color="#047857")
            self.lbl_mic_info.configure(text="🟢 Micro ĐANG BẬT: Đang nhận giọng nói từ Microphone của bạn", text_color="#4ade80")
            if not is_mic_selected:
                for d in self.audio_devices:
                    if d["type"] == "microphone":
                        self.device_combo.set(d["name"])
                        if self.is_listening:
                            self._stop_listening()
                            self._start_listening()
                        break
        else:
            self.btn_mic.configure(text="🎙️ Micro: TẮT", fg_color="#475569", hover_color="#334155")
            self.lbl_mic_info.configure(text="🔒 Micro ĐÃ TẮT: Chỉ nghe âm thanh máy tính (Discord, Meet, Video)", text_color="#94a3b8")
            if is_mic_selected:
                for d in self.audio_devices:
                    if d["type"] == "loopback":
                        self.device_combo.set(d["name"])
                        if self.is_listening:
                            self._stop_listening()
                            self._start_listening()
                        break

    def _on_language_changed(self, choice):
        for code, name in self.lang_map.items():
            if name == choice:
                self.transcriber.set_language(code)
                break

    def _toggle_always_on_top(self):
        self.is_always_on_top = not self.is_always_on_top
        self.attributes("-topmost", self.is_always_on_top)
        if self.is_always_on_top:
            self.btn_pin.configure(text="📌 Ghim trên cùng: BẬT", fg_color="#0284c7")
        else:
            self.btn_pin.configure(text="📌 Ghim trên cùng: TẮT", fg_color="#475569")

    def _toggle_listening(self):
        if not self.is_listening:
            self._start_listening()
        else:
            self._stop_listening()

    def _start_listening(self):
        dev = self._get_selected_device()
        device_id = dev["id"] if dev else None
        is_loopback = (dev["type"] == "loopback") if dev else True

        self.recorder.start(device_id=device_id, is_loopback=is_loopback)
        self.is_listening = True
        self.btn_listen.configure(text="⏸ TẠM DỪNG (PAUSE)", fg_color="#ef4444", hover_color="#dc2626")
        dev_desc = dev["raw_name"] if dev else "Mặc định"
        self.lbl_status.configure(text=f"Trạng thái: 🟢 Đang nghe ({dev_desc})", text_color="#4ade80")
        self.lbl_live_orig.configure(text="🎧 Đang lắng nghe giọng nói...", text_color="#38bdf8")

    def _stop_listening(self):
        self.recorder.stop()
        self.is_listening = False
        self.btn_listen.configure(text="▶ BẮT ĐẦU NGHE", fg_color="#10b981", hover_color="#059669")
        self.lbl_status.configure(text="Trạng thái: 🔴 Đang dừng", text_color="#9ca3af")
        self.lbl_live_orig.configure(text="🎧 Đã tạm dừng nghe", text_color="#94a3b8")
        self.lbl_live_trans.configure(text="")

    def _on_phrase_complete(self, audio_data, sample_rate):
        """Callback khi câu nói kết thúc"""
        self.audio_queue.put((audio_data, sample_rate))

    def _on_phrase_interim(self, audio_data, sample_rate):
        """Callback khi đang nói (để xuất chữ tức thời)"""
        try:
            # Bỏ bớt frame cũ nếu worker đang bận
            if self.interim_queue.full():
                try:
                    self.interim_queue.get_nowait()
                except queue.Empty:
                    pass
            self.interim_queue.put_nowait((audio_data, sample_rate))
        except Exception:
            pass

    def _process_interim_worker(self):
        """Worker xử lý audio interim để nói tới đâu ra chữ tới đó"""
        while True:
            try:
                audio_data, sr = self.interim_queue.get()
                text = self.transcriber.transcribe_numpy(audio_data, sample_rate=sr)
                if text and len(text.strip()) > 0:
                    src_code = self.transcriber.language.split("-")[0]
                    trans = self.translator.translate(text, source_lang=src_code, target_lang="vi")
                    self.interim_result_queue.put({"original": text, "translated": trans})
                self.interim_queue.task_done()
            except Exception:
                time.sleep(0.05)

    def _process_audio_worker(self):
        """Worker xử lý chốt câu hoàn chỉnh khi người nói ngắt nghỉ"""
        while True:
            try:
                audio_data, sr = self.audio_queue.get()
                original_text = self.transcriber.transcribe_numpy(audio_data, sample_rate=sr)
                if original_text and len(original_text.strip()) > 0:
                    src_code = self.transcriber.language.split("-")[0]
                    translated_text = self.translator.translate(original_text, source_lang=src_code, target_lang="vi")

                    now_str = datetime.now().strftime("%H:%M:%S")
                    self.result_queue.put({
                        "original": original_text,
                        "translated": translated_text,
                        "timestamp": now_str
                    })
                self.audio_queue.task_done()
            except Exception:
                time.sleep(0.05)

    def _check_queues(self):
        """Kiểm tra và cập nhật giao diện theo thời gian thực"""
        try:
            # 1. Cập nhật chữ đang nói trực tiếp (Live Interim)
            while not self.interim_result_queue.empty():
                item = self.interim_result_queue.get_nowait()
                self.lbl_live_orig.configure(text=f"🗣️ {item['original']}", text_color="#f8fafc")
                if item["translated"]:
                    self.lbl_live_trans.configure(text=f"🇻🇳 {item['translated']}", text_color="#4ade80")
                self.interim_result_queue.task_done()

            # 2. Cập nhật câu hoàn chỉnh chốt vào lịch sử
            while not self.result_queue.empty():
                item = self.result_queue.get_nowait()
                self.latest_original = item["original"]
                self.latest_translated = item["translated"]

                # Nếu bật Auto-copy -> Tự động copy câu dịch mới nhất
                if self.auto_copy_var.get() and item["translated"]:
                    pyperclip.copy(item["translated"])
                    self.lbl_status.configure(text=f"⚡ Auto-Copied: \"{item['translated'][:25]}...\"", text_color="#38bdf8")

                self._add_subtitle_card(item["original"], item["translated"], item["timestamp"])

                # Cập nhật Live Banner về trạng thái chờ câu kế tiếp
                self.lbl_live_orig.configure(text="🎧 Đang lắng nghe...", text_color="#38bdf8")
                self.lbl_live_trans.configure(text="")
                self.result_queue.task_done()
        except Exception:
            pass
        finally:
            self.after(50, self._check_queues)

    def _add_subtitle_card(self, original: str, translated: str, timestamp_str: str):
        if self.placeholder_lbl.winfo_exists():
            self.placeholder_lbl.destroy()

        card = SubtitleCard(
            self.subtitles_scroll,
            original_text=original,
            translated_text=translated,
            timestamp_str=timestamp_str
        )
        card.pack(fill="x", pady=5, padx=4)

        self.history.append({
            "time": timestamp_str,
            "original": original,
            "translated": translated
        })

        self.lbl_count.configure(text=f"Tổng câu: {len(self.history)} | Phím tắt: F2 (Gốc), F3 (Dịch), F4 (Tất cả)")

    def _clear_subtitles(self):
        self.history.clear()
        self.latest_original = ""
        self.latest_translated = ""
        for child in self.subtitles_scroll.winfo_children():
            child.destroy()

        self.placeholder_lbl = ctk.CTkLabel(
            self.subtitles_scroll,
            text="👉 Bấm '▶ BẮT ĐẦU NGHE' rồi mở Video YouTube, Discord hoặc Meet.\nChữ sẽ xuất hiện trực tiếp ngay khi nói và lưu vào danh sách bên dưới.",
            font=ctk.CTkFont(size=13),
            text_color="#64748b",
            justify="center"
        )
        self.placeholder_lbl.pack(pady=35)
        self.lbl_count.configure(text="Tổng câu: 0 | Phím tắt: F2 (Gốc), F3 (Dịch), F4 (Tất cả)")

    def _export_history(self):
        if not self.history:
            return

        export_path = os.path.join(os.path.dirname(__file__), "..", "..", "subtitle_history.txt")
        export_path = os.path.abspath(export_path)
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(f"=== TOOL LISTEN - LỊCH SỬ PHỤ ĐỀ ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===\n\n")
            for item in self.history:
                f.write(f"[{item['time']}]\n")
                f.write(f"Gốc: {item['original']}\n")
                f.write(f"Dịch: {item['translated']}\n")
                f.write("-" * 40 + "\n")

        self.lbl_status.configure(text=f"✓ Đã xuất lịch sử ra {os.path.basename(export_path)}!", text_color="#38bdf8")
        self.after(3000, lambda: self.lbl_status.configure(
            text="Trạng thái: 🟢 Đang nghe" if self.is_listening else "Trạng thái: 🔴 Đang dừng",
            text_color="#4ade80" if self.is_listening else "#9ca3af"
        ))

    def on_closing(self):
        self._stop_listening()
        self.destroy()
        sys.exit(0)
