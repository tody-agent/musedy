# ⚡ Sơ Đồ Kết Nối Phần Cứng & Pinout Robot Musedy (Musedy S3)

> **Dự án:** Robot Trí Tuệ Nhân Tạo **Musedy** (Musedy AI Companion)  
> **Vi điều khiển trung tâm:** ESP32-S3 N16R8 (16MB Flash, 8MB Octal PSRAM, Dual-Core 240MHz)  
> **Hỗ trợ vỏ:** Mẫu Máy Tính Cổ Điển Mini (Retro Computer) & Quả Cầu Astro-Pod  
> **Tài liệu trực tuyến:** [https://tody-agent.github.io/musedy/](https://tody-agent.github.io/musedy/) | [Sơ đồ tương tác](https://tody-agent.github.io/musedy/wiring.html)

---

## 1. Sơ Đồ Tổng Quan Khối Phần Cứng (System Block Diagram)

```
                     +---------------------------------------+
                     |         Nguồn Pin / Cổng Sạc          |
                     |   Pin LiPo 3.7V 800-1200mAh + TP4056  |
                     |           Hoặc Cáp Type-C 5V          |
                     +-------------------+-------------------+
                                         | 5V / 3.3V
                                         v
+-----------------------------------------------------------------------------------+
|                            ESP32-S3 N16R8 BOARD                                   |
|                                                                                   |
|  [SPI Master]       [I2S0 RX - Mic]    [I2S1 TX - Amp]    [I2C0]     [Touch/GPIO] |
|   GPIO 42: SCLK      GPIO 4: WS         GPIO 15: BCLK      GPIO 8:    GPIO 2:     |
|   GPIO 41: MOSI      GPIO 5: SCK        GPIO 16: LRCK        SDA        Touch Pad |
|   GPIO 40: DC        GPIO 6: SD (DIN)   GPIO 7:  DOUT      GPIO 9:    GPIO 0:     |
|   GPIO 39: RST                                               SCL        BOOT/Talk |
|   GPIO 38: CS                                                         GPIO 47:    |
|   GPIO 21: Backlight                                                    Aux Menu  |
+---------+------------------+------------------+--------------+------------+-------+
          |                  |                  |              |            |
          v                  v                  v              v            v
+------------------+ +---------------+ +----------------+ +---------+ +-----------+
| Màn Hình Tròn    | | Micro I2S     | | Khuếch Đại     | | 6-DOF   | | Cảm Ứng   |
| GC9A01 1.28"     | | INMP441       | | MAX98357A Mono | | IMU     | | Chạm Đỉnh |
| 240x240 RGB565   | | Đa Hướng      | | Loa Hộp 3W 4Ω  | | MPU6050 | | & Phím Cơ |
+------------------+ +---------------+ +----------------+ +---------+ +-----------+
```

---

## 2. Bảng Tra Cứu Pinout Chi Tiết (Pin Mapping Matrix)

### 2.1. Màn Hình 1.8" TFT 160x128 Xoay Ngang (ST7735 / ST7789 SPI) & GC9A01 1.28"
| Ký Hiệu Chân Màn Hình (ST7735 / GC9A01) | Chân ESP32-S3 | Màu Dây Gợi Ý | Chức Năng Kỹ Thuật |
| :--- | :---: | :---: | :--- |
| **VCC** | **3.3V (hoặc 5V)** | Đỏ | Nguồn cấp cho chip điều khiển màn hình và đèn nền |
| **GND** | **GND** | Đen | Nối mass chung hệ thống |
| **SCL / SCLK / SCK** | **GPIO 42** | Vàng | Xung nhịp SPI Clock (40MHz SPI Master DMA) |
| **SDA / MOSI** | **GPIO 41** | Xanh lá | Đường truyền dữ liệu hình ảnh (Data Out) |
| **DC / A0 / RS** | **GPIO 40** | Cam | Lựa chọn Lệnh (Command) / Dữ liệu (Data) |
| **RES / RST / RESET** | **GPIO 39** | Trắng | Reset phần cứng màn hình (Active Low) |
| **CS** | **GPIO 38** | Xanh dương | Chip Select chọn chip màn hình (Active Low) |
| **BLK / LED / BL** | **GPIO 21** | Tím | Điều chế độ sáng đèn nền LED qua PWM (LEDC) |

> 💡 **Khả năng tương thích:**  
> - **Màn hình 1.8" TFT 128x160 (ST7735 / ST7789):** Chuẩn 8 chân cắm SPI phổ biến nhất trong giới maker. Firmware tự động xoay ngang 160x128 pixel (`swap_xy = true`) phù hợp hoàn hảo với tỷ lệ 5:4 của cửa sổ vỏ máy tính retro `Computer/obj_2_Object_1.stl`.  
> - **Màn hình tròn 1.28" IPS GC9A01 (240x240):** Dùng chung hoàn toàn sơ đồ chân GPIO 38–42, 21. Có thể chuyển đổi qua lại dễ dàng chỉ bằng 1 tùy chọn Kconfig.

---

### 2.2. Module Thu Âm Microphone I2S (INMP441 Omnidirectional)
Microphone kỹ thuật số độ nhạy cao, thu âm giọng nói tự nhiên cho tính năng nhận dạng giọng nói và Voice Wakeup ("Rody ơi" / "Musedy"):

| Chân Module INMP441 | Chân ESP32-S3 | Màu Dây Gợi Ý | Chức Năng Kỹ Thuật |
| :--- | :---: | :---: | :--- |
| **VDD** | **3.3V** | Đỏ | Nguồn cấp 3.3V sạch (tránh chung nguồn công suất loa) |
| **GND** | **GND** | Đen | Mass tín hiệu âm thanh |
| **SD** | **GPIO 6** | Vàng | Serial Data Out (dữ liệu âm thanh số 24-bit) |
| **WS** | **GPIO 4** | Xanh lá | Word Select / Left-Right Clock |
| **SCK** | **GPIO 5** | Cam | Continuous Serial Clock |
| **L/R** | **GND** | Đen | Nối GND để chọn kênh Trái (Left Channel) |

---

### 2.3. Module Khuếch Đại Âm Thanh I2S & Loa (MAX98357A + Loa 3W)
Mạch khuếch đại Class-D hiệu suất cao, không cần DAC rời, đánh trực tiếp loa 3W âm thanh ấm áp, rõ ràng:

| Chân Module MAX98357A | Chân ESP32-S3 / Nguồn | Màu Dây Gợi Ý | Chức Năng Kỹ Thuật |
| :--- | :---: | :---: | :--- |
| **VIN** | **5V (VBUS)** | Đỏ to | Lấy nguồn 5V trực tiếp từ cổng Type-C / mạch Boost để đạt công suất 3W |
| **GND** | **GND** | Đen to | Mass công suất âm thanh |
| **DIN** | **GPIO 7** | Vàng | Serial Data Input từ ESP32-S3 |
| **BCLK** | **GPIO 15** | Cam | Bit Clock âm thanh |
| **LRC** | **GPIO 16** | Xanh lá | Left-Right Clock |
| **GAIN** | **GND** | - | Nối GND cho mức khuếch đại 9dB (hoặc để trống = 12dB) |
| **SD_MODE** | **Không nối** | - | Tự động trộn kênh (Stereo mix to Mono) |
| **SPK+ / SPK-** | **2 cực Loa 4Ω 3W** | Đỏ / Đen | Hàn trực tiếp vào 2 cực của loa hộp trong buồng âm |

---

### 2.4. Cảm Biến Góc Nghiêng & Gia Tốc 6-DOF (MPU6050 I2C)
Nhận biết robot đang đứng yên, bị nhấc bổng, rung lắc hay xoay nghiêng:

| Chân MPU6050 | Chân ESP32-S3 | Màu Dây Gợi Ý | Chức Năng Kỹ Thuật |
| :--- | :---: | :---: | :--- |
| **VCC** | **3.3V** | Đỏ | Nguồn cảm biến |
| **GND** | **GND** | Đen | Mass chung |
| **SDA** | **GPIO 8** | Xanh lá | I2C Data (kèm điện trở kéo lên 4.7kΩ nội) |
| **SCL** | **GPIO 9** | Vàng | I2C Clock |
| **AD0** | **GND** | - | Địa chỉ I2C mặc định `0x68` |

---

### 2.5. Cảm Ứng Chạm Đỉnh Đầu & Phím Cứng (Touch & Buttons)
| Linh Kiện | Chân ESP32-S3 | Chức Năng |
| :--- | :---: | :--- |
| **Miếng cảm ứng điện dung** | **GPIO 2** | Vuốt / chạm đỉnh đầu robot để tương tác cảm xúc |
| **Nút BOOT / Talk** | **GPIO 0** | Bấm giữ để nói chuyện trực tiếp / xác nhận BLE pairing |
| **Nút Menu / Phụ** | **GPIO 47** | Mở menu cài đặt nhanh, đổi chế độ |
| **Đèn LED RGB WS2812** | **GPIO 48** | Đèn trạng thái nhiều màu tích hợp trên bo |

---

## 3. Quy Tắc Đi Dây & Chống Nhiễu Thực Tế (Engineering Best Practices)

1. **Tách mass tín hiệu & mass công suất (Star Grounding):**
   - Chân GND của micro INMP441 và GC9A01 nối về mass sạch của ESP32.
   - Chân GND của module MAX98357A nối thẳng về chân GND cấp nguồn nguồn chính (Type-C / Pin), tránh dòng loa chạy qua làm rung mass micro gây tiếng rè "hum/buzz".
2. **Chiều dài dây ngắn tối ưu:**
   - Cáp SPI màn hình GC9A01 $\le 50\text{ mm}$ để xung 40MHz không bị biến dạng dạng sóng.
   - Bện xoắn nhẹ các cặp dây tín hiệu I2S (SCK/WS/SD) để triệt tiêu nhiễu chéo (cross-talk).
3. **Cách âm buồng loa (Acoustic Isolation):**
   - Khoang loa phải được bọc mút xốp EVA kín khít. Không để khe hở giữa mặt trước loa và micro, tránh phản xạ âm thanh từ loa lọt ngược vào micro gây hiện tượng hú và ngắt lời sai (False Barge-in).

---

## 4. Kiểm Tra Sau Khi Đi Dây (Checklist Trước Khi Cắm Điện)

- [ ] Đo thông mạch kiểm tra **VCC (3.3V) và 5V KHÔNG bị chập với GND**.
- [ ] Kiểm tra chân L/R của INMP441 đã nối đúng GND (chọn kênh trái).
- [ ] Kiểm tra cực tính của loa SPK+ và SPK- không bị chạm vào khung kim loại.
- [ ] Cắm cổng USB nạp lệnh test phần cứng:
  ```bash
  DEVELOPER_DIR=/Library/Developer/CommandLineTools ./test_host.sh
  ```
