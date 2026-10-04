# 🚀 Hướng Dẫn Triển Khai & Nạp Firmware Robot Musedy (Deployment Guide)

> **Dự án:** Robot Trí Tuệ Nhân Tạo **Musedy** (Musedy S3 AI Companion)  
> **Nền tảng:** ESP-IDF v5.1+ / PlatformIO / Python CLI  
> **Vi điều khiển mục tiêu:** ESP32-S3 (N16R8: 16MB Flash, 8MB Octal PSRAM)  
> **Trang chủ & Tài liệu:** [https://tody-agent.github.io/musedy/](https://tody-agent.github.io/musedy/)

---

## 1. Yêu Cầu Chuẩn Bị (Prerequisites)

### 1.1. Phần Cứng Cần Thiết
1. **Bo mạch ESP32-S3:** Phiên bản N16R8 (16MB Flash, 8MB PSRAM Octal).
2. **Cáp Type-C:** Cáp truyền dữ liệu chất lượng tốt (không dùng cáp chỉ có dây sạc).
3. **Màn hình hiển thị:** Màn hình tròn 1.28" GC9A01 SPI (240x240) hoặc ST7789 2.0" vuông.
4. **Âm thanh:** Micro I2S INMP441 + Khuếch đại MAX98357A + Loa 4Ω 3W.

### 1.2. Môi Trường Phần Mềm (Toolchain)
- **Hệ điều hành:** macOS, Linux (Ubuntu/Debian), hoặc Windows 11 (WSL2 / PowerShell).
- **ESP-IDF:** Phiên bản v5.1 hoặc mới hơn (đã cài `idf.py`).
- **Python:** 3.10+ kèm `esptool`, `pyserial`, `requests`.
- **Clang / LLVM (Tùy chọn):** Dùng để chạy 174 bài host test cục bộ trên máy tính không cần phần cứng.

---

## 2. Quy Trình Cài Đặt & Triển Khai Từng Bước

### Bước 1: Sao Chép Mã Nguồn (Clone Repository)
```bash
git clone https://github.com/tody-agent/musedy.git
cd musedy
```

### Bước 2: Chạy Bộ Test Kiểm Thử Tự Động (Host Verification)
Trước khi nạp vào mạch thực, kiểm tra toàn bộ 174 bài test dung sai vỏ máy tính, driver màn hình GC9A01, thuật toán Voice Wakeup VAD và Edge TTS:
```bash
# Trên macOS:
DEVELOPER_DIR=/Library/Developer/CommandLineTools ./test_host.sh

# Trên Linux:
./test_host.sh
```
*Kết quả hiển thị `Ran 174 tests ... OK` xác nhận môi trường và mã nguồn hoàn toàn ổn định.*

---

### Bước 3: Cấu Hình Thiết Bị (Device Configuration)

Dự án cung cấp sẵn cấu hình tối ưu cho các mẫu phần cứng khác nhau trong thư mục `devices/`:

| Tên Cấu Hình | Màn Hình | Mục Đích Sử Dụng |
| :--- | :--- | :--- |
| **`devices/sdkconfig.muse-computer-18`** | **1.8" TFT 160x128 Xoay Ngang** | Khuyên dùng cho Vỏ máy tính retro (MakerWorld #1967811) kèm ngàm in 3D |
| **`devices/sdkconfig.muse-bread-s3`** | **1.8" Landscape / GC9A01 1.28"** | Cấu hình mặc định cho bo mạch Musedy S3 đa năng |
| **`devices/sdkconfig.muse`** | **ST7789 2.0" Vuông** | Dành cho mẫu máy tính Xiaozhi tiêu chuẩn |

Áp dụng cấu hình chuẩn:
```bash
# Thiết lập target là ESP32-S3
idf.py set-target esp32s3

# Nạp file cấu hình chuẩn Musedy Computer (1.8" TFT 160x128 Xoay Ngang)
cp devices/sdkconfig.muse-computer-18 sdkconfig
```

Hoặc tùy chỉnh trực quan qua menu:
```bash
idf.py menuconfig
```
*Các tùy chọn quan trọng:*
- `Component config -> Muse -> Display Panel & Resolution for Musedy S3`:
  - `CONFIG_MUSE_DISPLAY_180_LANDSCAPE`: Màn hình 1.8" TFT 160x128 xoay ngang ST7735.
  - `CONFIG_MUSE_DISPLAY_GC9A01_ROUND`: Màn hình tròn 1.28" GC9A01 240x240.
- `Component config -> Muse Configuration`:
  - `CONFIG_MUSE_VOICE_WAKEUP`: Bật/tắt nhận diện từ khóa giọng nói ("Rody ơi" / "Musedy").
  - `CONFIG_MUSE_FREE_TTS`: Bật tính năng phát âm thanh tiếng Việt miễn phí (Edge / Google TTS).

---

### Bước 4: Biên Dịch Firmware (Build)
```bash
idf.py build
```
Thời gian biên dịch lần đầu khoảng 2-4 phút tùy theo cấu hình máy tính.

---

### Bước 5: Nạp Firmware Vào Bo Mạch (Flash Firmware)

1. Cắm cáp Type-C nối ESP32-S3 vào máy tính.
2. Xác định cổng Serial (ví dụ: `/dev/ttyUSB0` trên Linux, `/dev/cu.usbmodem*` trên macOS, hoặc `COM5` trên Windows).
3. Thực hiện nạp firmware và nạp bảng phân vùng Flash (Partitions):

```bash
# Thay thế /dev/cu.usbmodem... bằng cổng thực tế của bạn
idf.py -p /dev/cu.usbmodem1101 flash monitor
```

> 💡 *Mẹo: Nếu mạch không tự động vào chế độ nạp, hãy nhấn giữ nút **BOOT (GPIO 0)**, nhấn nhả nút **RESET**, sau đó thả nút **BOOT**.*

---

## 3. Cấu Hình Wi-Fi & Kích Hoạt Robot

### 3.1. Cấu Hình Qua Cổng Serial (Nhanh nhất)
Mở cửa sổ dòng lệnh Serial (115200 baud) và gửi lệnh:
```text
>wifi=Ten_Wifi,Mat_Khau_Wifi
```
Robot sẽ lưu thông tin mạng vào bộ nhớ NVS mã hóa và tự động kết nối sau mỗi lần khởi động.

### 3.2. Cấu Hình Qua Bluetooth BLE (Web Setup)
1. Bật nguồn robot, màn hình sẽ hiển thị biểu tượng Bluetooth chờ ghép nối.
2. Mở trình duyệt Chrome trên điện thoại hoặc máy tính hỗ trợ Web Bluetooth:
   - Truy cập công cụ cấu hình đi kèm: `tools/muse/ble_setup.html`
3. Quét tìm thiết bị tên `Musedy-XXXX`, nhập mật khẩu Wi-Fi và bấm **Connect**.

---

## 4. Các Lệnh Điều Khiển & Chẩn Đoán Serial (CLI Diagnostic)

Khi mở Serial Monitor (`idf.py monitor` hoặc qua PuTTY / screen), bạn có thể gửi các lệnh trực tiếp sau:

| Lệnh Serial | Mô Tả Chức Năng |
| :--- | :--- |
| `>diag` | In báo cáo tình trạng hệ thống: RAM, PSRAM, Flash, nhiệt độ chip, pin, Wi-Fi RSSI |
| `>say=Xin chào bạn!` | Thử nghiệm phát âm câu thoại tiếng Việt ngay lập tức qua loa |
| `>wakeup=on` / `>wakeup=off` | Bật hoặc tắt chế độ Voice Wakeup thường trực |
| `>tts=edge` / `>tts=google` | Chuyển đổi giữa engine phát âm Edge TTS hoặc Google TTS |
| `>emotion=happy` | Thay đổi biểu cảm mắt robot (*standby, happy, listening, speaking, thinking*) |
| `>reboot` | Khởi động lại vi điều khiển |

---

## 5. Xử Lý Sự Cố Thường Gặp (Troubleshooting)

### Màn hình GC9A01 không sáng hoặc hiển thị sọc nhiễu
- Kiểm tra lại chân **BLK (GPIO 21)** đã có tín hiệu PWM.
- Kiểm tra chiều dài dây SPI $\le 50\text{ mm}$ và đã đấu đúng MOSI=GPIO 41, SCLK=GPIO 42.

### Micro không thu được tiếng hoặc loa bị rè
- Kiểm tra chân **L/R của INMP441** đã được nối xuống **GND** (chọn kênh Trái).
- Cấp nguồn cho chân **VIN của MAX98357A** bằng nguồn **5V VBUS** thay vì nguồn 3.3V để tránh sụt áp gây méo tiếng.
- Đảm bảo buồng loa kín khí bằng đệm mút EVA.
