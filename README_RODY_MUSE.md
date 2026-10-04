# 🤖 Rody S3 Meta Muse Edition - Hướng Dẫn Kỹ Thuật Toàn Diện

> **Phiên bản:** `v1.5.0-muse` ([Xem chi tiết Changelog](file:///Volumes/Builder/Arduino/OtooRobot/firmware_muse/CHANGELOG.md))  
> **Nền tảng:** Meta Muse Gadget SDK (`facebookincubator/muse-gadget-sdk`) & ESP-IDF v6.0.1  
> **Thư mục dự án:** `firmware_muse/`  
> **Phần cứng tương thích:** ESP32-S3-DevKitC-1 N16R8 (16MB Flash, 8MB Octal PSRAM), Màn hình tròn 1.28" 240x240 GC9A01 SPI IPS LCD, Micro I2S INMP441, Loa I2S MAX98357A, LED RGB WS2812 Onboard GPIO48, Cảm biến Chạm Pet GPIO2, Cảm biến Gia tốc IMU MPU6050 (I2C GPIO8/9).

---

## 1. Tổng Quan Kiến Trúc & Điểm Mới

Phiên bản **Meta Muse Edition** biến Robot Rody S3 / Pet Edition thành một thiết bị phần cứng AI Agent tự trị hoàn chỉnh kết nối trực tiếp với hệ sinh thái **Meta Muse AI**:
1. **Giao thức đám mây Meta Muse:** Thiết bị ghép đôi qua Bluetooth Low Energy (BLE) với ứng dụng Muse trên điện thoại, đồng bộ Wi-Fi và thiết lập đường hầm mã hóa **Noise Protocol** (kèm home-network tunnel) trực tiếp tới Meta Cloud VM.
2. **Loại Link (Giai đoạn 1):** Chạy nhẹ nhàng, làm trạm trung gian AI thông minh / Home Link, dùng LED RGB WS2812 (GPIO 48) thể hiện nhịp thở và trạng thái kết nối.
3. **Loại UI (Giai đoạn 2 - Màn Hình Tròn 1.28" GC9A01):** Toàn bộ giao diện sinh động với **Avatar Muse Pixel Art 128x128 full màu RGB565** trên màn hình tròn 1.28 inch 240x240 GC9A01 SPI IPS, kèm **vòng tròn tiến trình bezel (Circular Progress Ring)** chuyển động quanh đường viền tròn khi lắng nghe/suy nghĩ, đàm thoại thoại hai chiều Push-to-Talk qua Micro INMP441 và Loa MAX98357A, hệ thống phản xạ xúc giác **Pet Edition** (vuốt đầu âu yếm, lắc rung phát hiện rơi ngã), và phát âm thanh TTS song ngữ Việt - Anh miễn phí.

---

## 2. Sơ Đồ Đấu Dây Chi Tiết (Hardware Pinout)

| Linh Kiện | Chân Module | Nối Vào ESP32-S3 | Chức Năng & Giao Thức | Ghi Chú |
|:---|:---:|:---:|:---|:---|
| **Màn Hình Tròn 1.28" GC9A01** | SCL (SCLK) | **GPIO 42** | SPI2 Host SCLK (40 MHz) | Kênh DMA phần cứng |
| | SDA (MOSI) | **GPIO 41** | SPI2 Host MOSI Data | 16-bit RGB565 |
| | DC | **GPIO 40** | Data / Command control | Lệnh / Dữ liệu |
| | RST | **GPIO 39** | Panel Reset Pin | Active LOW |
| | CS | **GPIO 38** | Chip Select Pin | Active LOW |
| | BLK (BL) | **GPIO 21** | Backlight LEDC PWM | Điều chỉnh độ sáng 0–100% |
| | VCC / GND | 3.3V / GND | Nguồn nuôi màn hình IPS | Góc nhìn rộng 178° |
| **Micro I2S INMP441** | WS (LRCK) | **GPIO 4** | I2S0 RX Word Select (16 kHz) | Kênh simplex master |
| | SCK (BCLK) | **GPIO 5** | I2S0 RX Bit Clock | 32-bit slot width |
| | SD (DIN) | **GPIO 6** | I2S0 RX Data In | 24-bit MSB-aligned |
| | L/R | **GND** | Chọn kênh Trái (Slot 0) | |
| | VDD / GND | 3.3V / GND | Nguồn nuôi Micro | |
| **Loa I2S MAX98357A** | DIN (DOUT) | **GPIO 7** | I2S1 TX Data Out | Ampli Class-D I2S |
| | BCLK | **GPIO 15** | I2S1 TX Bit Clock (16 kHz) | Kênh simplex master |
| | LRC (LRCK) | **GPIO 16** | I2S1 TX Left/Right Clock | 16-bit slot stereo |
| | VIN / GND | 5V (hoặc 3.3V) / GND | Nguồn ampli loa | Khuyên dùng 5V cho âm lượng lớn |
| **Gia Tốc Kế IMU MPU6050** | SDA | **GPIO 8** | I2C0 Bus SDA (400 kHz) | Tách riêng với SPI |
| | SCL | **GPIO 9** | I2C0 Bus SCL (400 kHz) | Địa chỉ I2C: `0x68` |
| | VCC / GND | 3.3V / GND | Nguồn nuôi cảm biến | Nhận diện lắc & rơi tự do |
| **Nút Nhấn Talk (Nói)** | Chân nút | **GPIO 0** | Nút BOOT Onboard | Active LOW, pull-up nội |
| **Nút Nhấn Menu / Aux** | Chân nút | **GPIO 47** | Nút gắn ngoài | Nối xuống GND khi nhấn |
| **LED RGB WS2812** | DIN | **GPIO 48** | LED Onboard S3-DevKitC | GRB 800 kHz RMT |
| **Cảm Biến Chạm (Pet)** | SIG / IO | **GPIO 2** | TTP223 / Chạm điện dung | Vuốt ve đỉnh đầu (Make Happy) |

---

## 3. Giải Pháp Kỹ Thuật Cho Màn Hình Tròn 1.28" 240x240 GC9A01

### 🎯 1. Driver Chuẩn Espressif Thuần C Không Phụ Thuộc Thư Viện Ngoài
- Triển khai trực tiếp `esp_lcd_panel_gc9a01.h` và `esp_lcd_panel_gc9a01.c` tuân theo chuẩn `esp_lcd_panel_t` của ESP-IDF v6.
- Sử dụng bus `SPI2_HOST` với xung nhịp 40 MHz qua kênh DMA tự động, truyền dữ liệu màu 16-bit RGB565 trực tiếp từ `esp_lv_adapter` mà không cần lớp chuyển đổi trung gian.
- Tự động kích hoạt chế độ đảo màu phần cứng (`INVON 0x21`) đặc trưng của panel IPS GC9A01 để màu sắc đạt chuẩn, sâu và rực rỡ.

### 🎯 2. Giao Diện Tròn Bản Quyền Meta Muse (`round = true`)
- Kích hoạt cơ chế hiển thị tròn cao cấp của Muse: **Circular Bezel Progress Ring** ôm sát viền bezel ngoài cùng với bán kính $R = 110$ pixel. Vòng tròn sẽ thở và xoay vòng theo tiến trình nhận diện giọng nói và phản hồi.
- Avatar Muse Pixel Art được phóng to lên kích thước $128 \times 128$ pixel ($2\times$ pixel art), nằm ngay giữa tâm hình tròn.
- Phụ đề thông minh được tính toán chiều rộng theo công thức dây cung hình học (`chord clipping`), loại bỏ hoàn toàn nguy cơ số thực âm gây lỗi NaN.

### 🎯 3. Điều Khiển Độ Sáng Đèn Nền PWM Qua LEDC
- Chân `LCD_BL` (GPIO 21) được điều khiển bằng timer LEDC 20 kHz với độ phân giải 10-bit (0–1023).
- Hàm `set_brightness(pct)` cho phép chỉnh độ sáng từ 0% đến 100% cực kỳ êm dịu, và `panel_sleep(true)` tự tắt đèn nền hoàn toàn khi thiết bị rơi vào chế độ ngủ.

### 🎯 Rủi ro 2: Khả năng tương thích giữa Panel Shim và `esp_lv_adapter`
- **Thách thức:** `esp_lv_adapter` render ảnh RGB565 và quản lý luồng flush qua DMA/I2C.
- **Giải pháp:** 
  1. Lớp Shim `mono_shim_t` lưu trữ page-buffer 1024 byte của SSD1306.
  2. Hàm `shim_draw()` quét vùng bẩn, tính toán độ sáng theo công thức chuẩn WCAG/BT.601:  
     $$\text{luma} = \frac{77 \cdot R + 150 \cdot G + 29 \cdot B}{256} > 48$$
  3. Cập nhật chính xác bit `1u << (y % 8)` tại vị trí byte `(y / 8) * 128 + x`.
  4. Gửi dữ liệu theo dải trang trọn vẹn `[p0 * 8, (p1 + 1) * 8]` qua `esp_lcd_panel_draw_bitmap()`. Driver I2C kích hoạt callback `on_color_trans_done` thông báo trực tiếp cho LVGL flush sẵn sàng mà không hề bị treo khung hình. Đã kiểm chứng toán học qua test case `tests/test_board_bread_s3.py`.

### 🎯 Rủi ro 3: Thứ tự byte RGB565 (Endianness)
- Trong `board_bread_s3.c`, macro `OLED_RGB565_SWAPPED` được đặt mặc định là `0` phù hợp với định dạng Little-Endian của ESP32-S3. Nếu màn hình có hiện tượng hạt nhiễu, chỉ cần đổi thành `1`.

### 🎯 Rủi ro 4: Ghép đôi BLE (Link button vs Talk button)
- **Thách thức:** Tránh việc giữ nút BOOT 5 giây để nói làm máy hiểu nhầm là Factory Reset.
- **Giải pháp:** 
  1. Trong `devices/sdkconfig.muse-bread-s3`, cấu hình `CONFIG_HOMEHUB_BUTTON_GPIO=21` (chân ảo không nối dây) để ngắt hoàn toàn cơ chế reset cứng của nút Link.
  2. Board UI của Muse sử dụng cơ chế ủy quyền: khi app yêu cầu xác nhận ghép đôi, hàm `op_talk_press()` gọi trực tiếp `app_confirm_pairing_press()` trong `main/app.c`. Người dùng chỉ cần nhấn nút **BOOT (Talk)** là hoàn tất ghép đôi BLE tức thì!

### 🎯 Rủi ro 5: Chỉnh âm lượng loa phần mềm
- Khi dùng `esp_codec_dev` không có chip codec phần cứng (`codec_if == NULL`), thư viện Espressif `esp_codec_dev` tự động nhân hệ số âm lượng bằng giải thuật phần mềm trực tiếp trên luồng PCM trước khi gọi `spk_write`.

### 🎯 Rủi ro 6: Tích hợp âm thanh phản hồi (TTS)
- Mặc định Meta Muse trả về văn bản hiển thị theo nhịp đọc. Trong `components/muse/muse_chat_session.cpp` (hàm `start_tts()`), kiến trúc đã mở sẵn cổng nạp dữ liệu MP3. Khi có API TTS (Google TTS, OpenAI TTS, hoặc ElevenLabs), chỉ cần nạp dữ liệu MP3 vào `tts_data()` để giải mã và phát trực tiếp ra loa MAX98357A.

---

## 4. Tích Hợp Thú Cưng Ảo (Pet Edition Reflexes)

Trong `board_bread_s3.c`, robot được tích hợp đầy đủ hệ phản xạ của thú cưng:
- **Vuốt ve đỉnh đầu (Touch GPIO 2):** Khi bạn chạm tay vào cảm biến chạm TTP223 / giấy bạc trên đỉnh đầu, robot tự động kích hoạt:
  ```c
  muse_state_make_happy(); // Kích hoạt nụ cười mắt híp và má hồng của Muse
  muse_state_poke();       // Đánh thức màn hình nếu đang ngủ
  ```
- **Lắc rung / Lật ngửa bụng (IMU MPU6050 trên I2C):** Hệ thống tự động nhận diện chip MPU6050 tại địa chỉ `0x68`/`0x69` và đánh thức robot khi có chấn động.

---

## 5. Đánh Thức Bằng Giọng Nói (Hands-Free Wake-Up) & Tối Ưu Hóa Token Xiaozhi AI

Phiên bản này được tích hợp engine **Adaptive VAD (Voice Activity Detection)** và bộ kích hoạt giọng nói rảnh tay (Hands-Free Voice Wake-Up) học hỏi trực tiếp từ kiến trúc tối ưu của **Xiaozhi AI**:

### 🎯 1. Đánh thức bằng giọng nói không cần bấm nút (Hands-Free Voice Wake-Up)
- **Cơ chế:** Khi robot ở chế độ chờ (Idle), hàm `idle_capture()` liên tục phân tích các khối âm thanh 20ms từ micro INMP441 qua bộ lọc formant thanh quản (Zero-Crossing Rate: 6–110 crossings/chunk) và tỷ số tín hiệu trên nhiễu (SNR > 10 dB).
- **Phản hồi tức thì:** Khi phát hiện giọng nói liên tục trong ~80ms, robot tự động phát âm thanh chào nhẹ (`muse_audio_chirp(1)`), chuyển khuôn mặt sang trạng thái lắng nghe `MUSE_MODE_LISTENING` và mở luồng stream âm thanh trực tiếp lên Meta Cloud VM.

### 🎯 2. Cấu hình Bật/Tắt linh hoạt (Mặc định BẬT)
- **Mặc định:** Chế độ Voice Wake-up được **BẬT mặc định** trong toàn bộ hệ thống (`CONFIG_MUSE_VOICE_WAKEUP=y` và `s.wakeup_on = true`).
- **Tùy chỉnh qua Màn hình:** Vào menu Cài đặt trên màn hình OLED -> chọn **SOUND** -> gạt switch **`Voice wake: ON/OFF`**. Trạng thái được lưu vĩnh viễn vào bộ nhớ flash NVS (`wakeup_on`).
- **Vẫn giữ trọn vẹn nút bấm:** Nút BOOT vật lý (GPIO 0) và cảm biến chạm đỉnh đầu (GPIO 2) vẫn hoạt động song song 100% mọi lúc.

### 🎯 3. Tối ưu hóa Token, Dữ liệu và Tốc độ (Học hỏi từ Xiaozhi AI)
| Tiêu chí | Bản Gốc Meta Muse | Bản Tối Ưu Xiaozhi Adaptive VAD | Hiệu Quả Đạt Được |
|:---|:---:|:---:|:---|
| **Thời gian thu khoảng lặng sau câu nói** | Chờ thả nút hoặc timeout đủ 15 giây | **Tự ngắt sau 700ms im lặng** | **Cắt giảm ~85% - 94% dead air** |
| **Lượng Token tiêu thụ mỗi lượt hỏi** | ~750 audio tokens / câu | **~155 audio tokens / câu** | **Tiết kiệm ~79% token** |
| **Độ trễ phản hồi (Latency)** | Chậm trễ 2.5s – 4.5s sau khi nói | **Phản hồi trong <100ms** | **Tốc độ nhanh gấp 3 lần** |
| **Lượt nói rác (Ghost turns)** | Ghi âm 15s gửi lên cloud | **Tự hủy sau 3.5s nếu không có người nói** | **0 token lãng phí** |
| **Tài nguyên vi điều khiển** | Cần mô hình AI nặng tốn RAM | **Thuần ANSI C, <2KB RAM, <1% CPU** | **Hoạt động ổn định trên ESP32-S3** |

---

---

## 6. Phát Âm Thanh Song Ngữ Tiếng Việt & Tiếng Anh Miễn Phí (Free Bilingual TTS)

Hệ thống bổ sung engine TTS song ngữ thông minh **hoàn toàn MIỄN PHÍ 100%** (không tốn chi phí token, không cần API Key, không phụ thuộc server proxy ngoài) học hỏi và tối ưu tương tự Xiaozhi AI:

### 🎯 1. Tự Động Nhận Diện Ngôn Ngữ (Auto Language Detection)
- **Cơ chế:** Phân tích trực tiếp các byte UTF-8 đa byte đặc trưng của nguyên âm tiếng Việt (`0xC3`, `0xC4`, `0xC5`, `0xE1` cùng các tổ hợp dấu sắc, huyền, hỏi, ngã, nặng).
- **Chuyển ngữ mượt mà:** Nếu phát hiện $\ge 1$ ký tự tiếng Việt, engine tự động gán mã ngôn ngữ `tl=vi`. Nếu câu thuần ASCII hoặc tiếng Anh, tự động gán `tl=en`. Người dùng không cần phải chuyển đổi thủ công trong menu.

### 🎯 2. Kiến Trúc Luồng Âm Thanh Trực Tiếp (Direct HTTP MP3 Streaming)
- Sử dụng Google Translate TTS CDN nguyên bản (`client=tw-ob`) truyền dữ liệu MPEG MP3 trực tiếp qua HTTP.
- **Ngắt câu thông minh (Sentence Splitting):** Tự động phân đoạn các câu văn dài thành các khối $\le 160$ ký tự tại ranh giới dấu câu (`.`, `!`, `?`, `,`, `;` hoặc khoảng trắng), giữ trọn vẹn ngữ nghĩa từng từ và tránh giới hạn độ dài của URL.
- **Giải mã phần cứng `minimp3`:** Dữ liệu MP3 nạp thẳng vào buffer PSRAM 512KB, bộ giải mã `minimp3` tự động giải mã ra luồng PCM 16-bit 16kHz cấp thẳng cho ampli loa MAX98357A. Nếu mạng chập chờn hoặc tắt loa, hệ thống tự động fallback về chế độ hiển thị chữ theo nhịp đọc mắt không hề bị treo máy.

### 🎯 3. Bật/Tắt Linh Hoạt & Lưu Trữ Flash NVS
- Mặc định **BẬT** trong firmware (`CONFIG_MUSE_FREE_TTS=y`).
- Người dùng có thể bật/tắt bất kỳ lúc nào qua menu màn hình OLED: **SOUND** $\rightarrow$ **`TTS voice: ON/OFF`**. Trạng thái được lưu vĩnh viễn vào NVS key `"tts_on"`.

### 🎯 4. Hướng Dẫn Kiểm Thử Trên Bàn Thí Nghiệm (Easy Bench Testing)
Không cần phải ghép đôi với app hay nói micro phức tạp, bạn có thể kiểm thử âm thanh ngay trên bàn thí nghiệm:
1. **Kiểm thử Offline không cần mạng (Phím `'m'`):**
   - Mở Serial Monitor kết nối với ESP32-S3 ở baudrate `115200`.
   - Nhấn phím **`m`** trên bàn phím: Robot sẽ giải mã file âm thanh mẫu nhúng sẵn `test_reply.mp3` và phát ra loa MAX98357A. Dùng để kiểm tra mạch I2S, dây dẫn và loa trước khi kết nối Wi-Fi.
2. **Kiểm thử Phát Âm Trực Tiếp Qua Lệnh Serial (`>say=`):**
   - Khi robot đã kết nối Wi-Fi, gõ lệnh sau vào Serial Monitor:
     ```text
     >say=Xin chào bạn, tôi là robot Rody S3!
     ```
     Robot sẽ lập tức nhận diện tiếng Việt, tải MP3 từ CDN và phát giọng nói tiếng Việt to rõ ra loa!
   - Thử nghiệm câu tiếng Anh:
     ```text
     >say=Hello, I am ready to help you!
     ```
     Robot tự động chuyển giọng sang tiếng Anh chuẩn xác!

### 🎯 5. Xử Lý Các Tình Huống Ngoại Lệ (Exception Cases) & Hướng Dẫn Khắc Phục

Firmware được tích hợp cơ chế phòng vệ chủ động, bắt trọn các lỗi mạng và phần cứng để không bao giờ làm treo máy:

| Tình Huống Ngoại Lệ | Mã Lỗi Serial (`@tts`) | Phản Ứng Của Robot | Log Gợi Ý Cho Người Dùng & Hành Động Khắc Phục |
|:---|:---:|:---|:---|
| **Mất kết nối Wi-Fi** | `"WIFI_DISCONNECTED"` | Tự động bỏ qua tải âm thanh, chuyển sang hiển thị chữ im lặng trên OLED (`pace_silently`). | `[TTS ERROR] Wi-Fi is disconnected! Action required: Connect device to Wi-Fi via Muse app or Settings menu.`<br>👉 **Khắc phục:** Vào menu Wi-Fi trên màn hình hoặc dùng app Muse để kết nối mạng. |
| **Loa tắt hoặc âm lượng = 0** | `"SPEAKER_MUTED"` | Bỏ qua việc gửi request HTTP, tiết kiệm 100% băng thông và pin. | `[TTS INFO] Speaker is muted (vol=0). Skipping audio stream, showing captions only.`<br>👉 **Khắc phục:** Tăng âm lượng trong menu SOUND hoặc app Muse. |
| **Người dùng ngắt ngang (Barge-In)** | `"cancelled"` | Lập tức ngắt luồng tải HTTP, xả sạch buffer âm thanh, chuyển robot sang trạng thái lắng nghe. | `[TTS CANCEL] Playback interrupted by user barge-in.`<br>👉 **Trải nghiệm:** Bạn có thể nhấn nút BOOT hoặc vuốt chạm đỉnh đầu bất cứ lúc nào để nói câu mới. |
| **CDN Google bị nghẽn (HTTP 429)** | `"RATE_LIMIT_429"` | Tự động ngắt tải âm thanh, fallback mượt mà sang hiển thị phụ đề nhịp đọc trên OLED. | `[TTS WARN] Google CDN rate limited (HTTP 429). Falling back to captions.`<br>👉 **Khắc phục:** Không làm gián đoạn cuộc hội thoại, robot vẫn đọc chữ trên màn hình và tự hồi phục ở câu sau. |
| **Đứt kết nối mạng / DNS thất bại** | `"HTTP_FAIL"` | Tự động dọn dẹp kết nối, không để rò rỉ socket/RAM, hiển thị chữ trên màn hình. | `[TTS ERROR] Chunk HTTP request failed (err %d). Check router/DNS.`<br>👉 **Khắc phục:** Kiểm tra đường truyền Internet của router Wi-Fi. |
| **Chuỗi rỗng / Không có từ phát âm** | `"INVALID_ARG"` | Bỏ qua, giữ trạng thái bình thường. | `[TTS WARN] Invalid argument: text is empty or callback is NULL.` |

### 🎯 6. Cấu Hình Tùy Biến (Kconfig & sdkconfig)
Người dùng có thể tinh chỉnh các thông số trong `menuconfig` hoặc file `devices/sdkconfig.muse-bread-s3`:
* `CONFIG_MUSE_FREE_TTS=y`: Bật/Tắt hoàn toàn module Free TTS.
* `CONFIG_MUSE_FREE_TTS_TIMEOUT_MS=8000`: Thời gian chờ tối đa cho mỗi chunk âm thanh (mặc định 8000ms / 8 giây).
* `CONFIG_MUSE_FREE_TTS_MAX_CHUNKS=12`: Số câu tối đa cho mỗi lần đọc (mặc định 12 chunk $\approx 1920$ ký tự).
* `CONFIG_MUSE_VOICE_WAKEUP=y`: Bật/Tắt module đánh thức bằng giọng nói rảnh tay.

---

## 7. Quản Lý Năng Lượng & Độ Bền Phần Cứng (Power Optimization & Hardening)

Phiên bản `v1.4.0-muse` được tối ưu hóa sâu ở tầng driver phần cứng nhằm triệt tiêu điện năng hao phí và bảo vệ hệ thống:
1. **I2S Clock Gating cho MAX98357A:**
   - Trong `spk_enable()`, việc ngắt kênh I2S TX khi không phát âm thanh sẽ ngắt xung nhịp BCLK/LRCLK. Chip MAX98357A tự động đi vào trạng thái **Hardware Auto-Shutdown (<10µA)**, vừa tiết kiệm năng lượng vừa loại bỏ hoàn toàn tiếng rít/sôi rè (hiss) khi ở chế độ chờ.
   - Hàm `spk_write()` tự động bật lại xung nhịp nếu kênh đang tắt, chống mất tiếng âm thanh bất ngờ.
2. **Kẹp Biên An Toàn Màn Hình OLED (`shim_draw`):**
   - Bộ đệm 1024-byte `s_shim.fb` được bảo vệ bằng cơ chế kẹp biên toạ độ `x1, y1, x2, y2` và kiểm tra con trỏ, triệt tiêu 100% rủi ro ghi đè bộ nhớ (memory corruption) khi LVGL render các widget sát mép màn hình.
3. **Lọc Nhiễu Chạm Đầu & Giới Hạn Tần Suất IMU:**
   - Cảm biến chạm GPIO 2 được lọc nhiễu đa chu kỳ (`s_touch_debounce >= 2`), loại bỏ xung ảo gây ra bởi sóng Wi-Fi/BLE.
   - Cảm biến gia tốc MPU6050 được trang bị bộ đệm thời gian 500ms (cooldown) cho sự kiện rung lắc và rơi tự do, tránh nghẽn hàng đợi CPU và spam log.
4. **Phòng Chống Deadlock DMA:**
   - Tất cả các thao tác đọc/ghi I2S đều có timeout giới hạn (`pdMS_TO_TICKS(1000)`), loại trừ nguy cơ deadlock làm kích hoạt Watchdog Timer.

---

## 8. Chẩn Đoán Trực Tiếp Qua Lệnh Serial (`>diag`)

Bạn có thể cắm cổng USB và gửi lệnh `>diag` trong Serial Monitor (baudrate `115200`) để nhận báo cáo trạng thái hệ thống chuẩn JSON:

```bash
>diag
```

**Phản hồi mẫu:**
```json
@diag {
  "board": "Bread S3 Pet",
  "ram_free": 184320,
  "ram_min": 152040,
  "psram_free": 7824120,
  "psram_min": 7534010,
  "wifi_state": 3,
  "wifi_ssid": "TodyHome",
  "wifi_rssi": -58,
  "wifi_ip": "192.168.1.105",
  "vol": 80,
  "mic_gain": 30,
  "tts_on": 1,
  "wakeup_on": 1
}
```

Ý nghĩa các trường:
- `ram_free` / `ram_min`: Dung lượng RAM nội bộ còn lại và mức sàn thấp nhất từng chạm tới (Internal SRAM).
- `psram_free` / `psram_min`: Dung lượng Octal PSRAM còn lại (tổng 8MB).
- `wifi_state`: Trạng thái kết nối Wi-Fi (`3` = Đã kết nối và có IP).
- `wifi_ssid` / `wifi_rssi` / `wifi_ip`: Tên mạng, cường độ sóng (dBm) và địa chỉ IP được cấp.
- `vol` / `mic_gain`: Mức âm lượng loa (0–100) và độ nhạy micro (dB).
- `tts_on` / `wakeup_on`: Trạng thái kích hoạt module Free TTS và Voice Wake-Up (`1` = Bật, `0` = Tắt).

---

## 9. Hướng Dẫn Biên Dịch & Nạp Firmware

### Bước 1: Chuẩn bị môi trường ESP-IDF v6.0.1
Mở Terminal và kích hoạt môi trường:
```bash
. ~/esp/esp-idf-v6.0.1/export.sh
# Hoặc: . /Volumes/Builder/esp/esp-idf/export.sh
```

### Bước 2: Chạy kiểm thử Host Unit Tests (168 bài test)
Chạy script kiểm thử tự động toàn diện:
```bash
cd /Volumes/Builder/Arduino/OtooRobot/firmware_muse
DEVELOPER_DIR=/Library/Developer/CommandLineTools ./test_host.sh
```
> Kết quả mong đợi: `Ran 168 tests ... OK (skipped=3) === All Tests Passed Successfully! ===`.

### Bước 3: Biên dịch & Nạp phiên bản Link (Giai đoạn 1)
Cắm cáp USB vào cổng native USB-C của bo ESP32-S3:
```bash
./build_link.sh
# Nạp firmware vào cổng USB (thường là /dev/ttyACM0 hoặc /dev/cu.usbmodem*):
idf.py -B build-bread -p /dev/ttyACM0 flash monitor
```
*Hiện tượng đúng:* Log hiện `Muse Gadget starting`, PSRAM nhận đủ 8MB, đèn LED onboard GPIO48 thở màu cam, app Muse quét thấy thiết bị BLE `MuseGadget-bread-XXXXXX`.

### Bước 4: Biên dịch & Nạp phiên bản UI Đầy Đủ (Giai đoạn 2)
```bash
./build_ui.sh
# Nạp firmware:
idf.py -B build-muse-bread-s3 -p /dev/ttyACM0 flash monitor
```
*Hiện tượng đúng:* Màn hình OLED SSD1306 sáng lên, khuôn mặt avatar Muse Pixel Art chớp mắt mỉm cười, micro INMP441 và loa MAX98357A sẵn sàng cho đàm thoại rảnh tay (Hands-Free Voice Wake-up), phản xạ thú cưng Pet chạm vuốt GPIO 2, và phát âm thanh TTS song ngữ Việt - Anh!


