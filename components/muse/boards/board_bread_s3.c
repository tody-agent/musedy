/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*
 * Rody S3 Round Pet (ESP32-S3 N16R8):
 * - Round 1.28" 240x240 GC9A01 SPI IPS LCD (Full RGB565 color with circular bezel ring)
 * - Backlight PWM on GPIO21 (LEDC smooth dimming)
 * - Micro INMP441 (I2S0 RX) and Ampli MAX98357A (I2S1 TX) simplex audio (no codec needed)
 * - Pet Head Touch sensor on GPIO2 (capacitive pad with multi-cycle glitch filter)
 * - MPU6050 Motion / Shake / Fall IMU on I2C (SDA=8, SCL=9)
 * - Buttons: BOOT (GPIO0 Talk) and GPIO47 (Aux/Menu)
 * - Onboard RGB LED WS2812 on GPIO48
 */

#include <math.h>
#include <string.h>
#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "driver/i2s_std.h"
#include "driver/ledc.h"
#include "driver/spi_master.h"
#include "esp_check.h"
#include "esp_heap_caps.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"
#include "esp_log.h"
#include "esp_lv_adapter.h"
#include "esp_sleep.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_lcd_panel_gc9a01.h"
#include "esp_lcd_panel_st7735.h"
#include "muse_audio.h"
#include "muse_board.h"
#include "muse_mem.h"
#include "muse_state.h"

static const char *TAG = "board";

#define LCD_RES 240

#if defined(CONFIG_MUSE_DISPLAY_GC9A01_ROUND)
#define LCD_WIDTH 240
#define LCD_HEIGHT 240
#define LCD_IS_ROUND true
#define LCD_DIAGONAL 1.28f
#define BOARD_NAME "Musedy S3 Round Pet"
#define LCD_TALK_HINT_ALIGN LV_ALIGN_BOTTOM_RIGHT
#define LCD_TALK_HINT_X -12
#define LCD_TALK_HINT_Y -12
#define LCD_AUX_HINT_ALIGN LV_ALIGN_BOTTOM_LEFT
#define LCD_AUX_HINT_X 12
#define LCD_AUX_HINT_Y -12
#else
// Default: 1.8" 160x128 Landscape ST7735/ST7789 (Retro Computer Edition)
#define LCD_WIDTH 160
#define LCD_HEIGHT 128
#define LCD_IS_ROUND false
#define LCD_DIAGONAL 1.8f
#define BOARD_NAME "Musedy S3 Retro Computer (1.8\" Landscape)"
#define LCD_TALK_HINT_ALIGN LV_ALIGN_BOTTOM_RIGHT
#define LCD_TALK_HINT_X -6
#define LCD_TALK_HINT_Y -4
#define LCD_AUX_HINT_ALIGN LV_ALIGN_BOTTOM_LEFT
#define LCD_AUX_HINT_X 6
#define LCD_AUX_HINT_Y -4
#endif

#define LCD_HOST SPI2_HOST
#define LCD_SCLK GPIO_NUM_42
#define LCD_MOSI GPIO_NUM_41
#define LCD_DC GPIO_NUM_40
#define LCD_RST GPIO_NUM_39
#define LCD_CS GPIO_NUM_38
#define LCD_BL GPIO_NUM_21
#define DRAW_BUF_LINES 32

#define I2C_SDA GPIO_NUM_8
#define I2C_SCL GPIO_NUM_9
#define MPU6050_ADDR 0x68

#define MIC_WS GPIO_NUM_4
#define MIC_SCK GPIO_NUM_5
#define MIC_DIN GPIO_NUM_6
#define SPK_DOUT GPIO_NUM_7
#define SPK_BCLK GPIO_NUM_15
#define SPK_LRCK GPIO_NUM_16
#define MIC_SHIFT 12               /* 24-bit INMP441 MSB in 32-bit slot -> 16-bit PCM */
#define MIC_GAIN_OFFSET_DB 30      /* Muse default 30 dB = unity gain (x1) */

#define TALK_GPIO GPIO_NUM_0       /* BOOT button */
#define AUX_GPIO GPIO_NUM_47       /* Auxiliary / Menu button */
#define TOUCH_GPIO GPIO_NUM_2      /* Pet Head Touch Sensor (TTP223 / Capacitive Pad) */

static i2c_master_bus_handle_t s_i2c;
static esp_lcd_panel_io_handle_t s_io;
static esp_lcd_panel_handle_t s_panel;
static muse_gpio_button_t s_talk, s_aux;
static i2s_chan_handle_t s_rx, s_tx;
static bool s_mic_on;
static bool s_spk_on;
static int s_mic_gain_q8 = 256;
static bool s_has_imu = false;
static i2c_master_dev_handle_t s_mpu = NULL;
static bool s_touch_was_pressed = false;
static int64_t s_last_imu_poll_us = 0;

/* ---------- Hardware & Peripherals Init ---------- */
static esp_err_t init(void)
{
    // Dedicated I2C bus on GPIO8/9 for MPU6050 IMU
    const i2c_master_bus_config_t i2c_cfg = {
        .i2c_port = I2C_NUM_0,
        .sda_io_num = I2C_SDA,
        .scl_io_num = I2C_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    ESP_RETURN_ON_ERROR(i2c_new_master_bus(&i2c_cfg, &s_i2c), TAG, "i2c bus init failed");

    // Buttons
    ESP_RETURN_ON_ERROR(muse_gpio_button_init(&s_talk, TALK_GPIO), TAG, "talk button init failed");
    ESP_RETURN_ON_ERROR(muse_gpio_button_init(&s_aux, AUX_GPIO), TAG, "aux button init failed");
    s_talk.pressed = (gpio_get_level(TALK_GPIO) == 0);
    s_aux.pressed = (gpio_get_level(AUX_GPIO) == 0);

    // Pet Head Touch Sensor (GPIO 2, active high)
    gpio_config_t touch_cfg = {
        .pin_bit_mask = (1ULL << TOUCH_GPIO),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&touch_cfg);

    // Check optional MPU6050 on I2C
    i2c_device_config_t mpu_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = MPU6050_ADDR,
        .scl_speed_hz = 400000,
    };
    if (i2c_master_bus_add_device(s_i2c, &mpu_cfg, &s_mpu) == ESP_OK) {
        uint8_t who_am_i_reg = 0x75;
        uint8_t who_am_i_val = 0;
        if (i2c_master_transmit_receive(s_mpu, &who_am_i_reg, 1, &who_am_i_val, 1, 50) == ESP_OK &&
            (who_am_i_val == 0x68 || who_am_i_val == 0x70 || who_am_i_val == 0x71)) {
            // Wake MPU6050 up (write 0x00 to PWR_MGMT_1 register 0x6B)
            uint8_t wake_cmd[2] = { 0x6B, 0x00 };
            i2c_master_transmit(s_mpu, wake_cmd, 2, 50);
            s_has_imu = true;
            ESP_LOGI(TAG, "🐾 Pet IMU detected (WHO_AM_I=0x%02X) on SDA=8, SCL=9 - Motion reflexes enabled", who_am_i_val);
        } else {
            i2c_master_bus_rm_device(s_mpu);
            s_mpu = NULL;
        }
    }

    ESP_LOGI(TAG, "Rody S3 Round Pet hardware initialized (GC9A01 240x240 SPI, INMP441, MAX98357A, Touch GPIO2)");
    return ESP_OK;
}

/* ---------- Display Init: GC9A01 240x240 Round SPI ---------- */
static lv_display_t *display_start(lv_indev_t **touch)
{
    if (touch) *touch = NULL;

    // 1. Backlight PWM (LEDC) on LCD_BL (GPIO 21)
    const ledc_timer_config_t bl_timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_10_BIT,
        .timer_num = LEDC_TIMER_0,
        .freq_hz = 20000,
        .clk_cfg = LEDC_AUTO_CLK,
    };
    const ledc_channel_config_t bl_ch = {
        .gpio_num = LCD_BL,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_0,
        .timer_sel = LEDC_TIMER_0,
        .duty = 0,
    };
    if (ledc_timer_config(&bl_timer) == ESP_OK && ledc_channel_config(&bl_ch) == ESP_OK) {
        ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, 1023); // Full brightness initially
        ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
    }

    // 2. SPI Bus Init (SPI2_HOST, 40MHz DMA)
    const spi_bus_config_t bus_cfg = {
        .sclk_io_num = LCD_SCLK,
        .mosi_io_num = LCD_MOSI,
        .miso_io_num = GPIO_NUM_NC,
        .quadwp_io_num = GPIO_NUM_NC,
        .quadhd_io_num = GPIO_NUM_NC,
        .max_transfer_sz = LCD_WIDTH * DRAW_BUF_LINES * sizeof(uint16_t),
    };
    if (spi_bus_initialize(LCD_HOST, &bus_cfg, SPI_DMA_CH_AUTO) != ESP_OK) {
        ESP_LOGE(TAG, "spi_bus_initialize failed");
        return NULL;
    }

    // 3. Panel IO SPI Init
    const esp_lcd_panel_io_spi_config_t io_cfg = {
        .cs_gpio_num = LCD_CS,
        .dc_gpio_num = LCD_DC,
        .spi_mode = 0,
        .pclk_hz = 40 * 1000 * 1000, // 40 MHz SPI PCLK
        .trans_queue_depth = 10,
        .lcd_cmd_bits = 8,
        .lcd_param_bits = 8,
    };
    if (esp_lcd_new_panel_io_spi(LCD_HOST, &io_cfg, &s_io) != ESP_OK) {
        ESP_LOGE(TAG, "esp_lcd_new_panel_io_spi failed");
        return NULL;
    }

#if defined(CONFIG_MUSE_DISPLAY_GC9A01_ROUND)
    // 4. Panel GC9A01 Init (240x240 Round)
    const esp_lcd_panel_dev_config_t panel_cfg = {
        .reset_gpio_num = LCD_RST,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_BGR,
        .bits_per_pixel = 16,
    };
    if (esp_lcd_new_panel_gc9a01(s_io, &panel_cfg, &s_panel) != ESP_OK) {
        ESP_LOGE(TAG, "esp_lcd_new_panel_gc9a01 failed");
        return NULL;
    }

    esp_lcd_panel_reset(s_panel);
    esp_lcd_panel_init(s_panel);
    esp_lcd_panel_invert_color(s_panel, true);
    esp_lcd_panel_disp_on_off(s_panel, true);
#else
    // 4. Panel ST7735 1.8" 128x160 Landscape Init
    const esp_lcd_panel_dev_config_t panel_cfg = {
        .reset_gpio_num = LCD_RST,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel = 16,
    };
    if (esp_lcd_new_panel_st7735(s_io, &panel_cfg, &s_panel) != ESP_OK) {
        ESP_LOGE(TAG, "esp_lcd_new_panel_st7735 failed");
        return NULL;
    }

    esp_lcd_panel_reset(s_panel);
    esp_lcd_panel_init(s_panel);
#if defined(CONFIG_MUSE_DISPLAY_INVERT) && CONFIG_MUSE_DISPLAY_INVERT
    esp_lcd_panel_invert_color(s_panel, true);
#else
    esp_lcd_panel_invert_color(s_panel, false);
#endif
    // Set landscape orientation: swap XY and mirror row/col
    esp_lcd_panel_swap_xy(s_panel, true);
    esp_lcd_panel_mirror(s_panel, false, true);

#if defined(CONFIG_MUSE_DISPLAY_ST7735_X_GAP) && defined(CONFIG_MUSE_DISPLAY_ST7735_Y_GAP)
    esp_lcd_panel_set_gap(s_panel, CONFIG_MUSE_DISPLAY_ST7735_X_GAP, CONFIG_MUSE_DISPLAY_ST7735_Y_GAP);
#else
    esp_lcd_panel_set_gap(s_panel, 0, 0);
#endif
    esp_lcd_panel_disp_on_off(s_panel, true);
#endif

    // 5. Register with esp_lv_adapter (Native RGB565 full-color rendering)
    esp_lv_adapter_config_t adapter_cfg = ESP_LV_ADAPTER_DEFAULT_CONFIG();
    adapter_cfg.task_core_id = MUSE_UI_CORE;
    adapter_cfg.task_priority = MUSE_UI_PRIORITY;
    if (esp_lv_adapter_init(&adapter_cfg) != ESP_OK) {
        ESP_LOGE(TAG, "esp_lv_adapter_init failed");
        return NULL;
    }

    const esp_lv_adapter_display_config_t disp_cfg = {
        .panel = s_panel,
        .panel_io = s_io,
        .profile = {
            .interface = ESP_LV_ADAPTER_PANEL_IF_OTHER,
            .rotation = ESP_LV_ADAPTER_ROTATE_0,
            .hor_res = LCD_WIDTH,
            .ver_res = LCD_HEIGHT,
            .buffer_height = DRAW_BUF_LINES,
            .use_psram = false,
            .require_double_buffer = true,
        },
        .tear_avoid_mode = ESP_LV_ADAPTER_TEAR_AVOID_MODE_NONE,
    };
    lv_display_t *disp = esp_lv_adapter_register_display(&disp_cfg);
    if (!disp || esp_lv_adapter_start() != ESP_OK) {
        ESP_LOGE(TAG, "esp_lv_adapter_start failed");
        return NULL;
    }
    ESP_LOGI(TAG, "%s display started with LVGL 9 (%dx%d RGB565)",
             BOARD_NAME, LCD_WIDTH, LCD_HEIGHT);
    return disp;
}

static bool display_lock(int timeout_ms)
{
    return esp_lv_adapter_lock(timeout_ms) == ESP_OK;
}

static void set_brightness(int pct)
{
    if (pct <= 0) {
        ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, 0);
        ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
        esp_lcd_panel_disp_on_off(s_panel, false);
        return;
    }
    uint32_t duty = (uint32_t)(pct * 1023 / 100);
    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, duty);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
    esp_lcd_panel_disp_on_off(s_panel, true);
}

static void panel_sleep(bool sleep)
{
    if (sleep) {
        set_brightness(0);
        esp_lcd_panel_disp_sleep(s_panel, true);
    } else {
        esp_lcd_panel_disp_sleep(s_panel, false);
        set_brightness(100);
    }
}

/* ---------- Audio: INMP441 on I2S0 RX, MAX98357A on I2S1 TX ---------- */
static int mic_enable(const audio_codec_data_if_t *h, esp_codec_dev_type_t t, bool on)
{
    (void)h; (void)t;
    if (on != s_mic_on) {
        if ((on ? i2s_channel_enable(s_rx) : i2s_channel_disable(s_rx)) != ESP_OK) {
            return ESP_CODEC_DEV_DRV_ERR;
        }
        s_mic_on = on;
    }
    return ESP_CODEC_DEV_OK;
}

static int mic_read(const audio_codec_data_if_t *h, uint8_t *data, int size)
{
    (void)h;
    static int32_t raw[256];
    int16_t *out = (int16_t *)data;
    for (int left = size / 2; left > 0;) {
        int n = left > 256 ? 256 : left;
        size_t got;
        if (i2s_channel_read(s_rx, raw, n * 4, &got, pdMS_TO_TICKS(1000)) != ESP_OK || got != (size_t)n * 4) {
            return ESP_CODEC_DEV_READ_FAIL;
        }
        for (int i = 0; i < n; i++) {
            int v = (raw[i] >> MIC_SHIFT) * s_mic_gain_q8 >> 8;
            *out++ = v > INT16_MAX ? INT16_MAX : v < INT16_MIN ? INT16_MIN : v;
        }
        left -= n;
    }
    return ESP_CODEC_DEV_OK;
}

static void set_mic_gain(esp_codec_dev_handle_t mic, int db)
{
    (void)mic;
    s_mic_gain_q8 = (int)(256.0f * powf(10.0f, (db - MIC_GAIN_OFFSET_DB) / 20.0f));
}

static int spk_enable(const audio_codec_data_if_t *h, esp_codec_dev_type_t t, bool on)
{
    (void)h; (void)t;
    if (on != s_spk_on) {
        if (s_tx) {
            esp_err_t err = on ? i2s_channel_enable(s_tx) : i2s_channel_disable(s_tx);
            if (err != ESP_OK) {
                return ESP_CODEC_DEV_DRV_ERR;
            }
        }
        s_spk_on = on;
    }
    return ESP_CODEC_DEV_OK;
}

static int spk_write(const audio_codec_data_if_t *h, uint8_t *data, int size)
{
    (void)h;
    if (!s_tx) {
        return ESP_CODEC_DEV_WRITE_FAIL;
    }
    if (!s_spk_on) {
        i2s_channel_enable(s_tx);
        s_spk_on = true;
    }
    size_t wrote;
    return (i2s_channel_write(s_tx, data, size, &wrote, pdMS_TO_TICKS(1000)) == ESP_OK)
               ? ESP_CODEC_DEV_OK
               : ESP_CODEC_DEV_WRITE_FAIL;
}

static esp_err_t audio_init(esp_codec_dev_handle_t *spk, esp_codec_dev_handle_t *mic)
{
    // I2S0: INMP441 Microphone RX
    i2s_chan_config_t rx_chan = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    ESP_RETURN_ON_ERROR(i2s_new_channel(&rx_chan, NULL, &s_rx), TAG, "mic channel creation failed");
    const i2s_std_config_t rx_cfg = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(MUSE_AUDIO_RATE),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_STEREO),
        .gpio_cfg = {
            .mclk = I2S_GPIO_UNUSED,
            .bclk = MIC_SCK,
            .ws = MIC_WS,
            .dout = I2S_GPIO_UNUSED,
            .din = MIC_DIN,
        },
    };
    ESP_RETURN_ON_ERROR(i2s_channel_init_std_mode(s_rx, &rx_cfg), TAG, "mic i2s init failed");

    // I2S1: MAX98357A Speaker TX
    i2s_chan_config_t tx_chan = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_1, I2S_ROLE_MASTER);
    tx_chan.auto_clear = true;
    ESP_RETURN_ON_ERROR(i2s_new_channel(&tx_chan, &s_tx, NULL), TAG, "spk channel creation failed");
    const i2s_std_config_t tx_cfg = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(MUSE_AUDIO_RATE),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_STEREO),
        .gpio_cfg = {
            .mclk = I2S_GPIO_UNUSED,
            .bclk = SPK_BCLK,
            .ws = SPK_LRCK,
            .dout = SPK_DOUT,
            .din = I2S_GPIO_UNUSED,
        },
    };
    ESP_RETURN_ON_ERROR(i2s_channel_init_std_mode(s_tx, &tx_cfg), TAG, "spk i2s init failed");
    ESP_RETURN_ON_ERROR(i2s_channel_enable(s_tx), TAG, "spk channel enable failed");
    s_spk_on = true;

    static const audio_codec_data_if_t spk_if = { .enable = spk_enable, .write = spk_write };
    static const audio_codec_data_if_t mic_if = { .enable = mic_enable, .read = mic_read };
    esp_codec_dev_cfg_t out_cfg = { .dev_type = ESP_CODEC_DEV_TYPE_OUT, .data_if = &spk_if };
    esp_codec_dev_cfg_t in_cfg = { .dev_type = ESP_CODEC_DEV_TYPE_IN, .data_if = &mic_if };
    *spk = esp_codec_dev_new(&out_cfg);
    *mic = esp_codec_dev_new(&in_cfg);
    return (*spk && *mic) ? ESP_OK : ESP_FAIL;
}

/* ---------- Button & Pet Reflexes Polling ---------- */
static unsigned poll_buttons(void)
{
    unsigned edges = muse_gpio_button_poll(&s_talk) | (muse_gpio_button_poll(&s_aux) << 2);

    // 🐾 Pet Head Touch Polling (GPIO 2) with glitch-filtering debounce
    bool touch_raw = (gpio_get_level(TOUCH_GPIO) == 1);
    static uint8_t s_touch_debounce = 0;
    if (touch_raw) {
        if (s_touch_debounce < 255) s_touch_debounce++;
    } else {
        s_touch_debounce = 0;
    }
    bool touch_pressed = (s_touch_debounce >= 2);
    if (touch_pressed && !s_touch_was_pressed) {
        muse_state_make_happy();
        muse_state_poke();
        ESP_LOGI(TAG, "🐾 Pet head touched! Purring with happiness.");
    }
    s_touch_was_pressed = touch_pressed;

    // 🐾 Pet IMU Motion / Shake Check (every 100 ms with 500ms cooldown)
    int64_t now_us = esp_timer_get_time();
    static int64_t s_last_shake_poke_us = 0;
    if (s_has_imu && s_mpu && (now_us - s_last_imu_poll_us > 100000)) {
        s_last_imu_poll_us = now_us;
        uint8_t reg = 0x3B; // ACCEL_XOUT_H
        uint8_t buf[6];
        if (i2c_master_transmit_receive(s_mpu, &reg, 1, buf, 6, 20) == ESP_OK) {
            int16_t ax = (int16_t)((buf[0] << 8) | buf[1]);
            int16_t ay = (int16_t)((buf[2] << 8) | buf[3]);
            int16_t az = (int16_t)((buf[4] << 8) | buf[5]);
            float g_sq = ((float)ax * ax + (float)ay * ay + (float)az * az) / (16384.0f * 16384.0f);
            if (g_sq > 4.84f && (now_us - s_last_shake_poke_us > 500000)) { // Shaking (> 2.2g)
                s_last_shake_poke_us = now_us;
                muse_state_poke();
                ESP_LOGI(TAG, "🐾 Pet robot shaken! (%.1fg)", sqrtf(g_sq));
            } else if (g_sq < 0.16f && (now_us - s_last_shake_poke_us > 500000)) { // Free fall (< 0.4g)
                s_last_shake_poke_us = now_us;
                muse_state_poke();
                ESP_LOGW(TAG, "🐾 Pet robot free fall! (%.1fg)", sqrtf(g_sq));
            }
        }
    }

    return edges;
}

static void wait_buttons(int timeout_ms)
{
    muse_gpio_buttons_wait((muse_gpio_button_t *const[]){ &s_talk, &s_aux }, 2, timeout_ms);
}

/* ---------- Power Management ---------- */
static esp_err_t read_power(muse_power_t *out)
{
    out->usb = true;
    out->charging = false;
    out->battery_pct = -1;
    out->battery_mv = 0;
    return ESP_OK;
}

static esp_err_t power_off(void)
{
    panel_sleep(true);
    if (s_tx) {
        i2s_channel_disable(s_tx);
    }
    if (s_rx) {
        i2s_channel_disable(s_rx);
    }
    while (gpio_get_level(TALK_GPIO) == 0) {
        vTaskDelay(pdMS_TO_TICKS(20));
    }
    vTaskDelay(pdMS_TO_TICKS(50));
    ESP_RETURN_ON_ERROR(esp_sleep_enable_ext0_wakeup(TALK_GPIO, 0), TAG, "wake config failed");
    esp_deep_sleep_start();
    return ESP_FAIL;
}

/* ---------- Board Descriptor: 1.8" Landscape 160x128 / 1.28" Round GC9A01 ---------- */
static const muse_board_t s_board = {
    .name = BOARD_NAME,
    .width = LCD_WIDTH,
    .height = LCD_HEIGHT,
#if defined(CONFIG_MUSE_DISPLAY_GC9A01_ROUND)
    .round = true,              /* Native round layout with circular progress ring bezel */
    .diagonal_in = 1.28f,       /* 1.28 inch round screen */
#else
    .round = false,             /* 1.8" Landscape 160x128 rectangular CRT frame */
    .diagonal_in = 1.8f,        /* 1.8 inch landscape screen */
#endif
    .touch = false,
    .keyboard = false,
    .talk_button = "BOOT",
    .aux_button = "GPIO47",
    .talk_hint = { LCD_TALK_HINT_ALIGN, LCD_TALK_HINT_X, LCD_TALK_HINT_Y },
    .aux_hint = { LCD_AUX_HINT_ALIGN, LCD_AUX_HINT_X, LCD_AUX_HINT_Y },
    .frame_ms = 33,             /* 30 FPS smooth animation */
    .init = init,
    .display_start = display_start,
    .display_lock = display_lock,
    .display_unlock = esp_lv_adapter_unlock,
    .set_brightness = set_brightness,
    .panel_sleep = panel_sleep,
    .audio_init = audio_init,
    .mic_slot = 0,              /* INMP441 L/R to GND -> Left slot (0) */
    .set_mic_gain = set_mic_gain,
    .poll_buttons = poll_buttons,
    .wait_buttons = wait_buttons,
    .read_power = read_power,
    .power_off = power_off,
};

const muse_board_t *muse_board_get(void)
{
    return &s_board;
}
