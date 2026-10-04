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

#include "muse_tts.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef ESP_PLATFORM
#include "esp_http_client.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "muse_settings.h"
#include "muse_wifi.h"
static const char *TAG = "muse_tts";

#ifndef CONFIG_MUSE_FREE_TTS_TIMEOUT_MS
#define CONFIG_MUSE_FREE_TTS_TIMEOUT_MS 8000
#endif

#ifndef CONFIG_MUSE_FREE_TTS_MAX_CHUNKS
#define CONFIG_MUSE_FREE_TTS_MAX_CHUNKS 12
#endif
#endif

static volatile bool s_tts_cancelled = false;

void muse_tts_cancel(void)
{
    s_tts_cancelled = true;
}

bool muse_tts_is_cancelled(void)
{
    return s_tts_cancelled;
}

const char *muse_tts_status_str(muse_tts_status_t st)
{
    switch (st) {
    case MUSE_TTS_STATUS_OK: return "OK";
    case MUSE_TTS_STATUS_OFFLINE: return "Wi-Fi Disconnected";
    case MUSE_TTS_STATUS_MUTED: return "Speaker Muted";
    case MUSE_TTS_STATUS_CANCELLED: return "Playback Cancelled";
    case MUSE_TTS_STATUS_HTTP_FAIL: return "CDN HTTP Error";
    case MUSE_TTS_STATUS_MEM_FAIL: return "Out of Memory";
    case MUSE_TTS_STATUS_INVALID_ARG: return "Invalid/Empty Text";
    default: return "Unknown Error";
    }
}

void muse_tts_init(void)
{
    s_tts_cancelled = false;
}

const char *muse_tts_detect_lang(const char *text)
{
    if (!text || text[0] == '\0') {
        return "en";
    }

    size_t len = strlen(text);
    for (size_t i = 0; i < len; i++) {
        uint8_t b = (uint8_t)text[i];
        if (b == 0xC3 || b == 0xC4 || b == 0xC5) {
            if (i + 1 < len) {
                uint8_t next = (uint8_t)text[i + 1];
                if (next >= 0x80 && next <= 0xBF) {
                    return "vi";
                }
            }
        } else if (b == 0xE1) {
            if (i + 1 < len) {
                uint8_t next = (uint8_t)text[i + 1];
                if (next == 0xBA || next == 0xBB) {
                    return "vi";
                }
            }
        }
    }
    return "en";
}

size_t muse_tts_url_encode(const char *src, char *dst, size_t dst_len)
{
    if (!src || !dst || dst_len == 0) {
        return 0;
    }

    static const char hex[] = "0123456789ABCDEF";
    size_t written = 0;

    while (*src && written + 1 < dst_len) {
        unsigned char c = (unsigned char)*src;
        if (isalnum(c) || c == '-' || c == '_' || c == '.' || c == '~') {
            dst[written++] = (char)c;
        } else if (c == ' ') {
            if (written + 3 >= dst_len) break;
            dst[written++] = '%';
            dst[written++] = '2';
            dst[written++] = '0';
        } else {
            if (written + 3 >= dst_len) break;
            dst[written++] = '%';
            dst[written++] = hex[(c >> 4) & 0x0F];
            dst[written++] = hex[c & 0x0F];
        }
        src++;
    }
    dst[written] = '\0';
    return written;
}

int muse_tts_split_sentences(const char *text, char chunks[][192], int max_chunks)
{
    if (!text || !chunks || max_chunks <= 0) {
        return 0;
    }

    int count = 0;
    const char *p = text;
    while (*p && count < max_chunks) {
        // Skip leading whitespace
        while (*p && isspace((unsigned char)*p)) {
            p++;
        }
        if (!*p) break;

        size_t chunk_len = 0;
        const char *start = p;
        const char *best_break = NULL;

        while (*p && chunk_len < 150) {
            char c = *p;
            chunk_len++;
            if (c == '.' || c == '!' || c == '?' || c == '\n') {
                best_break = p + 1;
                if (chunk_len >= 10) {
                    p++;
                    break;
                }
            } else if ((c == ';' || c == ',') && chunk_len >= 80) {
                best_break = p + 1;
            } else if (c == ' ' && chunk_len >= 120) {
                best_break = p;
            }
            p++;
        }

        const char *end = best_break ? best_break : p;
        size_t actual_len = (size_t)(end - start);
        if (actual_len >= 191) actual_len = 191;

        memcpy(chunks[count], start, actual_len);
        chunks[count][actual_len] = '\0';

        // Strip trailing whitespace
        while (actual_len > 0 && isspace((unsigned char)chunks[count][actual_len - 1])) {
            chunks[count][--actual_len] = '\0';
        }

        if (actual_len > 0) {
            count++;
        }
        p = end;
    }
    return count;
}

size_t muse_tts_build_url(const char *chunk, const char *lang, char *out_url, size_t max_len)
{
    if (!chunk || !out_url || max_len == 0) {
        return 0;
    }

    char encoded[512];
    muse_tts_url_encode(chunk, encoded, sizeof(encoded));

    const char *actual_lang = (lang && lang[0]) ? lang : muse_tts_detect_lang(chunk);

    int n = snprintf(out_url, max_len,
                     "https://translate.google.com/translate_tts?ie=UTF-8&tl=%s&client=tw-ob&q=%s",
                     actual_lang, encoded);
    return (n > 0 && (size_t)n < max_len) ? (size_t)n : 0;
}

#ifdef ESP_PLATFORM

static esp_err_t http_event_handler(esp_http_client_event_t *evt)
{
    if (evt->event_id == HTTP_EVENT_ON_DATA && evt->data_len > 0) {
        muse_tts_data_cb_t cb = (muse_tts_data_cb_t)evt->user_data;
        if (cb) {
            cb((const uint8_t *)evt->data, (size_t)evt->data_len, NULL);
        }
    }
    return ESP_OK;
}

esp_err_t muse_tts_speak_text(const char *text, const char *lang_override,
                              muse_tts_data_cb_t data_cb, void *ctx)
{
    s_tts_cancelled = false;

    if (!text || text[0] == '\0' || !data_cb) {
        ESP_LOGW(TAG, "[TTS WARN] Invalid argument: text is empty or callback is NULL.");
        return ESP_ERR_INVALID_ARG;
    }

    if (!muse_wifi_connected()) {
        ESP_LOGW(TAG, "[TTS ERROR] Wi-Fi is disconnected! Cannot stream audio from Google TTS CDN.");
        ESP_LOGW(TAG, "[TTS HINT] Action required: Connect device to Wi-Fi via Muse app or Settings menu.");
        printf("@tts {\"status\":\"error\",\"code\":\"WIFI_DISCONNECTED\",\"action\":\"connect_wifi\"}\n");
        fflush(stdout);
        return ESP_ERR_INVALID_STATE;
    }

    if (!muse_settings_speaker_on() || muse_settings_volume() <= 0) {
        ESP_LOGI(TAG, "[TTS INFO] Speaker is muted (vol=%d, on=%d). Skipping network fetch to save bandwidth.",
                 muse_settings_volume(), (int)muse_settings_speaker_on());
        printf("@tts {\"status\":\"skipped\",\"code\":\"SPEAKER_MUTED\"}\n");
        fflush(stdout);
        return ESP_ERR_NOT_SUPPORTED;
    }

    const char *lang = (lang_override && lang_override[0]) ? lang_override : muse_tts_detect_lang(text);
    ESP_LOGI(TAG, "[TTS START] Speaking (lang: %s, %u chars): \"%.40s...\"", lang, (unsigned)strlen(text), text);
    printf("@tts {\"status\":\"start\",\"lang\":\"%s\",\"bytes\":%u}\n", lang, (unsigned)strlen(text));
    fflush(stdout);

    char chunks[CONFIG_MUSE_FREE_TTS_MAX_CHUNKS][192];
    int n_chunks = muse_tts_split_sentences(text, chunks, CONFIG_MUSE_FREE_TTS_MAX_CHUNKS);
    if (n_chunks <= 0) {
        ESP_LOGW(TAG, "[TTS WARN] Text splitting yielded no speakable chunks.");
        return ESP_FAIL;
    }

    char url[768];
    int success_chunks = 0;
    for (int i = 0; i < n_chunks; i++) {
        if (s_tts_cancelled) {
            ESP_LOGI(TAG, "[TTS CANCEL] Playback interrupted by user barge-in.");
            printf("@tts {\"status\":\"cancelled\",\"chunk\":%d}\n", i);
            fflush(stdout);
            return ESP_ERR_INVALID_STATE;
        }

        muse_tts_build_url(chunks[i], lang, url, sizeof(url));

        esp_http_client_config_t config = {
            .url = url,
            .event_handler = http_event_handler,
            .user_data = (void *)data_cb,
            .timeout_ms = CONFIG_MUSE_FREE_TTS_TIMEOUT_MS,
            .buffer_size = 2048,
        };

        esp_http_client_handle_t client = esp_http_client_init(&config);
        if (!client) {
            ESP_LOGE(TAG, "[TTS ERROR] Failed to initialize HTTP client for chunk %d.", i + 1);
            continue;
        }

        esp_http_client_set_header(client, "User-Agent",
                                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");
        esp_err_t err = esp_http_client_perform(client);
        int status = esp_http_client_get_status_code(client);
        esp_http_client_cleanup(client);

        if (err != ESP_OK) {
            ESP_LOGW(TAG, "[TTS ERROR] Chunk %d/%d HTTP request failed (err %d). Check router/DNS.",
                     i + 1, n_chunks, err);
            printf("@tts {\"status\":\"error\",\"chunk\":%d,\"err\":%d}\n", i + 1, err);
            fflush(stdout);
        } else if (status == 429) {
            ESP_LOGW(TAG, "[TTS WARN] Google CDN rate limited (HTTP 429). Falling back to captions.");
            printf("@tts {\"status\":\"error\",\"code\":\"RATE_LIMIT_429\"}\n");
            fflush(stdout);
            break;
        } else if (status != 200) {
            ESP_LOGW(TAG, "[TTS WARN] Chunk %d/%d HTTP returned code %d. Falling back to captions.",
                     i + 1, n_chunks, status);
            printf("@tts {\"status\":\"error\",\"chunk\":%d,\"http_code\":%d}\n", i + 1, status);
            fflush(stdout);
        } else {
            success_chunks++;
            ESP_LOGD(TAG, "[TTS OK] Chunk %d/%d streamed successfully.", i + 1, n_chunks);
        }
    }

    if (success_chunks == 0) {
        ESP_LOGW(TAG, "[TTS FAIL] All audio chunks failed. Smoothly falling back to silent reading pace.");
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "[TTS DONE] Successfully streamed %d/%d chunks.", success_chunks, n_chunks);
    printf("@tts {\"status\":\"done\",\"chunks_streamed\":%d,\"total\":%d}\n", success_chunks, n_chunks);
    fflush(stdout);
    return ESP_OK;
}

void muse_tts_speak_standalone(const char *text)
{
    ESP_LOGI(TAG, "[TTS STANDALONE] Speak requested: %s", text ? text : "");
}

#else

// Host test mock states
static bool s_mock_wifi_connected = true;
static bool s_mock_speaker_on = true;
static int s_mock_volume = 80;

void muse_tts_test_set_mock_wifi(bool connected)
{
    s_mock_wifi_connected = connected;
}

void muse_tts_test_set_mock_speaker(bool on, int vol)
{
    s_mock_speaker_on = on;
    s_mock_volume = vol;
}

esp_err_t muse_tts_speak_text(const char *text, const char *lang_override,
                              muse_tts_data_cb_t data_cb, void *ctx)
{
    (void)lang_override;
    (void)data_cb;
    (void)ctx;
    if (!text || text[0] == '\0' || !data_cb) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_mock_wifi_connected) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!s_mock_speaker_on || s_mock_volume <= 0) {
        return ESP_ERR_NOT_SUPPORTED;
    }
    if (s_tts_cancelled) {
        return ESP_ERR_INVALID_STATE;
    }
    return ESP_OK;
}

void muse_tts_speak_standalone(const char *text)
{
    (void)text;
}

#endif
