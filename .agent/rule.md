# Dự án ToolListen - Live Subtitle & Translator cho Windows

## 1. Mục tiêu và phạm vi
- **Mục tiêu**: Xây dựng công cụ Desktop lắng nghe âm thanh trực tiếp từ hệ thống (System Audio / Loa: Discord, Google Meet, YouTube, Video...) hoặc Microphone.
- **Tính năng cốt lõi**:
  - Nhận diện giọng nói (STT - Speech to Text) theo thời gian thực (hỗ trợ Tiếng Anh hoặc bất kỳ ngôn ngữ nào người dùng chọn, hoặc tự động phát hiện).
  - Tự động dịch sang Tiếng Việt ngay lập tức.
  - Hiển thị phụ đề song ngữ trực quan (Gốc & Tiếng Việt).
  - Nút Copy nhanh 1-click (Copy câu gốc, Copy tiếng Việt, hoặc Copy cả 2).
  - Cửa sổ nổi Overlay ghim trên cùng (Always on Top) tiện xem khi họp/học/xem video.

## 2. Tech Stack & Thư viện
- **Ngôn ngữ**: Python 3.12
- **Audio Capture**: `soundcard` (WASAPI Loopback capture chuyên dụng trên Windows) & `sounddevice`
- **Speech Recognition (STT)**:
  - Google Speech API (nhẹ, nhanh, miễn phí)
  - Faster-Whisper (hỗ trợ local AI model nếu muốn)
- **Translation**: Dịch sang Tiếng Việt (MyMemory API, Fallback Google Translate / Bing)
- **UI Framework**: `customtkinter` (Giao diện hiện đại Dark Mode phong cách Windows 11 Fluent Design, hỗ trợ Always-on-Top, kéo thả cửa sổ nổi)
- **Clipboard**: `pyperclip`

## 3. Kiến trúc module
- `src/audio/recorder.py`: Quản lý luồng bắt âm thanh từ Loa (System Loopback) hoặc Microphone với cơ chế VAD (Voice Activity Detection) / Silence Detection thông minh.
- `src/stt/transcriber.py`: Module nhận diện giọng nói từ âm thanh, chuyển thành văn bản ngôn ngữ nguồn.
- `src/translator/service.py`: Module dịch câu thoại sang Tiếng Việt nhanh chóng với cơ chế cache và fallback.
- `src/ui/app.py`: Giao diện CustomTkinter với danh sách phụ đề song ngữ, nút Copy nhanh, chọn nguồn âm thanh, chọn ngôn ngữ và tuỳ chỉnh Always-On-Top.
- `main.py`: Điểm khởi chạy ứng dụng.

## 4. Definition of Done & Verify
- Kiểm thử đơn vị cho Audio Recorder, Transcriber, Translator.
- Chạy thử nghiệm các tính năng bắt âm thanh, dịch thuật và giao diện.
