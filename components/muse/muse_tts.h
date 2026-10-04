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

#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifndef ESP_OK
typedef int esp_err_t;
#define ESP_OK 0
#define ESP_FAIL -1
#define ESP_ERR_INVALID_ARG 0x102
#define ESP_ERR_INVALID_STATE 0x103
#define ESP_ERR_NOT_SUPPORTED 0x106
#endif

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Free Vietnamese & English Text-to-Speech (TTS) Engine
 * Uses Google Translate TTS CDN (direct MPEG MP3 stream, zero API key)
 * with smart UTF-8 language detection (Vietnamese diacritics vs English),
 * sentence chunking, and minimp3 hardware streaming.
 */

typedef enum {
    MUSE_TTS_LANG_AUTO = 0,
    MUSE_TTS_LANG_VI,
    MUSE_TTS_LANG_EN,
} muse_tts_lang_pref_t;

typedef void (*muse_tts_data_cb_t)(const uint8_t *data, size_t len, void *ctx);
typedef void (*muse_tts_done_cb_t)(bool success, void *ctx);

/* Initialize TTS system and defaults. */
void muse_tts_init(void);

/* Detects whether text contains Vietnamese characters or standard English. Returns "vi" or "en". */
const char *muse_tts_detect_lang(const char *text);

/* URL-encodes UTF-8 string into dst (null-terminated). Returns bytes written (excluding null). */
size_t muse_tts_url_encode(const char *src, char *dst, size_t dst_len);

/* Splits text into sentence chunks (<= 160 chars) preserving complete words. */
int muse_tts_split_sentences(const char *text, char chunks[][192], int max_chunks);

/* Builds the Google Translate TTS query URL. Returns bytes written. */
size_t muse_tts_build_url(const char *chunk, const char *lang, char *out_url, size_t max_len);

/* Fetches and streams TTS MP3 audio for given text over HTTP. Calls data_cb with MP3 chunks. */
esp_err_t muse_tts_speak_text(const char *text, const char *lang_override,
                              muse_tts_data_cb_t data_cb, void *ctx);

/* Standalone speech helper (called from serial console ">say=<text>"). */
void muse_tts_speak_standalone(const char *text);

/* Cancels any ongoing TTS fetch/streaming session (e.g. on user barge-in). */
void muse_tts_cancel(void);

/* Returns whether cancellation has been requested. */
bool muse_tts_is_cancelled(void);

/* Error and diagnostic status codes for TTS operations. */
typedef enum {
    MUSE_TTS_STATUS_OK = 0,
    MUSE_TTS_STATUS_OFFLINE,       /* Wi-Fi not connected */
    MUSE_TTS_STATUS_MUTED,         /* Speaker off or volume 0 */
    MUSE_TTS_STATUS_CANCELLED,     /* User barged in */
    MUSE_TTS_STATUS_HTTP_FAIL,     /* Google CDN error (4xx/5xx/timeout) */
    MUSE_TTS_STATUS_MEM_FAIL,      /* Allocation failed */
    MUSE_TTS_STATUS_INVALID_ARG,   /* Empty or invalid text */
} muse_tts_status_t;

/* Returns human-readable diagnostic description of TTS status. */
const char *muse_tts_status_str(muse_tts_status_t st);

#ifndef ESP_PLATFORM
/* Mock helpers for host unit testing exception flows */
void muse_tts_test_set_mock_wifi(bool connected);
void muse_tts_test_set_mock_speaker(bool on, int vol);
#endif

#ifdef __cplusplus
}
#endif
