/*
 * SPDX-FileCopyrightText: 2021-2024 Espressif Systems (Shanghai) CO LTD
 * SPDX-License-Identifier: Apache-2.0
 */

#include "esp_lcd_panel_st7735.h"

#include <stdlib.h>
#include <sys/cdefs.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_check.h"
#include "esp_log.h"
#include "driver/gpio.h"
#include "esp_lcd_panel_commands.h"
#include "esp_lcd_panel_interface.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"

static const char *TAG = "lcd_panel.st7735";

/* ST7735 specific command codes */
#define ST7735_CMD_FRMCTR1   0xB1
#define ST7735_CMD_FRMCTR2   0xB2
#define ST7735_CMD_FRMCTR3   0xB3
#define ST7735_CMD_INVCTR    0xB4
#define ST7735_CMD_PWCTR1    0xC0
#define ST7735_CMD_PWCTR2    0xC1
#define ST7735_CMD_PWCTR3    0xC2
#define ST7735_CMD_PWCTR4    0xC3
#define ST7735_CMD_PWCTR5    0xC4
#define ST7735_CMD_VMCTR1    0xC5
#define ST7735_CMD_GMCTRP1   0xE0
#define ST7735_CMD_GMCTRN1   0xE1

typedef struct {
    esp_lcd_panel_t base;
    esp_lcd_panel_io_handle_t io;
    int reset_gpio_num;
    bool reset_level;
    int x_gap;
    int y_gap;
    uint8_t madctl_val;
    uint8_t colmod_val;
} st7735_panel_t;

static esp_err_t panel_st7735_del(esp_lcd_panel_t *panel);
static esp_err_t panel_st7735_reset(esp_lcd_panel_t *panel);
static esp_err_t panel_st7735_init(esp_lcd_panel_t *panel);
static esp_err_t panel_st7735_draw_bitmap(esp_lcd_panel_t *panel, int x_start, int y_start, int x_end, int y_end, const void *color_data);
static esp_err_t panel_st7735_invert_color(esp_lcd_panel_t *panel, bool invert_color_data);
static esp_err_t panel_st7735_mirror(esp_lcd_panel_t *panel, bool mirror_x, bool mirror_y);
static esp_err_t panel_st7735_swap_xy(esp_lcd_panel_t *panel, bool swap_axes);
static esp_err_t panel_st7735_set_gap(esp_lcd_panel_t *panel, int x_gap, int y_gap);
static esp_err_t panel_st7735_disp_on_off(esp_lcd_panel_t *panel, bool on_off);
static esp_err_t panel_st7735_disp_sleep(esp_lcd_panel_t *panel, bool sleep);

esp_err_t esp_lcd_new_panel_st7735(const esp_lcd_panel_io_handle_t io,
                                   const esp_lcd_panel_dev_config_t *panel_dev_config,
                                   esp_lcd_panel_handle_t *ret_panel)
{
    esp_err_t ret = ESP_OK;
    st7735_panel_t *st7735 = NULL;
    ESP_GOTO_ON_FALSE(io && panel_dev_config && ret_panel, ESP_ERR_INVALID_ARG, err, TAG, "invalid argument");
    st7735 = calloc(1, sizeof(st7735_panel_t));
    ESP_GOTO_ON_FALSE(st7735, ESP_ERR_NO_MEM, err, TAG, "no mem for st7735 panel");

    if (panel_dev_config->reset_gpio_num >= 0) {
        gpio_config_t io_conf = {
            .mode = GPIO_MODE_OUTPUT,
            .pin_bit_mask = 1ULL << panel_dev_config->reset_gpio_num,
        };
        ESP_GOTO_ON_ERROR(gpio_config(&io_conf), err, TAG, "configure GPIO for RST line failed");
    }

    switch (panel_dev_config->rgb_ele_order) {
    case LCD_RGB_ELEMENT_ORDER_RGB:
        st7735->madctl_val = 0;
        break;
    case LCD_RGB_ELEMENT_ORDER_BGR:
        st7735->madctl_val |= LCD_CMD_BGR_BIT;
        break;
    default:
        ESP_GOTO_ON_FALSE(false, ESP_ERR_NOT_SUPPORTED, err, TAG, "unsupported RGB element order");
        break;
    }

    switch (panel_dev_config->bits_per_pixel) {
    case 16: // RGB565
        st7735->colmod_val = 0x55;
        break;
    case 18: // RGB666
        st7735->colmod_val = 0x66;
        break;
    default:
        ESP_GOTO_ON_FALSE(false, ESP_ERR_NOT_SUPPORTED, err, TAG, "unsupported pixel width");
        break;
    }

    st7735->io = io;
    st7735->reset_gpio_num = panel_dev_config->reset_gpio_num;
    st7735->reset_level = panel_dev_config->flags.reset_active_high;
    st7735->base.del = panel_st7735_del;
    st7735->base.reset = panel_st7735_reset;
    st7735->base.init = panel_st7735_init;
    st7735->base.draw_bitmap = panel_st7735_draw_bitmap;
    st7735->base.invert_color = panel_st7735_invert_color;
    st7735->base.set_gap = panel_st7735_set_gap;
    st7735->base.mirror = panel_st7735_mirror;
    st7735->base.swap_xy = panel_st7735_swap_xy;
    st7735->base.disp_on_off = panel_st7735_disp_on_off;
    st7735->base.disp_sleep = panel_st7735_disp_sleep;
    *ret_panel = &(st7735->base);
    ESP_LOGI(TAG, "new ST7735 1.8\" 128x160 panel @%p", st7735);
    return ESP_OK;

err:
    if (st7735) {
        if (panel_dev_config->reset_gpio_num >= 0) {
            gpio_reset_pin(panel_dev_config->reset_gpio_num);
        }
        free(st7735);
    }
    return ret;
}

static esp_err_t panel_st7735_del(esp_lcd_panel_t *panel)
{
    st7735_panel_t *st7735 = __containerof(panel, st7735_panel_t, base);
    if (st7735->reset_gpio_num >= 0) {
        gpio_reset_pin(st7735->reset_gpio_num);
    }
    free(st7735);
    return ESP_OK;
}

static esp_err_t panel_st7735_reset(esp_lcd_panel_t *panel)
{
    st7735_panel_t *st7735 = __containerof(panel, st7735_panel_t, base);
    esp_lcd_panel_io_handle_t io = st7735->io;

    if (st7735->reset_gpio_num >= 0) {
        gpio_set_level(st7735->reset_gpio_num, st7735->reset_level);
        vTaskDelay(pdMS_TO_TICKS(10));
        gpio_set_level(st7735->reset_gpio_num, !st7735->reset_level);
        vTaskDelay(pdMS_TO_TICKS(50));
    } else {
        ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, LCD_CMD_SWRESET, NULL, 0), TAG, "send SWRESET failed");
        vTaskDelay(pdMS_TO_TICKS(120));
    }
    return ESP_OK;
}

static esp_err_t panel_st7735_init(esp_lcd_panel_t *panel)
{
    st7735_panel_t *st7735 = __containerof(panel, st7735_panel_t, base);
    esp_lcd_panel_io_handle_t io = st7735->io;

    // 1. Software reset
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, LCD_CMD_SWRESET, NULL, 0), TAG, "SWRESET failed");
    vTaskDelay(pdMS_TO_TICKS(120));

    // 2. Out of sleep mode
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, LCD_CMD_SLPOUT, NULL, 0), TAG, "SLPOUT failed");
    vTaskDelay(pdMS_TO_TICKS(120));

    // 3. Frame rate control in normal mode (FRMCTR1)
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, ST7735_CMD_FRMCTR1, (uint8_t[]){0x01, 0x2C, 0x2D}, 3), TAG, "FRMCTR1 failed");

    // 4. Frame rate control in idle mode (FRMCTR2)
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, ST7735_CMD_FRMCTR2, (uint8_t[]){0x01, 0x2C, 0x2D}, 3), TAG, "FRMCTR2 failed");

    // 5. Frame rate control in partial mode (FRMCTR3)
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, ST7735_CMD_FRMCTR3, (uint8_t[]){0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D}, 6), TAG, "FRMCTR3 failed");

    // 6. Display inversion control (INVCTR): line inversion
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, ST7735_CMD_INVCTR, (uint8_t[]){0x07}, 1), TAG, "INVCTR failed");

    // 7. Power control 1 (PWCTR1)
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, ST7735_CMD_PWCTR1, (uint8_t[]){0xA2, 0x02, 0x84}, 3), TAG, "PWCTR1 failed");

    // 8. Power control 2 (PWCTR2)
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, ST7735_CMD_PWCTR2, (uint8_t[]){0xC5}, 1), TAG, "PWCTR2 failed");

    // 9. Power control 3 (PWCTR3)
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, ST7735_CMD_PWCTR3, (uint8_t[]){0x0A, 0x00}, 2), TAG, "PWCTR3 failed");

    // 10. Power control 4 (PWCTR4)
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, ST7735_CMD_PWCTR4, (uint8_t[]){0x8A, 0x2A}, 2), TAG, "PWCTR4 failed");

    // 11. Power control 5 (PWCTR5)
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, ST7735_CMD_PWCTR5, (uint8_t[]){0x8A, 0xEE}, 2), TAG, "PWCTR5 failed");

    // 12. VCOM control 1 (VMCTR1)
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, ST7735_CMD_VMCTR1, (uint8_t[]){0x0E}, 1), TAG, "VMCTR1 failed");

    // 13. Display inversion off by default
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, LCD_CMD_INVOFF, NULL, 0), TAG, "INVOFF failed");

    // 14. Memory access control & Pixel format
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, LCD_CMD_MADCTL, &st7735->madctl_val, 1), TAG, "MADCTL failed");
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, LCD_CMD_COLMOD, &st7735->colmod_val, 1), TAG, "COLMOD failed");

    // 15. Gamma adjustments (GMCTRP1 & GMCTRN1)
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, ST7735_CMD_GMCTRP1,
        (uint8_t[]){0x02, 0x1C, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2D, 0x29, 0x25, 0x2B, 0x39, 0x00, 0x01, 0x03, 0x10}, 16),
        TAG, "GMCTRP1 failed");
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, ST7735_CMD_GMCTRN1,
        (uint8_t[]){0x03, 0x1D, 0x07, 0x06, 0x2E, 0x2C, 0x29, 0x2D, 0x2E, 0x2E, 0x37, 0x3F, 0x00, 0x00, 0x02, 0x10}, 16),
        TAG, "GMCTRN1 failed");

    // 16. Normal display mode on (NORON)
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, 0x13, NULL, 0), TAG, "NORON failed");
    vTaskDelay(pdMS_TO_TICKS(10));

    // 17. Main screen turn on (DISPON)
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, LCD_CMD_DISPON, NULL, 0), TAG, "DISPON failed");
    vTaskDelay(pdMS_TO_TICKS(100));

    ESP_LOGI(TAG, "ST7735 initialized successfully (1.8\" 128x160 TFT)");
    return ESP_OK;
}

static esp_err_t panel_st7735_draw_bitmap(esp_lcd_panel_t *panel, int x_start, int y_start, int x_end, int y_end, const void *color_data)
{
    st7735_panel_t *st7735 = __containerof(panel, st7735_panel_t, base);
    esp_lcd_panel_io_handle_t io = st7735->io;

    x_start += st7735->x_gap;
    x_end += st7735->x_gap;
    y_start += st7735->y_gap;
    y_end += st7735->y_gap;

    // Column address set (CASET)
    uint8_t caset[] = {
        (uint8_t)(x_start >> 8),
        (uint8_t)(x_start & 0xFF),
        (uint8_t)((x_end - 1) >> 8),
        (uint8_t)((x_end - 1) & 0xFF),
    };
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, LCD_CMD_CASET, caset, sizeof(caset)), TAG, "send CASET failed");

    // Row address set (RASET)
    uint8_t raset[] = {
        (uint8_t)(y_start >> 8),
        (uint8_t)(y_start & 0xFF),
        (uint8_t)((y_end - 1) >> 8),
        (uint8_t)((y_end - 1) & 0xFF),
    };
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io, LCD_CMD_RASET, raset, sizeof(raset)), TAG, "send RASET failed");

    // Memory write (RAMWR)
    size_t len = (size_t)(x_end - x_start) * (size_t)(y_end - y_start) * sizeof(uint16_t);
    return esp_lcd_panel_io_tx_color(io, LCD_CMD_RAMWR, color_data, len);
}

static esp_err_t panel_st7735_invert_color(esp_lcd_panel_t *panel, bool invert_color_data)
{
    st7735_panel_t *st7735 = __containerof(panel, st7735_panel_t, base);
    uint8_t cmd = invert_color_data ? LCD_CMD_INVON : LCD_CMD_INVOFF;
    return esp_lcd_panel_io_tx_param(st7735->io, cmd, NULL, 0);
}

static esp_err_t panel_st7735_mirror(esp_lcd_panel_t *panel, bool mirror_x, bool mirror_y)
{
    st7735_panel_t *st7735 = __containerof(panel, st7735_panel_t, base);
    if (mirror_x) {
        st7735->madctl_val |= LCD_CMD_MX_BIT;
    } else {
        st7735->madctl_val &= ~LCD_CMD_MX_BIT;
    }
    if (mirror_y) {
        st7735->madctl_val |= LCD_CMD_MY_BIT;
    } else {
        st7735->madctl_val &= ~LCD_CMD_MY_BIT;
    }
    return esp_lcd_panel_io_tx_param(st7735->io, LCD_CMD_MADCTL, &st7735->madctl_val, 1);
}

static esp_err_t panel_st7735_swap_xy(esp_lcd_panel_t *panel, bool swap_axes)
{
    st7735_panel_t *st7735 = __containerof(panel, st7735_panel_t, base);
    if (swap_axes) {
        st7735->madctl_val |= LCD_CMD_MV_BIT;
    } else {
        st7735->madctl_val &= ~LCD_CMD_MV_BIT;
    }
    return esp_lcd_panel_io_tx_param(st7735->io, LCD_CMD_MADCTL, &st7735->madctl_val, 1);
}

static esp_err_t panel_st7735_set_gap(esp_lcd_panel_t *panel, int x_gap, int y_gap)
{
    st7735_panel_t *st7735 = __containerof(panel, st7735_panel_t, base);
    st7735->x_gap = x_gap;
    st7735->y_gap = y_gap;
    return ESP_OK;
}

static esp_err_t panel_st7735_disp_on_off(esp_lcd_panel_t *panel, bool on_off)
{
    st7735_panel_t *st7735 = __containerof(panel, st7735_panel_t, base);
    uint8_t cmd = on_off ? LCD_CMD_DISPON : LCD_CMD_DISPOFF;
    return esp_lcd_panel_io_tx_param(st7735->io, cmd, NULL, 0);
}

static esp_err_t panel_st7735_disp_sleep(esp_lcd_panel_t *panel, bool sleep)
{
    st7735_panel_t *st7735 = __containerof(panel, st7735_panel_t, base);
    uint8_t cmd = sleep ? LCD_CMD_SLPIN : LCD_CMD_SLPOUT;
    esp_err_t ret = esp_lcd_panel_io_tx_param(st7735->io, cmd, NULL, 0);
    if (ret == ESP_OK) {
        vTaskDelay(pdMS_TO_TICKS(120));
    }
    return ret;
}
