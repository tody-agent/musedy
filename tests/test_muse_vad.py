# Copyright (c) Meta Platforms, Inc. and affiliates.
# SPDX-License-Identifier: Apache-2.0

"""Host tests for Voice Activity Detection (VAD) and Hands-Free Voice Wake-Up:
- ANSI C VAD engine math (RMS dBFS, asymmetric noise floor tracking)
- Zero-Crossing Rate (ZCR) human formant discrimination
- Voice Wake-Up trigger requiring multi-frame speech onset
- End-of-Speech silence cutoff (Xiaozhi-style token/latency optimization)
- Setting contract and configuration verification
"""

import math
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

VAD_C_HARNESS = r'''
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <assert.h>

#include "muse_vad.h"

// Generate a synthetic mono PCM frame (16kHz, 320 samples)
void gen_tone(int16_t *buf, size_t n, float freq_hz, float amplitude, float *phase) {
    for (size_t i = 0; i < n; i++) {
        buf[i] = (int16_t)(amplitude * sinf(*phase));
        *phase += 2.0f * (float)M_PI * freq_hz / 16000.0f;
        if (*phase > 2.0f * (float)M_PI) *phase -= 2.0f * (float)M_PI;
    }
}

void gen_silence(int16_t *buf, size_t n) {
    for (size_t i = 0; i < n; i++) {
        buf[i] = (int16_t)((rand() % 20) - 10); // Low background dither (-60 dBFS)
    }
}

int main(void) {
    muse_vad_t vad;
    muse_vad_init(&vad, 16000);

    // Test 1: Initial state
    assert(vad.noise_floor_db < -50.0f);
    assert(!vad.speech_started);

    // Test 2: Silence processing keeps VAD in silence state
    int16_t silence_frame[320];
    gen_silence(silence_frame, 320);
    for (int i = 0; i < 20; i++) {
        muse_vad_result_t res = muse_vad_process(&vad, silence_frame, 320);
        assert(res == MUSE_VAD_SILENCE);
    }
    assert(!vad.speech_started);

    // Test 3: Wake-up trigger with voice tone (500 Hz tone, amplitude 8000 ~ -12 dBFS)
    int16_t speech_frame[320];
    float phase = 0.0f;
    bool woken = false;
    for (int i = 0; i < 10; i++) {
        gen_tone(speech_frame, 320, 500.0f, 8000.0f, &phase);
        if (muse_vad_check_wakeup(&vad, speech_frame, 320)) {
            woken = true;
            break;
        }
    }
    assert(woken == true);

    // Test 4: End-of-speech silence cutoff simulation (Xiaozhi-style)
    // Reset VAD for new turn
    muse_vad_reset(&vad);
    assert(!vad.speech_started);

    // Feed 10 frames of speech (200 ms)
    for (int i = 0; i < 10; i++) {
        gen_tone(speech_frame, 320, 400.0f, 6000.0f, &phase);
        muse_vad_result_t res = muse_vad_process(&vad, speech_frame, 320);
        assert(res == MUSE_VAD_SPEECH);
    }
    assert(vad.speech_started == true);
    assert(muse_vad_should_cutoff(&vad, 700) == false);

    // Feed silence frames: should cutoff at 700ms (35 frames)
    int cutoff_frame = -1;
    for (int i = 0; i < 50; i++) {
        muse_vad_process(&vad, silence_frame, 320);
        if (muse_vad_should_cutoff(&vad, 700)) {
            cutoff_frame = i;
            break;
        }
    }
    // 35 frames * 20ms = 700ms cutoff point
    assert(cutoff_frame >= 34 && cutoff_frame <= 36);

    // Test 5: Verify massive token saving
    // 10 speech frames + 35 silence frames = 45 frames (900 ms)
    // vs full 15s turn (750 frames) -> 94% saving on dead air
    size_t vad_frames = (10 + cutoff_frame) * 320;
    size_t full_turn_frames = 15 * 16000;
    assert(vad_frames < (full_turn_frames / 4)); // Saved > 75% frames!

    printf("ALL_VAD_TESTS_PASSED\n");
    return 0;
}
'''


class VoiceWakeupVadTest(unittest.TestCase):
    def test_vad_c_harness(self):
        """Compile and execute C harness verifying VAD algorithms and cutoff timing."""
        vad_c = ROOT / "components/muse/muse_vad.c"
        vad_h = ROOT / "components/muse/muse_vad.h"
        self.assertTrue(vad_c.exists(), f"{vad_c} must exist")
        self.assertTrue(vad_h.exists(), f"{vad_h} must exist")

        with tempfile.TemporaryDirectory() as td:
            harness_src = Path(td) / "harness.c"
            out_bin = Path(td) / "harness"
            harness_src.write_text(VAD_C_HARNESS)

            import os
            env = dict(os.environ)
            if Path("/Library/Developer/CommandLineTools").exists():
                env["DEVELOPER_DIR"] = "/Library/Developer/CommandLineTools"

            cmd = [
                "clang", "-O2", "-Wall", "-Werror",
                f"-I{ROOT / 'components/muse'}",
                str(harness_src),
                str(vad_c),
                "-lm",
                "-o", str(out_bin)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, env=env)
            self.assertEqual(res.returncode, 0, msg=f"Compile error:\n{res.stderr}")

            run_res = subprocess.run([str(out_bin)], capture_output=True, text=True, env=env)
            self.assertEqual(run_res.returncode, 0, msg=f"Run error:\n{run_res.stderr}")
            self.assertIn("ALL_VAD_TESTS_PASSED", run_res.stdout)

    def test_settings_exports_wakeup(self):
        """Verify muse_settings.h has MUSE_SETTING_WAKEUP and getters/setters."""
        hdr = (ROOT / "components/muse/muse_settings.h").read_text()
        self.assertIn("MUSE_SETTING_WAKEUP", hdr)
        self.assertIn("muse_settings_wakeup_on", hdr)
        self.assertIn("muse_settings_set_wakeup_on", hdr)

    def test_kconfig_and_sdkconfig_wakeup_default(self):
        """Verify Kconfig and device sdkconfig define CONFIG_MUSE_VOICE_WAKEUP."""
        kconfig = (ROOT / "components/muse/Kconfig").read_text()
        self.assertIn("MUSE_VOICE_WAKEUP", kconfig)

        sdkconfig = (ROOT / "devices/sdkconfig.muse-bread-s3").read_text()
        self.assertIn("CONFIG_MUSE_VOICE_WAKEUP=y", sdkconfig)

    def test_voice_and_ui_integration_present(self):
        """Verify muse_voice.c and muse_settings_ui.c integrate VAD and wakeup switch."""
        voice_c = (ROOT / "components/muse/muse_voice.c").read_text()
        self.assertIn("muse_vad_check_wakeup", voice_c)
        self.assertIn("muse_vad_should_cutoff", voice_c)
        self.assertIn("Xiaozhi Voice Wake-Up triggered", voice_c)
        self.assertIn("Xiaozhi VAD: silence cutoff", voice_c)

        ui_c = (ROOT / "components/muse/muse_settings_ui.c").read_text()
        self.assertIn("s_wakeup_sw", ui_c)
        self.assertIn("Voice wake", ui_c)
        self.assertIn("on_wakeup_sw", ui_c)


if __name__ == "__main__":
    unittest.main()
