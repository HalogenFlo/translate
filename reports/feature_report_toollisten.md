# Báo Cáo Chức Năng: ToolListen (Live Audio Subtitle & Translator)

## 1. Giới thiệu chức năng
Công cụ **ToolListen** được phát triển nhằm giải quyết trọn vẹn nhu cầu:
- Lắng nghe âm thanh hệ thống Windows (từ Video YouTube, cuộc gọi Discord, Google Meet, Zoom, phim...).
- Nhận diện giọng nói tức thì (Speech-to-Text) cho ngôn ngữ nguồn (Tiếng Anh, Nhật, Trung, Hàn, v.v.).
- Lập tức hiển thị phụ đề song ngữ: **1 bản tiếng gốc** và **1 bản dịch Tiếng Việt**.
- Trang bị cụm nút **Copy nhanh 1-Click** cho từng bản dịch hoặc cả hai kèm phản hồi thị giác.
- Cửa sổ nổi Always-on-Top ghim trên cùng màn hình giúp người dùng vừa xem video/họp vừa theo dõi phụ đề.

---

## 2. Sơ Đồ Hệ Thống Tổng Quan (System Map)

```mermaid
graph TD
    subgraph AudioEngine["1. Lớp Thu Âm (Audio Capture)"]
        WASAPI["🔊 Windows WASAPI Loopback<br/>(Bắt âm thanh Loa/Discord/Meet)"]
        MIC["🎙️ Microphone Input<br/>(Bật/Tắt nhanh 1-Click)"]
        VAD["⚡ Voice Activity & Silence Slicer<br/>(Ngắt câu theo nhịp nói tự nhiên)"]
    end

    subgraph Processing["2. Lớp Xử Lý AI & Dịch Thuật"]
        STT["🗣️ SpeechTranscriber<br/>(Google Speech Engine)"]
        TRANS["🌐 TranslatorService<br/>(MyMemory API + Fallback + Cache)"]
    end

    subgraph UI["3. Lớp Giao Diện Desktop Overlay"]
        TOP["📌 Ghim Trên Cùng (Always On Top)"]
        LIVE["🔴 Live Streaming Banner<br/>(Nói tới đâu xuất chữ tới đó)"]
        FAST_CPY["⚡ Cụm Nút Copy Siêu Tốc [F2/F3] & Auto-Copy"]
        MIC_BTN["🎙️ Nút Bật/Tắt Micro (Mute / Unmute tức thì)"]
        CTRL["⚙️ Bảng Điều Khiển (Chọn Loa/Mic, Ngôn ngữ, Bắt đầu/Dừng)"]
        CARD["💬 Danh Sách Card Phụ Đề Song Ngữ"]
        CPY["📋 1-Click Copy (Gốc / Tiếng Việt / Cả 2)"]
        EXP["💾 Xuất File TXT & Xóa Lịch Sử"]
    end

    WASAPI --> VAD
    MIC -->|Khi Micro: BẬT| VAD
    VAD -->|Interim PCM (0.35s)| STT
    VAD -->|Final PCM| STT
    STT -->|Live Interim Text| LIVE
    STT -->|Final Original Text| TRANS
    TRANS -->|Song Ngữ| CARD
    TRANS -->|Auto-Copy| FAST_CPY
    CARD --> CPY
    CTRL -->|Điều khiển luồng| AudioEngine
    MIC_BTN -->|Bật / Tắt Microphone| MIC
```

---

## 3. Kết quả Kiểm thử (Test Verification)
- Toàn bộ **10 bài kiểm thử đơn vị** đều vượt qua (100% Passed):
  - `tests/test_recorder.py`: Kiểm tra phát hiện thiết bị WASAPI Loopback, tính toán RMS năng lượng và trạng thái luồng thu âm.
  - `tests/test_transcriber.py`: Kiểm tra chuyển đổi âm thanh, danh sách ngôn ngữ hỗ trợ và xử lý khoảng lặng.
  - `tests/test_translator.py`: Kiểm tra dịch song ngữ Anh -> Việt, xử lý cache và chuỗi rỗng.
  - `tests/test_ui.py`: Kiểm tra khởi tạo component thẻ phụ đề SubtitleCard và gán dữ liệu.

---

## 4. Danh mục tệp dự án
- [main.py](file:///c:/Users/Admin/Desktop/toollisten/main.py): Điểm khởi chạy ứng dụng.
- [run.bat](file:///c:/Users/Admin/Desktop/toollisten/run.bat): Tệp chạy nhanh 1-click cho người dùng.
- [src/audio/recorder.py](file:///c:/Users/Admin/Desktop/toollisten/src/audio/recorder.py): Quản lý thu âm WASAPI loopback & Mic.
- [src/stt/transcriber.py](file:///c:/Users/Admin/Desktop/toollisten/src/stt/transcriber.py): Nhận diện giọng nói đa ngôn ngữ.
- [src/translator/service.py](file:///c:/Users/Admin/Desktop/toollisten/src/translator/service.py): Dịch tự động sang Tiếng Việt.
- [src/ui/app.py](file:///c:/Users/Admin/Desktop/toollisten/src/ui/app.py): Giao diện Modern Dark Mode Overlay.
- [ARCHITECTURE.md](file:///c:/Users/Admin/Desktop/toollisten/ARCHITECTURE.md): Kiến trúc kỹ thuật.
- [README.md](file:///c:/Users/Admin/Desktop/toollisten/README.md): Hướng dẫn sử dụng chi tiết.
