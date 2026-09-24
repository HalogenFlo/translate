# 🎧 ToolListen - Live Subtitle & Translator cho Windows

Ứng dụng lắng nghe âm thanh trực tiếp từ máy tính (Video YouTube, Discord, Google Meet, Zoom...) hoặc Microphone, nhận diện giọng nói theo thời gian thực (Tiếng Anh hoặc bất kỳ ngôn ngữ nào), lập tức dịch sang Tiếng Việt và hỗ trợ nút Copy nhanh 1-click.

---

## ✨ Tính Năng Nổi Bật

1. **Tối ưu độ trễ siêu tốc - "Nói tới đâu xuất chữ tới đó" (Live Streaming Subtitle)**:
   - Tích hợp luồng phát hiện âm thanh ngắt đoạn siêu nhanh (`silence_timeout = 0.35s`).
   - Khung **`🔴 Đang nói trực tiếp (Live Stream)`**: Chữ và bản dịch hiển thị tức thời ngay khi người nói phát âm từng từ, không cần đợi nói xong hết câu.

2. **Cụm Nút Copy Siêu Tốc 1-Click & Phím Tắt [F2] / [F3] / [F4]**:
   - ⚡ **`[COPY GỐC VỪA NÓI - F2]`**: Bấm 1 click hoặc gõ phím **`F2`** để copy ngay câu thoại gốc mới nhất.
   - ⚡ **`[COPY DỊCH TIẾNG VIỆT - F3]`**: Bấm 1 click hoặc gõ phím **`F3`** để copy ngay câu dịch tiếng Việt mới nhất.
   - 📑 **`[COPY TẤT CẢ LỊCH SỬ - F4]`**: Bấm 1 click hoặc gõ phím **`F4`** để sao chép **toàn bộ cuộc hội thoại/video từ đầu đến giờ** (kèm mốc thời gian và cả bản gốc + dịch) để dán vào Word, Docs, Note hoặc ChatGPT!
   - 🇻🇳 **`[CHỈ COPY TOÀN BỘ TIẾNG VIỆT]`**: Sao chép toàn bộ nội dung dịch thuần tiếng Việt để dễ dàng đọc và tổng kết.
   - ⚡ **Tự động Copy (Auto-Copy)**: Bật tùy chọn `[x] Tự động đưa câu dịch vào Clipboard`, người khác nói xong là câu dịch đã có sẵn trong bộ nhớ tạm, bạn chỉ việc ấn `Ctrl + V` để gửi ngay mà không cần chạm chuột vào nút copy!

3. **Thu âm trực tiếp từ Loa Hệ Thống (WASAPI Loopback)**:
   - Tự động bắt âm thanh đang phát ra từ bất kỳ nguồn nào: YouTube, Discord Call, Google Meet, Zoom, phim, game... mà không cần cài đặt thêm Virtual Audio Cable.
   - Hỗ trợ chuyển đổi linh hoạt sang Microphone nếu muốn nói vào mic.

4. **Nút Bật / Tắt Microphone 1-Click (Mute / Unmute)**:
   - 🔒 **`🎙️ Micro: TẮT` (Mặc định)**: Hoàn toàn ngắt tiếng từ Micro, chỉ tập trung nghe âm thanh phát ra từ máy tính (Discord, Meet, Video). Giúp phụ đề không bao giờ bị lẫn tạp âm trong phòng, tiếng thở hay tiếng gõ phím của bạn.
   - 🟢 **`🎙️ Micro: BẬT`**: Bật nhận giọng nói từ micro của bạn bất cứ lúc nào khi bạn muốn nói để dịch.
   - Hỗ trợ Tiếng Anh (Mỹ, Anh), Tiếng Nhật, Tiếng Trung, Tiếng Hàn, Tiếng Pháp, Tiếng Đức, Tiếng Tây Ban Nha, Tiếng Nga, Tiếng Việt...
   - Tự động nhận diện khoảng ngắt câu thông minh (Voice Activity & Silence Detection) để phụ đề hiển thị trọn vẹn từng câu thoại.

3. **Dịch tức thì sang Tiếng Việt**:
   - Tự động dịch bản tiếng gốc sang Tiếng Việt ngay sau khi kết thúc câu nói.
   - Cơ chế dịch thông minh kèm bộ nhớ cache để giảm độ trễ tối đa.

4. **Nút Bấm Copy Nhanh 1-Click**:
   - 📋 **Copy Gốc**: Sao chép nguyên văn câu tiếng Anh/nguồn.
   - 📋 **Copy Tiếng Việt**: Sao chép bản dịch tiếng Việt.
   - 📋 **Copy Cả 2**: Sao chép cả 2 dòng để lưu trữ hoặc gửi tin nhắn.
   - Hiệu ứng đổi màu nút "✓ Đã Copy!" trực quan.

5. **Giao diện Modern Overlay (Fluent Dark Mode)**:
   - **Ghim trên cùng (Always on Top)**: Cửa sổ luôn nổi trên các ứng dụng khác, cực kỳ tiện lợi để vừa theo dõi cuộc họp Meet/Discord/YouTube vừa đọc phụ đề.
   - Nút **Xuất File TXT** để lưu toàn bộ nội dung cuộc họp hoặc video vào máy.
   - Nút **Xóa Lịch Sử** để dọn dẹp phiên làm việc mới.

---

## 🚀 Hướng Dẫn Sử Dụng

### Cách 1: Click đúp file `run.bat`
Chỉ cần nhấp đúp chuột vào file [run.bat](file:///c:/Users/Admin/Desktop/toollisten/run.bat) trên thư mục máy tính.

### Cách 2: Khởi chạy bằng dòng lệnh
```powershell
python main.py
```

---

## 🛠️ Hướng Dẫn Thao Tác Trong Ứng Dụng

1. **Nguồn âm thanh**:
   - Chọn `🔊 [Hệ thống/Loa] Speakers...` để nghe tiếng từ YouTube, Discord, Meet, Zoom.
   - Hoặc chọn `🎙️ [Microphone]...` nếu muốn nghe từ mic của bạn.
2. **Ngôn ngữ nói**:
   - Chọn ngôn ngữ của người đang nói trong video hoặc cuộc gọi (mặc định: `Tiếng Anh (US)`).
3. **Bắt đầu**:
   - Nhấn **▶ BẮT ĐẦU NGHE (LISTEN)**.
   - Mở video hoặc cuộc gọi Discord/Meet để bắt đầu nhận phụ đề song ngữ và copy.
4. **Copy nhanh**:
   - Nhấp vào nút `📋 Copy Gốc` hoặc `📋 Copy Tiếng Việt` trên mỗi câu phụ đề để dán vào bất cứ đâu (Ctrl + V).
