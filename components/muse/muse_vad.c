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

#include "muse_vad.h"

#include <math.h>
#include <stdlib.h>
#include <string.h>

#define DEFAULT_NOISE_FLOOR_DB    -65.0f
#define VAD_SNR_MARGIN_DB         12.0f
#define MIN_SPEECH_THRESHOLD_DB   -48.0f
#define MAX_SPEECH_THRESHOLD_DB   -22.0f

#define WAKEUP_CONSECUTIVE_FRAMES 4       /* ~80ms of sustained vocal formant */
#define MIN_VOICE_ZCR             6       /* Filters sub-bass rumbles */
#define MAX_VOICE_ZCR             110     /* Filters ultrasonic / sharp hiss */

void muse_vad_init(muse_vad_t *vad, int sample_rate)
{
    if (!vad) return;
    vad->sample_rate = sample_rate > 0 ? sample_rate : 16000;
    vad->noise_floor_db = DEFAULT_NOISE_FLOOR_DB;
    vad->speech_threshold_db = DEFAULT_NOISE_FLOOR_DB + VAD_SNR_MARGIN_DB;
    vad->consecutive_speech_frames = 0;
    vad->consecutive_silence_frames = 0;
    vad->wakeup_speech_frames = 0;
    vad->speech_started = false;
}

void muse_vad_reset(muse_vad_t *vad)
{
    if (!vad) return;
    vad->consecutive_speech_frames = 0;
    vad->consecutive_silence_frames = 0;
    vad->wakeup_speech_frames = 0;
    vad->speech_started = false;
}

float muse_vad_calculate_dbfs(const int16_t *pcm, size_t frames)
{
    if (!pcm || frames == 0) return -100.0f;
    double acc = 0.0;
    for (size_t i = 0; i < frames; i++) {
        acc += (double)pcm[i] * pcm[i];
    }
    double mean_sq = acc / frames;
    float db = 10.0f * log10f((float)(mean_sq / (32768.0 * 32768.0)) + 1e-10f);
    return db < -100.0f ? -100.0f : db;
}

int muse_vad_calculate_zcr(const int16_t *pcm, size_t frames)
{
    if (!pcm || frames < 2) return 0;
    int crossings = 0;
    for (size_t i = 1; i < frames; i++) {
        if ((pcm[i - 1] > 0 && pcm[i] <= 0) || (pcm[i - 1] < 0 && pcm[i] >= 0)) {
            crossings++;
        }
    }
    return crossings;
}

static void update_noise_floor(muse_vad_t *vad, float db)
{
    if (db < vad->noise_floor_db) {
        // Ambient noise dropped: adapt down relatively quickly
        vad->noise_floor_db = vad->noise_floor_db * 0.90f + db * 0.10f;
    } else if (db < vad->speech_threshold_db) {
        // Slow rise during quiet conditions
        vad->noise_floor_db = vad->noise_floor_db * 0.995f + db * 0.005f;
    }
    if (vad->noise_floor_db < -85.0f) vad->noise_floor_db = -85.0f;
    if (vad->noise_floor_db > -35.0f) vad->noise_floor_db = -35.0f;

    vad->speech_threshold_db = vad->noise_floor_db + VAD_SNR_MARGIN_DB;
    if (vad->speech_threshold_db < MIN_SPEECH_THRESHOLD_DB) {
        vad->speech_threshold_db = MIN_SPEECH_THRESHOLD_DB;
    }
    if (vad->speech_threshold_db > MAX_SPEECH_THRESHOLD_DB) {
        vad->speech_threshold_db = MAX_SPEECH_THRESHOLD_DB;
    }
}

muse_vad_result_t muse_vad_process(muse_vad_t *vad, const int16_t *pcm, size_t frames)
{
    if (!vad || !pcm || frames == 0) return MUSE_VAD_SILENCE;

    float db = muse_vad_calculate_dbfs(pcm, frames);
    int zcr = muse_vad_calculate_zcr(pcm, frames);

    update_noise_floor(vad, db);

    bool is_speech = (db >= vad->speech_threshold_db) &&
                     (zcr >= MIN_VOICE_ZCR && zcr <= MAX_VOICE_ZCR);

    if (is_speech) {
        vad->consecutive_speech_frames++;
        vad->consecutive_silence_frames = 0;
        if (vad->consecutive_speech_frames >= 2) {
            vad->speech_started = true;
        }
        return MUSE_VAD_SPEECH;
    } else {
        vad->consecutive_silence_frames++;
        vad->consecutive_speech_frames = 0;
        return MUSE_VAD_SILENCE;
    }
}

bool muse_vad_check_wakeup(muse_vad_t *vad, const int16_t *pcm, size_t frames)
{
    if (!vad || !pcm || frames == 0) return false;

    float db = muse_vad_calculate_dbfs(pcm, frames);
    int zcr = muse_vad_calculate_zcr(pcm, frames);

    update_noise_floor(vad, db);

    // Wake-up trigger uses SNR margin above ambient noise
    bool vocal_candidate = (db >= (vad->noise_floor_db + 10.0f)) &&
                          (db >= MIN_SPEECH_THRESHOLD_DB) &&
                          (zcr >= MIN_VOICE_ZCR && zcr <= MAX_VOICE_ZCR);

    if (vocal_candidate) {
        vad->wakeup_speech_frames++;
        if (vad->wakeup_speech_frames >= WAKEUP_CONSECUTIVE_FRAMES) {
            vad->wakeup_speech_frames = 0;
            return true;
        }
    } else {
        if (vad->wakeup_speech_frames > 0) {
            vad->wakeup_speech_frames--;
        }
    }
    return false;
}

bool muse_vad_should_cutoff(const muse_vad_t *vad, int silence_timeout_ms)
{
    if (!vad || !vad->speech_started) return false;
    int silence_ms = vad->consecutive_silence_frames * 20; // 20ms per frame
    return silence_ms >= silence_timeout_ms;
}

bool muse_vad_timed_out(const muse_vad_t *vad, int total_elapsed_ms, int max_wait_ms)
{
    if (!vad) return false;
    return (!vad->speech_started) && (total_elapsed_ms >= max_wait_ms);
}
