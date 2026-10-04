# 🛠️ Rody S3 Round Edition (Astro-Pod) - Hướng Dẫn Gia Công & Lắp Ráp Hoàn Thiện

> **Mã thiết kế:** `RODY-S3-ENC-V1`  
> **Áp dụng cho:** Phiên bản màn hình tròn GC9A01 1.28" (240x240 SPI) + ESP32-S3 + Vỏ cầu vát nghiêng $65^\circ$ Astro-Pod.  
> **Độ khó:** Trung bình (yêu cầu kỹ năng hàn thiếc cơ bản và thao tác lắp ráp cẩn thận).  

---

## 1. Danh Mục Dụng Cụ & Vật Tư Yêu Cầu

### 1.1. Các Chi Tiết Cơ Khí In 3D (Xuất từ `firmware_muse/cad/rody_s3_astropod.scad`)
| Chi Tiết | File STL | Vật Liệu Đề Xuất | Số Lượng |
| :--- | :--- | :--- | :--- |
| **Viền Màn Hình (Front Bezel)** | `front_bezel.stl` | Nhựa Resin 8K hoặc PLA+ Space Gray | 1 |
| **Thân Cầu Chính (Main Shell)** | `main_shell.stl` | PLA+ / PETG Matte Ceramic White | 1 |
| **Đế Âm Học (Acoustic Base)** | `acoustic_base.stl` | ABS / PETG Dark Charcoal (Infill 100%) | 1 |
| **Đôi Tai Mecha (Modular Ears)** | `modular_ears.stl` | TPU mềm 85A hoặc Silicone Pastel Mint | 1 cặp |

### 1.2. Phụ Kiện Cơ Khí & Tiêu Hao
- **Mặt kính bảo vệ 2.5D:** Mica/Acrylic tròn $\varnothing 36.0\text{ mm} \times 1.5\text{ mm}$ (1 cái).
- **Vít inox tự ren đầu chìm M2 $\times 5\text{ mm}$:** 4 con bắt nắp đáy, 3 con giữ bezel trước, 2 con giữ bo mạch.
- **Nam châm vĩnh cửu Neodymium N52:** $\varnothing 6.0\text{ mm} \times 2.0\text{ mm}$ (4 viên: 2 viên trong thân, 2 viên trong tai).
- **Vòng đệm O-ring chống trượt chân đế:** Cao su silicone $\varnothing 42\text{ mm} \times 2.5\text{ mm}$ (1 sợi).
- **Đệm xốp EVA kín âm:** Băng keo xốp EVA $1.0\text{ mm}$ dán viền loa 28mm (1 đoạn).
- **Lá nhôm / đồng cảm ứng điện dung:** Kích thước $15\text{ mm} \times 15\text{ mm}$ (1 miếng).
- **Keo dán chuyên dụng:** Keo B-7000 (dán màn hình, mica) + Keo CA / 502 định vị nam châm.

### 1.3. Linh Kiện Điện Tử Đã Kiểm Thử
- Bo mạch điều khiển ESP32-S3 DevKitC-1 (hoặc Bread S3 Mini).
- Màn hình tròn 1.28 inch IPS LCD GC9A01 SPI (240x240).
- Module micro I2S INMP441 (Omnidirectional).
- Module khuếch đại âm thanh I2S MAX98357A Mono 3W.
- Loa từ tính $28\text{ mm}\ 4\Omega\ 3\text{W}$ (màng cao su âm trầm).
- Cảm biến gia tốc & con quay hồi chuyển 6-DOF MPU6050.

---

## 2. Bảng Chiều Dài Dây Dẫn Chuẩn (Wire Length Schedule)

Do không gian trong quả cầu $\varnothing 72\text{ mm}$ rất gọn gàng và bo mạch đặt thẳng đứng trên khung xương, việc cắt dây đúng độ dài là **bắt buộc** để tránh cuộn dây gây nhiễu điện từ (EMI) hoặc cấn khung:

| Tuyến Tín Hiệu | Số Sợi | Chiều Dài Cắt | Kiểu Đi Dây | Ghi Chú Kỹ Thuật |
| :--- | :---: | :---: | :--- | :--- |
| **GC9A01 SPI Bus** | 8 sợi | **$48\text{ mm} \pm 2\text{ mm}$** | Cáp ribbon dán phẳng | SCLK, MOSI, DC, RST, CS, BL, 3V3, GND. Dây ngắn tránh suy hao tần số cao 40MHz. |
| **INMP441 I2S Mic** | 5 sợi | **$55\text{ mm} \pm 3\text{ mm}$** | Bện xoắn nhẹ (twisted) | WS, SCK, SD, 3V3, GND. L/R nối mass (GND) để chọn kênh Trái. |
| **MAX98357A & Loa** | 5 sợi + 2 | **$42\text{ mm} \pm 2\text{ mm}$** | Bện cặp nguồn riêng | BCLK, LRC, DIN từ ESP32; VIN lấy nguồn 5V USB để loa đánh đủ công suất 3W. |
| **MPU6050 I2C Bus** | 4 sợi | **$35\text{ mm} \pm 2\text{ mm}$** | Bó 4 sợi dẹt | SDA (GPIO 8), SCL (GPIO 9), 3V3, GND. |
| **Capacitive Touch** | 1 sợi | **$38\text{ mm} \pm 2\text{ mm}$** | Dây đơn mềm 28AWG | Nối từ GPIO 2 đến miếng lá nhôm dán trần đỉnh đầu. |

---

## 3. Quy Trình Thi Công & Lắp Ráp Từng Bước (6 Giai Đoạn)

```
[Phase 1: Xử lý vỏ in 3D] ───> [Phase 2: Lắp cụm Bezel & Màn hình]
                                             │
[Phase 3: Lắp buồng loa đáy] <───────────────┘
         │
         ▼
[Phase 4: Hàn dây & Cố định ESP32 vào Spine]
         │
         ▼
[Phase 5: Khép kín thân & Siết ốc đáy] ───> [Phase 6: Gắn tai nam châm & Test]
```

### Phase 1: Xử Lý Vỏ In 3D & Định Vị Nam Châm N52
1. Dùng dao gọt bavia (deburring tool) làm sạch các đường viền gờ của cả 3 chi tiết vỏ.
2. Dùng mũi khoan $\varnothing 1.8\text{ mm}$ xoay nhẹ tay để thông sạch các lỗ bắt ốc tự ren M2.
3. **Cực nam châm:** Lấy 2 viên nam châm N52 gắn vào 2 hốc ở đỉnh đầu thân vỏ, nhỏ 1 giọt keo CA. Đánh dấu mặt cực từ để đảm bảo 2 tai mèo gắn vào hút chặt (không bị đẩy ngược).

### Phase 2: Lắp Ráp Cụm Màn Hình Tròn GC9A01 & Micro
1. Đặt mặt kính acrylic 2.5D vào rãnh trước của `front_bezel.stl`, chấm nhẹ keo B-7000 quanh mép viền (chờ 10 phút cho keo se mặt).
2. Dán vòng đệm mút mỏng hoặc bôi 1 lớp keo viền quanh mép ngoài màn hình tròn GC9A01 để chống bụi và chống phản xạ sáng.
3. Đặt bo mạch GC9A01 vào hốc $\varnothing 38.2\text{ mm}$, căn chỉnh chân cáp phẳng hướng xuống dưới.
4. Đặt module micro INMP441 vào gờ dưới viền, căn chỉnh lỗ thu âm của chip hướng thẳng vào ống dẫn âm $\varnothing 1.5\text{ mm}$ nghiêng $45^\circ$. Bơm 1 chấm keo silicon để bịt kín xung quanh chân mic (tránh âm thanh loa lọt vào mic gây phản xạ hú - echo).

### Phase 3: Lắp Ráp Buồng Loa Kín & Cảm Biến Góc Nghiêng (Acoustic Base)
1. Dán dải xốp EVA $1.0\text{ mm}$ xung quanh vành loa $28\text{ mm}$.
2. Nhấn chặt loa vào khoang buồng âm của `acoustic_base.stl`. Khoang buồng âm phải tuyệt đối kín khí (Acoustic Suspension) để triệt tiêu hiện tượng đoản mạch âm (Acoustic Short Circuit), giúp dải âm trầm của robot sâu và rõ tiếng.
3. Đặt module MPU6050 vào khay trung tâm của đế, cố định bằng 1 giọt keo dán dẻo hoặc vít M2. Căn trục X/Y song song mặt phẳng bàn.
4. Lắp vòng đệm cao su O-ring $\varnothing 42\text{ mm}$ vào rãnh tròn dưới chân đế.

### Phase 4: Đấu Nối Dây & Cố Định Bo Mạch ESP32-S3
1. Cắt và tuốt đầu dây theo đúng bảng **Wire Length Schedule**.
2. Hàn các đầu dây vào các chân header của ESP32-S3 theo sơ đồ pinout:
   - **SPI Màn hình:** SCLK=42, MOSI=41, DC=40, RST=39, CS=38, BL=21.
   - **I2S Âm thanh:** Mic (WS=4, SCK=5, SD=6), Amp Loa (BCLK=15, LRC=16, DIN=7).
   - **I2C & Chạm:** I2C (SDA=8, SCL=9), Cảm biến chạm (GPIO 2).
3. Trượt bo mạch ESP32-S3 dọc theo hai rãnh ray của khung xương (`vertical spine`) bên trong `main_shell.stl`.
4. Dán miếng lá nhôm cảm ứng điện dung vào hõm âm trần ở đỉnh đầu robot, hàn dây nối vào GPIO 2.

### Phase 5: Hợp Nhất Thân Vỏ & Siết Ốc Khép Kín
1. Đưa cụm `front_bezel.stl` vào hốc nghiêng $65^\circ$ trên mặt trước thân vỏ, siết 3 vít M2 đầu chìm.
2. Gấp nhẹ các bó dây theo chiều dọc, không để dây đè lên tản nhiệt chip ESP32-S3.
3. Đưa nắp đáy `acoustic_base.stl` ăn khớp vào ngàm âm dương ở đáy thân vỏ.
4. Siết 4 con vít M2 $\times 5\text{ mm}$ từ phía dưới mặt đáy để cố định toàn bộ kết cấu robot.

### Phase 6: Hoàn Thiện Tai Mèo Mecha & Kiểm Tra
1. Dán 2 viên nam châm N52 còn lại vào đáy 2 tai mecha bằng keo CA (chú ý hút đúng chiều cực từ).
2. Hít 2 tai vào đỉnh đầu robot. Tai có thể xoay đổi góc hoặc tháo rời tùy ý.

---

## 4. Kiểm Thử Xuất Xưởng (Factory Checkout)

1. **Cắm nguồn Type-C:**
   - Quan sát dòng tiêu thụ qua đồng hồ USB-C: Idle $\approx 95\text{ mA} - 120\text{ mA}$ (ở 5V).
2. **Kiểm tra Màn hình GC9A01:**
   - Màn hình khởi động logo Rody S3 tròn trịa, viền không bị cắt góc, vòng tiến trình xoay mượt mà 30 FPS.
3. **Kiểm tra Âm thanh & VAD:**
   - Thử nói: *"Rody ơi"*, vòng tròn chuyển sang trạng thái lắng nghe (Xanh ngọc).
   - Phát âm thanh phản hồi: Loa 28mm âm lượng to, ấm, không bị rè méo ở mức 80% volume.
4. **Kiểm tra Cảm biến:**
   - Chạm tay lên đỉnh đầu (giữa 2 tai): Màn hình đổi biểu cảm cảm xúc (vui vẻ / chớp mắt).
   - Nghiêng / lắc robot: MPU6050 nhận diện góc nghiêng và trọng lực tức thì.

---

*Chúc mừng bạn đã hoàn thành chế tạo thành công Robot Trí Tuệ Nhân Tạo Rody S3 Round Edition!*
