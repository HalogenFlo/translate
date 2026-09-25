# Kiến Trúc Hệ Thống ToolListen (Realtime Audio Subtitle & Translator)

## 1. Sơ đồ Luồng Hoạt động (Data Flow & Architecture)

```mermaid
flowchart TD
    subgraph AudioSource["Nguồn Âm Thanh (Audio Capture)"]
        A1["🔊 System Audio (Loa/Tai nghe: Discord, Meet, Youtube...)"]
        A2["🎙️ Microphone (Giọng nói trực tiếp)"]
    end

    subgraph LoopbackEngine["WASAPI Loopback Recorder"]
        B1["Soundcard WASAPI Loopback / InputStream"]
        B2["VAD (Voice Activity Detection) & Silence Slicer"]
        B3["Chunk Buffer (16kHz, Mono, 16-bit PCM)"]
    end

    subgraph STTEngine["Speech-to-Text Engine"]
        C1["Google Web Speech API (Nhanh, Nhẹ, Đa ngôn ngữ)"]
        C2["Faster-Whisper Engine (Local AI / GPU RTX 3060)"]
    end

    subgraph TranslationService["Dịch Thuật Sang Tiếng Việt"]
        D1["MyMemory API / Edge Translate"]
        D2["Translation Cache (Tránh dịch lặp)"]
    end

    subgraph TTSEngine["Realtime Text-To-Speech (Phát Âm Tiếng Việt)"]
        F1["Microsoft Edge Neural TTS (Hoài My / Nam Minh)"]
        F2["Windows MCI Media Player (winmm.dll)"]
        F3["Echo Suppression (Tạm dừng thu khi TTS đang phát)"]
    end

    subgraph UIOverlay["Giao Diện Desktop Overlay (CustomTkinter)"]
        E1["Cửa sổ nổi Always-On-Top (Ghim trên cùng mọi ứng dụng)"]
        E2["Thẻ Phụ Đề Song Ngữ: Bản gốc + Bản dịch Tiếng Việt"]
        E3["Nút 1-Click Copy: 📋 Copy Gốc [F2] | 📋 Copy Dịch [F3] | 📑 Copy Tất Cả [F4]"]
        E4["Bảng Điều Khiển: Loa/Mic, Ngôn ngữ, Đọc Tiếng Việt [F5], Tốc độ"]
        E5["Lịch sử hội thoại & Live Interim Subtitle"]
    end

    A1 -->|WASAPI Loopback| B1
    A2 -->|Direct Mic| B1
    B1 --> B2 --> B3
    B3 -->|Audio Chunk| STTEngine
    C1 -->|Original Text| TranslationService
    C2 -->|Original Text| TranslationService
    TranslationService -->|Original + Vietnamese Text| UIOverlay
    TranslationService -->|Vietnamese Text| F1
    F1 --> F2
    F2 -->|Phát tiếng Việt ra Loa/Tai nghe| A1
    F2 -.->|Echo Suppression Signal| F3 -.->|Mute loopback trong lúc đọc| B2
```

## 2. Chi tiết các thành phần chính
1. **Audio Capture Layer (`src/audio/recorder.py`)**:
   - Sử dụng Windows WASAPI Loopback để "nghe lén" chính xác mọi âm thanh đang phát ra tai nghe / loa của hệ thống (bất kể phát từ tab trình duyệt Youtube, ứng dụng Discord, Zoom hay Google Meet).
   - Tích hợp bộ lọc năng lượng âm thanh (RMS Energy threshold) và kiểm tra khoảng lặng (silence detection) để cắt câu thoại tự nhiên, không cắt vụn chữ.
   - Hỗ trợ cờ chống tiếng vọng `set_suppressed(True)` khi hệ thống đang phát âm thanh dịch tiếng Việt ra loa.

2. **STT Transcriber Layer (`src/stt/transcriber.py`)**:
   - Hỗ trợ chọn ngôn ngữ nguồn: `en-US` (Tiếng Anh), `auto` (Tự động phát hiện), `ja-JP` (Tiếng Nhật), `zh-CN` (Tiếng Trung), `ko-KR` (Tiếng Hàn), `fr-FR` (Tiếng Pháp)...
   - Bộ giải mã giọng nói chuyển luồng PCM audio thành chuỗi văn bản.

3. **Translator Layer (`src/translator/service.py`)**:
   - Nhận chuỗi văn bản từ STT, dịch sang Tiếng Việt.
   - Cơ chế fallback thông minh: Thử dịch MyMemory -> Bing / Edge -> Cache.

4. **TTS Speaker Layer (`src/tts/speaker.py`)**:
   - Nhận chuỗi văn bản Tiếng Việt sau khi dịch, tổng hợp giọng nói Neural siêu tự nhiên qua Microsoft Edge TTS.
   - Tùy chọn giọng đọc: Giọng Nữ (`vi-VN-HoaiMyNeural`), Giọng Nam (`vi-VN-NamMinhNeural`).
   - Tùy chọn tốc độ đọc (`1.0x` đến `1.35x`) để đọc nhanh kịp ngữ cảnh đàm thoại realtime.
   - Phát âm thanh qua Windows MCI (`winmm.dll`) mượt mà, không block giao diện.

5. **UI Layer (`src/ui/app.py`)**:
   - Cửa sổ nổi Always-on-Top với nền bán trong suốt / dark mode hiện đại.
   - Thao tác 1 click để Copy nhanh vào clipboard (`F2` copy câu gốc, `F3` copy câu dịch, `F4` copy toàn bộ lịch sử).
   - Phím tắt `F5` bật/tắt nhanh chế độ Dịch Nói Realtime.

