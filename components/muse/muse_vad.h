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

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Adaptive Voice Activity Detection (VAD) & Voice Wake-Up Engine
 * Inspired by Xiaozhi AI's dynamic noise floor tracking, Zero-Crossing Rate
 * formant verification, and speech turn silence cutoff.
 */

typedef enum {
    MUSE_VAD_SILENCE = 0,
    MUSE_VAD_SPEECH  = 1,
} muse_vad_result_t;

typedef struct {
    int sample_rate;
    float noise_floor_db;
    float speech_threshold_db;
    int consecutive_speech_frames;
    int consecutive_silence_frames;
    int wakeup_speech_frames;
    bool speech_started;
} muse_vad_t;

/* Initialize VAD state. Default noise floor starts at -65.0 dBFS. */
void muse_vad_init(muse_vad_t *vad, int sample_rate);

/* Reset VAD counters for a new turn while retaining learned noise floor. */
void muse_vad_reset(muse_vad_t *vad);

/* Calculate frame RMS in dBFS (-100.0f for silence). */
float muse_vad_calculate_dbfs(const int16_t *pcm, size_t frames);

/* Calculate Zero-Crossing Rate (ZCR) across the frame. */
int muse_vad_calculate_zcr(const int16_t *pcm, size_t frames);

/* Process one frame (e.g. 20ms / 320 samples at 16kHz). Updates noise floor and state. */
muse_vad_result_t muse_vad_process(muse_vad_t *vad, const int16_t *pcm, size_t frames);

/* Check if frame qualifies as voice wake-up trigger (requires sustained vocal energy). */
bool muse_vad_check_wakeup(muse_vad_t *vad, const int16_t *pcm, size_t frames);

/* Returns true if speech has occurred and silence persists for silence_timeout_ms. */
bool muse_vad_should_cutoff(const muse_vad_t *vad, int silence_timeout_ms);

/* Returns true if no speech has started and total elapsed recording exceeds max_wait_ms. */
bool muse_vad_timed_out(const muse_vad_t *vad, int total_elapsed_ms, int max_wait_ms);

#ifdef __cplusplus
}
#endif
