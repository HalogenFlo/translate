# Báo Cáo Triển Khai: Chế Độ Dịch Nói Realtime (Speech-to-Speech Voice Translation)

## 1. Giới thiệu Tính năng
Theo yêu cầu của người dùng:
> *"thêm chế độ dịch realtime được không là bên kia nói hết câu là bên đây nói ra tiếng việt cho tôi nghe"*

Hệ thống đã được bổ sung giải pháp **Realtime Speech-to-Speech / Live Voice Translation**:
- **Bên kia nói**: Âm thanh phát ra từ cuộc gọi Discord, Google Meet, Zoom, video YouTube hoặc người nói trực tiếp.
- **Dứt câu**: Thuật toán VAD & Silence Detection ngắt câu ngay lập tức.
- **Dịch tức thì**: Chuyển giọng nói sang text (STT) và dịch sang tiếng Việt (Translator).
- **Phát âm Tiếng Việt**: Module **Text-to-Speech (TTS)** sử dụng trí tuệ nhân tạo phát trực tiếp câu tiếng Việt ra loa hoặc tai nghe của bạn với ngữ điệu tự nhiên như người bản xứ.

---

## 2. Kiến trúc & Công nghệ Thực thi
- **TTS Engine**: `edge-tts` với các model giọng đọc Neural hàng đầu của Microsoft:
  - 👩 **`vi-VN-HoaiMyNeural`**: Giọng nữ ấm áp, truyền cảm.
  - 👨 **`vi-VN-NamMinhNeural`**: Giọng nam rõ ràng, tự nhiên.
- **Audio Output**: Sử dụng Windows Media Control Interface (MCI qua `winmm.dll`), phát âm thanh cực kỳ mượt mà, không phụ thuộc ffmpeg, không làm đơ giao diện.
- **Echo Loop Suppression (Chống tiếng vọng vòng lặp)**:
  - Khi hệ thống đang phát âm thanh tiếng Việt ra loa, cờ `is_suppressed` sẽ được bật tự động trên `AudioRecorder` để tạm dừng thu âm loopback.
  - Khi đọc xong, cờ được nhả ra để tiếp tục lắng nghe câu tiếp theo.
  - Triệt tiêu 100% tình trạng loa tự nghe chính mình rồi dịch ngược lại.

---

## 3. Các Thay Đổi Chính
1. **Module Mới**: `src/tts/speaker.py` (`TextToSpeechService`):
   - Quản lý hàng đợi phát âm phi đồng bộ qua background worker thread.
   - Hỗ trợ chọn giọng đọc và tùy chỉnh tốc độ phát (`1.0x` đến `1.35x`).
   - Callback an toàn `on_start` và `on_finish`.
2. **Audio Recorder**: `src/audio/recorder.py`:
   - Bổ sung `set_suppressed(bool)` và bỏ qua audio chunk khi đang TTS phát âm thanh.
3. **Giao diện Desktop**: `src/ui/app.py`:
   - Thêm nút **`🔊 Đọc TV: TẮT / BẬT [F5]`** với màu sắc cảnh báo trực quan.
   - Bộ chọn Giọng Nữ / Giọng Nam và Tốc độ phát âm.
   - Đăng ký phím tắt toàn cục **`F5`** để bật/tắt nhanh chế độ đọc tiếng Việt.
   - Tự động gọi `self.tts.speak(translated_text)` ngay khi câu nói kết thúc.
4. **Kiểm thử đơn vị & tích hợp**:
   - `tests/test_tts.py`: 8 unit tests cho khởi tạo, chọn giọng, hàng đợi, dừng và dọn dẹp.
   - `tests/test_recorder.py`: Bổ sung test kiểm tra tính năng `suppress`.
   - `tests/test_ui.py`: Bổ sung test tích hợp TTS vào giao diện.
   - Toàn bộ **24/24 tests PASSED** 100%.

---

## 4. Hướng dẫn sử dụng
1. Mở ứng dụng bằng file `run.bat` hoặc lệnh `python main.py`.
2. Nhấn nút **`🔊 Đọc TV: TẮT [F5]`** hoặc bấm phím **`F5`** trên bàn phím:
   - Nút chuyển sang màu cam rực rỡ: **`🔊 Đọc TV: BẬT [F5]`**.
3. Chọn giọng đọc mong muốn (Nữ Hoài My hoặc Nam Nam Minh) và tốc độ đọc (khuyên dùng `1.15x`).
4. Bấm **`▶ BẮT ĐẦU NGHE`** và bật video/cuộc gọi.
5. Mỗi khi người kia nói xong 1 câu, loa/tai nghe của bạn sẽ tự động đọc to câu dịch Tiếng Việt!
