# 🤖 Musedy S3 - Robot Trí Tuệ Nhân Tạo Mini (Retro AI Companion)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![ESP-IDF](https://img.shields.io/badge/ESP--IDF-v5.1%2B-red.svg)](https://idf.espressif.com/)
[![Tests](https://img.shields.io/badge/Tests-181%20Passed-emerald.svg)](./test_host.sh)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live%20Demo-cyan.svg)](https://tody-agent.github.io/musedy/)
[![MakerWorld](https://img.shields.io/badge/MakerWorld-%231967811-blue.svg)](https://makerworld.com/en/models/1967811-xiaozhi-ai-computer-xiaozhi#profileId-2115633)

**Musedy S3** là robot trí tuệ nhân tạo để bàn thế hệ mới, kết hợp hoàn hảo giữa hình hài máy tính cổ điển Macintosh CRT thập niên 80 (màu Xanh Dương & Trắng Sữa) với bộ vi xử lý lõi kép **ESP32-S3 N16R8**:
- 🗣️ **Voice Wakeup kích hoạt tức thì:** Nhận diện từ khóa giọng nói ("Rody ơi" / "Musedy") và tự động ngắt lời (Barge-in).
- 🎙️ **Giọng nói tiếng Việt mượt mà:** Tích hợp engine Zero-Token Edge TTS & Google Translate TTS, không tốn chi phí API token.
- 📺 **Màn hình 1.8" TFT 160x128 Xoay Ngang (ST7735 / ST7789):** Tỉ lệ hiển thị ngang 5:4 chuẩn cho khung vỏ máy tính retro, và tùy chọn 1.28" tròn GC9A01 240x240, 30 FPS mượt mà.
- 🔊 **Âm học loa vòm 3W dội sàn:** Mạch giải mã I2S MAX98357A kết hợp buồng kín chống đoản mạch âm, cho chất âm trầm ấm rõ tiếng.
- 📐 **Hỗ trợ 2 phong cách vỏ in 3D:** Mẫu Máy Tính Retro Xiaozhi Computer Edition (kèm ngàm in 3D `cad/stl/musedy_computer_18_adapter.stl`) & Quả Cầu Astro-Pod.

---

## 🌐 Trải Nghiệm Trực Tuyến & Tài Liệu Nhanh

- 🚀 **Trang chủ & Giả lập Simulator trực tiếp:** [https://tody-agent.github.io/musedy/](https://tody-agent.github.io/musedy/)
- ⚡ **Sơ đồ kết nối phần cứng & Pinout:** [https://tody-agent.github.io/musedy/wiring.html](https://tody-agent.github.io/musedy/wiring.html) (File Markdown: [`docs/WIRING_DIAGRAM.md`](docs/WIRING_DIAGRAM.md))
- 🛠️ **Cẩm nang triển khai & nạp firmware:** [https://tody-agent.github.io/musedy/deploy.html](https://tody-agent.github.io/musedy/deploy.html) (File Markdown: [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md))
- 🖥️ **Hướng dẫn lắp vỏ máy tính cổ điển:** [`docs/XIAOZHI_COMPUTER_GUIDE.md`](docs/XIAOZHI_COMPUTER_GUIDE.md)
- 🛸 **Hướng dẫn lắp quả cầu Astro-Pod:** [`docs/ASSEMBLY_GUIDE.md`](docs/ASSEMBLY_GUIDE.md)

---

## ⚡ Sơ Đồ Chân Kết Nối (Hardware Pinout)

| Thiết Bị | Chân Module | Chân ESP32-S3 | Ghi Chú Kỹ Thuật |
| :--- | :--- | :---: | :--- |
| **Màn Hình 1.8" / GC9A01** | SCLK / MOSI / DC / RST / CS / BLK | **42, 41, 40, 39, 38, 21** | 160x128 Landscape ST7735 / 240x240 GC9A01, SPI Master 40MHz, PWM Backlight |
| **Micro I2S INMP441** | WS / SCK / SD / L/R | **4, 5, 6, GND** | Kênh Trái (Left Channel), thu âm đa hướng |
| **Ampli MAX98357A** | BCLK / LRC / DIN / VIN | **15, 16, 7, 5V (VBUS)** | Nguồn 5V cho công suất 3W RMS (Loa 4Ω) |
| **6-DOF IMU MPU6050** | SDA / SCL | **8, 9** | I2C0 Master, nhận diện nghiêng/lắc/rơi |
| **Cảm Ứng Đỉnh Đầu** | Chạm điện dung | **GPIO 2** | Vuốt chạm tương tác cảm xúc |
| **Nút Bấm** | BOOT (Talk) / Aux Menu | **GPIO 0, GPIO 47** | Nhấn nói chuyện / BLE Pairing |

---

## 🚀 Hướng Dẫn Bắt Đầu Nhanh (Quick Start)

### 1. Kiểm thử mã nguồn trước trên máy tính (181 tests)
```bash
git clone https://github.com/tody-agent/musedy.git
cd musedy

# Chạy toàn bộ 181 test tự động không cần cắm mạch:
DEVELOPER_DIR=/Library/Developer/CommandLineTools ./test_host.sh
```

### 2. Cấu hình thiết bị & nạp firmware qua ESP-IDF
```bash
# Thiết lập target ESP32-S3
idf.py set-target esp32s3

# Áp dụng cấu hình chuẩn Musedy Computer (Màn hình 1.8" TFT 160x128 Xoay Ngang)
cp devices/sdkconfig.muse-computer-18 sdkconfig

# Biên dịch mã nguồn
idf.py build

# Nạp vào mạch và mở Serial Monitor
idf.py -p /dev/cu.usbmodem1101 flash monitor
```

### 3. Cấu hình Wi-Fi nhanh qua Serial
Khi mở Serial Monitor (115200 baud), gửi lệnh:
```text
>wifi=Ten_Wifi_Cua_Ban,Mat_Khau_Wifi
>say=Xin chào! Mình là robot Musedy!
```

---

## 🧩 Cấu Trúc Dự Án (Repository Architecture)

```
musedy/
├── index.html                   # Landing page chính trên GitHub Pages
├── wiring.html                  # Sơ đồ kết nối phần cứng tương tác
├── deploy.html                  # Cẩm nang triển khai & lệnh nạp firmware
├── docs/                        # Tài liệu chi tiết & ảnh render
│   ├── WIRING_DIAGRAM.md        # Sơ đồ đấu nối chi tiết
│   ├── DEPLOYMENT_GUIDE.md      # Hướng dẫn build & flash
│   ├── XIAOZHI_COMPUTER_GUIDE.md # Cẩm nang vỏ máy tính màu xanh dương
│   ├── ASSEMBLY_GUIDE.md        # Hướng dẫn lắp ráp quả cầu Astro-Pod
│   └── designs/                 # Bản vẽ và hình render 3D
├── cad/                         # File thiết kế tham số OpenSCAD
│   ├── xiaozhi_gc9a01_adapter.scad # Ngàm chuyển màn hình tròn CRT
│   └── rody_s3_astropod.scad    # Quả cầu Astro-Pod nguyên khối
├── Computer/                    # File in 3D STL vỏ máy tính retro
├── components/                  # Các module phần cứng ESP-IDF (muse, GC9A01, audio)
├── devices/                     # Cấu hình overlay cho từng dòng phần cứng
├── main/                        # Điểm khởi chạy firmware ESP32-S3
├── test_host.sh                 # Runner chạy 174 bài test tự động
└── tests/                       # Bộ kiểm thử dung sai, driver và thuật toán
```

---

## 📜 Giấy Phép & Tác Quyền

- Mã nguồn firmware phát triển theo giấy phép mã nguồn mở **Apache-2.0**.
- Thiết kế vỏ máy tính cổ điển mini bởi **董老爺 (Mr. Dong)** trên [MakerWorld #1967811](https://makerworld.com/en/models/1967811-xiaozhi-ai-computer-xiaozhi#profileId-2115633).
- Ngôn ngữ thiết kế web & UI tuân thủ hệ thống thiết kế **Meta Astryx**.
