# 📋 Changelog - Rody S3 Meta Muse Edition

Toàn bộ lịch sử các thay đổi, tối ưu hóa kiến trúc, tính năng mới và các bản vá cho dự án **Rody S3 Meta Muse Edition** (`firmware_muse/`).

---

## [v1.5.0-muse] - 2026-10-04

### 🌟 Nâng Cấp Màn Hình Tròn 1.28" 240x240 GC9A01 SPI (Round Display Upgrade)
- **Màn Hình Tròn IPS Siêu Nét (Full RGB565):**
  - Chuyển đổi từ màn OLED đơn sắc SSD1306 128x64 I2C sang màn hình tròn **1.28 inch 240x240 GC9A01 SPI IPS LCD** hiển thị màu 16-bit RGB565 rực rỡ, góc nhìn rộng 178°.
  - Tích hợp driver chuẩn Espressif `esp_lcd_panel_gc9a01.h` và `esp_lcd_panel_gc9a01.c` thuần C, tốc độ xung nhịp SPI 40 MHz qua kênh DMA tự động (`SPI2_HOST`).
- **Giao Diện Tròn Bản Quyền Meta Muse (`round = true`):**
  - Kích hoạt giao diện tròn cao cấp với **vòng tròn tiến trình chuyển động quanh viền bezel (Circular Bezel Progress Ring)** khi lắng nghe và suy nghĩ.
  - Tự động co giãn avatar Muse Pixel Art lên tỉ lệ 128x128 pixel ($2\times$ pixel art), mắt chớp và biểu cảm sắc nét ở trung tâm hình tròn.
  - Phụ đề thông minh uốn theo cung tròn hình học (`chord clipping`), loại bỏ hoàn toàn nguy cơ lỗi tính toán số thực NaN.
- **Điều Khiển Độ Sáng Đèn Nền PWM (Backlight Dimming):**
  - Tích hợp điều khiển độ sáng màn hình qua LEDC phần cứng trên chân `LCD_BL` (GPIO 21), hỗ trợ chỉnh độ sáng mượt mà từ 0% đến 100% trong menu hoặc tự tắt khi ngủ (`panel_sleep`).
- **Tối Ưu Chân Nối Phần Cứng (Clean Pinout):**
  - Tách bus I2C cho cảm biến gia tốc MPU6050 sang `GPIO 8 (SDA)` và `GPIO 9 (SCL)`.
  - Toàn bộ chân SPI màn hình khớp hoàn hảo: SCLK=42, MOSI=41, DC=40, RST=39, CS=38, BL=21.
  - Giữ nguyên 100% các chân âm thanh Micro INMP441 (4, 5, 6), Loa MAX98357A (7, 15, 16), Cảm biến chạm đỉnh đầu (GPIO 2), nút BOOT (GPIO 0) và LED RGB onboard (GPIO 48).
- **Kiểm Thử Toàn Diện:**
  - Cập nhật test harness `tests/test_board_bread_s3.py` kiểm tra đóng gói màu RGB565, hình học dây cung màn hình tròn, và các cấu hình tích hợp. Toàn bộ 168 unit tests tiếp tục đạt 100% thành công.

---

## [v1.4.0-muse] - 2026-10-04

### ⚡ Tối Ưu Điện Năng & Độ Bền Phần Cứng (Power & Hardening)
- **MAX98357A I2S Clock Gating:** Tích hợp ngắt/bật xung I2S TX tự động trong `spk_enable()`. Khi hết âm thanh hoặc sang chế độ nghỉ, xung BCLK/LRCLK tự động ngắt, kích hoạt chế độ **Hardware Auto-Shutdown (<10µA)** của chip MAX98357A, triệt tiêu hoàn toàn tiếng sôi rè (quiescent hiss).
- **Auto Wake-Up Trong `spk_write()`:** Đảm bảo tự động kích hoạt lại `s_tx` nếu kênh I2S đang tắt trước khi ghi, triệt tiêu mọi khả năng mất tiếng ngẫu nhiên.
- **Kẹp Biên An Toàn Màn Hình OLED (`shim_draw`):** Thêm kiểm tra tham số `!data` và kẹp biên chặt chẽ `[0, OLED_W]`, `[0, OLED_H]` chống tràn bộ nhớ 1024-byte `s_shim.fb` khi LVGL render các widget sát mép màn hình.
- **Khử Nhiễu Cảm Biến Chạm Đầu (GPIO 2):** Bộ lọc debounce đa chu kỳ (`s_touch_debounce >= 2`) triệt tiêu hoàn toàn hiện tượng kích hoạt giả (phantom trigger) do sóng RF Wi-Fi/Bluetooth.
- **Cooldown IMU Chống Spam Log:** Thêm khoảng đệm 500ms giữa các lần kích hoạt cảm biến rung lắc (> 2.2g) và rơi tự do (< 0.4g) của MPU6050, bảo vệ hàng đợi sự kiện và CPU khỏi bị quá tải khi robot vận động mạnh.
- **Bounded Timeout Cho DMA Audio:** Thay thế `portMAX_DELAY` bằng `pdMS_TO_TICKS(1000)` trong các thao tác I2S, ngăn chặn nguy cơ deadlock làm kích hoạt Watchdog Timer.

### 🔍 Chẩn Đoán Hệ Thống & Trải Nghiệm Người Dùng (Diagnostics & UX)
- **Lệnh Console `>diag`:** Xuất báo cáo trạng thái hệ thống chuẩn JSON qua Serial:
  - Bộ nhớ RAM nội bộ (Free & Min Watermark).
  - Bộ nhớ Octal PSRAM (Free & Min Watermark).
  - Trạng thái kết nối Wi-Fi, SSID, cường độ sóng RSSI, địa chỉ IP nội mạng.
  - Mức âm lượng, độ nhạy micro (Mic Gain dB).
  - Trạng thái công tắc TTS Song Ngữ và Đánh thức bằng giọng nói (Wakeup).
- **Hệ Thống Log Có Cấu Trúc & Gợi Ý Hành Động (`[TTS HINT]`):** Bổ sung chỉ dẫn hành động rõ ràng khi mất mạng Wi-Fi, khi loa bị tắt, hoặc khi gặp lỗi mạng.
- **Cơ Chế Barge-In Tức Thì:** Người dùng có thể nhấn BOOT hoặc chạm vào đầu pet để ngắt ngang lời nói của robot bất kỳ lúc nào, robot dừng phát và lắng nghe ngay tức khắc.

### 🧪 Kiểm Thử Tự Động
- Bổ sung các bài test chuyên sâu cho `>diag`, cơ chế Barge-in, Mock Wi-Fi offline, Mock Loa mute trong `tests/test_muse_tts.py`.
- Toàn bộ **168 test cases** trong bộ test suite host (`./test_host.sh`) vượt qua 100% (0 lỗi).

---

## [v1.3.0-muse] - 2026-10-04

### 🎙️ Phát Âm Thanh Song Ngữ Miễn Phí (Free Bilingual TTS)
- **Zero API Key & Zero Chi Phí:** Tích hợp engine TTS trực tiếp qua Google Translate CDN (`translate.google.com/translate_tts?client=tw-ob`), không tốn phí token LLM, không cần proxy ngoài.
- **Tự Động Nhận Diện Tiếng Việt / Tiếng Anh:** Phân tích trực tiếp các chuỗi byte UTF-8 đặc trưng của dấu thanh tiếng Việt (`0xC3`, `0xC4`, `0xC5`, `0xE1`), tự động chọn `tl=vi` hoặc `tl=en` mượt mà.
- **Ngắt Câu Thông Minh (Sentence Chunking):** Tự động chia các câu văn dài thành các đoạn $\le 160$ ký tự tại dấu câu hoặc khoảng trắng để tương thích với CDN và URL encoding.
- **Mã Hóa URL Tiếng Việt An Toàn:** Mở rộng bộ đệm mã hóa URL (`encoded[512]`, `url[768]`) hỗ trợ tiếng Việt có dấu phức tạp mà không bị tràn bộ nhớ.
- **Giải Mã Phần Cứng `minimp3`:** Tận dụng thư viện `minimp3` có sẵn trong Muse SDK, giải mã MP3 trực tiếp từ buffer PSRAM và cấp tín hiệu PCM16 cho loa MAX98357A.
- **Lệnh Serial Kiểm Thử Trực Tiếp:** Thêm lệnh `>say=<nội dung>` để phát âm câu nói tiếng Việt hoặc tiếng Anh bất kỳ qua Serial Monitor.
- **Công Tắc Trong Cài Đặt (NVS):** Thêm switch `TTS voice: ON/OFF` trong menu màn hình OLED và key lưu trữ flash `"tts_on"`.

---

## [v1.2.0-muse] - 2026-10-04

### ⚡ Đánh Thức Bằng Giọng Nói & Tối Ưu Token Kiểu Xiaozhi AI
- **Hands-Free Voice Wake-Up:** Kích hoạt robot bằng giọng nói rảnh tay thông qua bộ lọc năng lượng âm thanh và tỷ lệ vượt mức không (Zero-Crossing Rate 6–110), không cần bấm nút vật lý.
- **Adaptive Voice Activity Detection (VAD):** Tự động theo dõi mức ồn môi trường thích ứng (Dynamic Noise Floor Tracking), cập nhật ngưỡng phân biệt giọng nói thời gian thực.
- **Silence Cutoff Tiết Kiệm Token:** Tự động phát hiện và ngắt thu âm sau **700ms im lặng**, cắt giảm tới 85% thời lượng khoảng lặng vô nghĩa sau câu nói, tiết kiệm tới 79% token audio gửi lên cloud.
- **Tự Hủy Lượt Nói Ảo (Ghost Turn Cutoff):** Nếu sau 3.5s không có tiếng người nói, turn tự động hủy để tiết kiệm 100% token LLM.
- **Công Tắc Bật/Tắt Trong Menu:** Thêm switch `Voice wake: ON/OFF` trong mục Cài đặt màn hình (mặc định BẬT, lưu vĩnh viễn vào NVS `"wakeup_on"`).

---

## [v1.1.0-muse] - 2026-10-04

### 🖥️ Giai Đoạn UI - Board `muse-bread-s3`
- **Driver Panel Shim SSD1306 128x64:** Chuyển đổi luồng đồ họa RGB565 từ `esp_lv_adapter` sang định dạng 1-bit monochrome page-aligned cho màn hình OLED SSD1306 qua bus I2C (GPIO 41 SDA, GPIO 42 SCL).
- **Tối Ưu Avatar Muse Pixel Art:** Cố định avatar 48x48 pixel vừa vặn chiều cao màn hình 64px, ẩn các nhãn thừa, hiển thị thanh trạng thái và phụ đề siêu gọn.
- **Audio Simplex Hai Bus I2S:** Tích hợp Micro INMP441 trên I2S0 RX và Loa MAX98357A trên I2S1 TX theo kiến trúc `audio_codec_data_if_t` không cần chip codec ngoài.
- **Hệ Thống Phản Xạ Thú Cưng Pet:**
  - Vuốt ve đỉnh đầu (Touch GPIO 2) kích hoạt cảm xúc mắt híp mỉm cười (`muse_state_make_happy`).
  - Hỗ trợ cảm biến gia tốc MPU6050 trên I2C, nhận diện chuyển động lắc và rơi tự do.

---

## [v1.0.0-muse] - 2026-10-04

### 🚀 Giai Đoạn Link Khởi Đầu
- **Khởi Tạo Cây Thư Mục `firmware_muse/`:** Tách biệt hoàn toàn khỏi phiên bản robot cũ, dựa trên Meta Muse Gadget SDK.
- **Cấu Hình `devices/sdkconfig.bread-s3`:** Hỗ trợ ESP32-S3-DevKitC N16R8 (16MB Flash, 8MB Octal PSRAM).
- **LED RGB Trạng Thái Onboard:** Chuyển đổi chân điều khiển LED sang GPIO 48 (WS2812 onboard của S3-DevKitC).
- **Cơ Chế Nút Nhấn Tránh Xung Đột:** Tách chân nút Link khỏi chân OLED SDA (GPIO 41), ghép đôi BLE trực tiếp bằng nút BOOT (GPIO 0).
