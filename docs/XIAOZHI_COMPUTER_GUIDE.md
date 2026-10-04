# 🖥️ Rody S3 - Cẩm Nang Chuyển Đổi Vỏ Máy Tính Retro (Xiaozhi AI Computer Edition)

> **Mẫu thiết kế gốc:** MakerWorld Model [`#1967811` - 小智AI-电脑小智](https://makerworld.com/en/models/1967811-xiaozhi-ai-computer-xiaozhi#profileId-2115633) thiết kế bởi **董老爺 (Mr. Dong)**  
> **Phiên bản vỏ người dùng:** Thân vỏ Xanh Dương (Sky Blue / Classic Cobalt Blue) + Mặt Bezel Màn Hình Trắng Sữa (Off-White Vintage CRT)  
> **Thư mục chứa file in 3D:** [`firmware_muse/Computer/电脑小智_stls/`](file:///Volumes/Builder/Arduino/OtooRobot/firmware_muse/Computer/电脑小智_stls/)  
> **File phối cảnh render hoàn thiện:** [`firmware_muse/docs/designs/xiaozhi_computer_blue.png`](file:///Volumes/Builder/Arduino/OtooRobot/firmware_muse/docs/designs/xiaozhi_computer_blue.png)  

---

## 1. Phối Cảnh Sản Phẩm Hoàn Thiện (Concept Visual)

Thiết kế mô phỏng dòng máy tính cổ điển Macintosh / CRT Retro thu nhỏ với phong cách màu **Xanh Dương Pastel** kết hợp viền mặt trước **Trắng Sữa**, khe đút đĩa mềm (floppy drive slot), mắt camera, lỗ micro và 4 phím bấm chức năng màu tím ở đỉnh:

![Rody S3 Xiaozhi Computer Blue Edition](file:///Volumes/Builder/Arduino/OtooRobot/firmware_muse/docs/designs/xiaozhi_computer_blue.png)

---

## 2. Cấu Trúc Các Chi Tiết In 3D Đã Tải Về (`firmware_muse/Computer`)

Bộ file in trong thư mục `firmware_muse/Computer/电脑小智_stls` bao gồm 3 chi tiết chính:

| Tên File STL | Mô Tả & Kích Thước Hình Học | Màu Sắc / Chức Năng |
| :--- | :--- | :--- |
| **`obj_2_Object_1.stl`** | **Mặt Trước (Front Bezel):** $68.50 \times 77.75 \times 18.96\text{ mm}$. Khung cửa sổ màn hình $44.87 \times 44.47\text{ mm}$, hốc âm lùi phía sau $48.84 \times 48.33\text{ mm}$, lỗ camera $\varnothing 6.0\text{ mm}$, lỗ mic và khe đĩa mềm $28 \times 2.8\text{ mm}$. | Trắng sữa (Warm White / Vintage Cream) |
| **`obj_3_Object_4.stl`** | **Thân Máy Tính Sau (Main Blue Shell):** $68.50 \times 76.11 \times 44.33\text{ mm}$. Khoang chứa bo mạch ESP32-S3, khay pin LiPo, loa hộp và cổng Type-C bên hông. | Xanh Dương (Pastel Blue / Cobalt Blue) |
| **`obj_1_组合体.stl`** | **Cụm 4 Nút Bấm Đỉnh (Top Button Caps):** $46.45 \times 11.50 \times 10.00\text{ mm}$ (3 nút tròn $\varnothing 5.5\text{ mm}$ + 1 nút nguồn chữ nhật $9.5 \times 5.5\text{ mm}$). | Tím Retro / Xanh Navy |

---

## 3. Hai Phương Án Lắp Ráp Phần Cứng (Hardware Integration Options)

### Phương Án A (Khuyên Dùng): Tận Dụng Màn Hình Tròn GC9A01 1.28" (Phong Cách Màn Hình CRT Bo Cong Cổ Điển)
Nếu bạn đang có sẵn màn hình tròn **GC9A01 1.28" SPI (240x240)** đã được viết driver trong dự án:

1. **In thêm chi tiết chuyển đổi siêu nhỏ:**  
   Sử dụng file CAD [`firmware_muse/cad/xiaozhi_gc9a01_adapter.scad`](file:///Volumes/Builder/Arduino/OtooRobot/firmware_muse/cad/xiaozhi_gc9a01_adapter.scad) (in mất khoảng 15 phút, tốn ~5g nhựa):
   ```bash
   openscad -o firmware_muse/cad/stl/xiaozhi_gc9a01_adapter.stl -D '$fn=96' firmware_muse/cad/xiaozhi_gc9a01_adapter.scad
   ```
2. **Ngàm khớp hoàn hảo:** Tấm chuyển đổi có gờ $48.4 \times 48.0\text{ mm}$ đặt lọt khít vào rãnh ngàm của `obj_2_Object_1.stl`, tạo thành viền vát CRT giữ chặt màn hình tròn GC9A01 ở chính giữa mà không cần sửa vỏ xanh ngoài.
3. **Firmware:** Giữ nguyên cấu hình `CONFIG_MUSE_BOARD_BREAD_S3` (GC9A01 240x240 RGB565) đã được tối ưu mượt mà 30 FPS.

### Phương Án B: Sử Dụng Màn Hình Vuông / Chữ Nhật 2.0" ST7789 (Bộ Kit Xiaozhi Tiêu Chuẩn)
Nếu bạn sử dụng bo mạch tích hợp Xiaozhi kèm màn hình chữ nhật 2.0 inch (ST7789 240x320 hoặc 240x280) và camera FPC OV2640:
1. Màn hình 2.0" được lắp trực tiếp vào rãnh chữ nhật $48.84 \times 48.33\text{ mm}$ của `obj_2_Object_1.stl`.
2. Camera FPC cắm vào mắt tròn phía trên góc trái.
3. Loa hộp chữ nhật (cavity box speaker) dán băng keo 2 mặt vào đáy khoang sau của `obj_3_Object_4.stl`.

---

## 4. Sơ Đồ Đi Dây & Hàn Kết Nối Trong Vỏ Máy Tính

Không gian bên trong thân máy tính sau (`obj_3_Object_4.stl`) sâu $44.3\text{ mm}$ và rộng $68.5\text{ mm}$, rất thoải mái cho việc bố trí:

```
+-------------------------------------------------------+
|  [Top Buttons: Vol+, Vol-, Action, Wakeup/Power]     |
|                                                       |
|   +-----------------------+    +------------------+   |
|   |  Front Bezel (obj_2)  |    |  ESP32-S3 Board  |   |
|   |  - GC9A01 + Adapter   |    |  (Bread S3 /     |   |
|   |    (hoặc 2.0" ST7789) |<-->|   DevKitC)       |   |
|   |  - Mic INMP441        |    |                  |   |
|   |  - Camera (Tùy chọn)  |    +------------------+   |
|   +-----------------------+             |             |
|                                         v             |
|               +-----------------------------------+   |
|               |  MAX98357A Amp + Box Speaker      |   |
|               |  Pin LiPo 3.7V 800-1200mAh        |   |
|               +-----------------------------------+   |
+-------------------------------------------------------+
```

### Bảng Kết Nối Chân (Pinout Wiring)
- **Màn hình GC9A01 SPI:**
  - SCLK $\rightarrow$ GPIO 42
  - MOSI $\rightarrow$ GPIO 41
  - DC $\rightarrow$ GPIO 40
  - RST $\rightarrow$ GPIO 39
  - CS $\rightarrow$ GPIO 38
  - BL (Đèn nền PWM) $\rightarrow$ GPIO 21
  - VCC $\rightarrow$ 3.3V, GND $\rightarrow$ GND
- **Microphone I2S (INMP441):**
  - WS $\rightarrow$ GPIO 4, SCK $\rightarrow$ GPIO 5, SD $\rightarrow$ GPIO 6, L/R $\rightarrow$ GND
- **Khuếch đại âm thanh (MAX98357A):**
  - BCLK $\rightarrow$ GPIO 15, LRC $\rightarrow$ GPIO 16, DIN $\rightarrow$ GPIO 7, VIN $\rightarrow$ 5V (hoặc VBUS)
- **Nút bấm đỉnh (Top Buttons):**
  - Nút 1 (Action / Wakeup): GPIO 0 (BOOT) hoặc GPIO 2
  - Nút 2 (Vol -): GPIO 10
  - Nút 3 (Vol +): GPIO 11
  - Nút 4 (Chuyển chế độ / Mute): GPIO 12

---

## 5. Quy Trình Lắp Ráp Vào Bản In 3D Màu Xanh Dương

1. **Bước 1 (Lắp mặt kính & màn hình vào mặt trắng):**
   - Nếu dùng GC9A01: Nhỏ keo nhẹ gắn `xiaozhi_gc9a01_adapter` vào mặt trong của `obj_2_Object_1.stl`. Đặt màn hình GC9A01 và kính mica 2.5D vào tâm.
   - Nếu dùng ST7789 2.0": Đặt trực tiếp màn hình vào rãnh chữ nhật, cố định bằng 2 giọt keo B-7000.
2. **Bước 2 (Lắp nút bấm đỉnh):**
   - Đặt 4 nắp phím `obj_1_组合体.stl` vào 4 lỗ trên đỉnh vỏ xanh `obj_3_Object_4.stl`. Gắn thanh phím microswitch hoặc tact switch ngay bên dưới.
3. **Bước 3 (Cố định loa và pin):**
   - Đặt loa hộp xuống đáy vỏ xanh, hướng màng loa về các khe thoáng đáy để tiếng thoát ra ngoài tốt nhất.
   - Dán pin LiPo vào vách sau bằng keo xốp dán pin.
4. **Bước 4 (Cố định bo mạch & cắm sạc Type-C):**
   - Đặt ESP32-S3 sao cho cổng Type-C nằm thẳng hàng với khe khoét Type-C bên cạnh hông vỏ xanh.
5. **Bước 5 (Gập dây & khép nắp):**
   - Cắm cáp màn hình và mic từ mặt trước sang bo mạch.
   - Ghép mặt trước trắng `obj_2_Object_1.stl` vào thân xanh `obj_3_Object_4.stl`.
   - Vặn 4 vít định vị M2 để siết chặt toàn bộ khung máy tính.

---

*Robot Rody S3 trong diện mạo Máy Tính Cổ Điển Xiaozhi AI Xanh Dương của bạn đã sẵn sàng hoạt động!*
