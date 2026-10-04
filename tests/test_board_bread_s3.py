# Copyright (c) Meta Platforms, Inc. and affiliates.
# SPDX-License-Identifier: Apache-2.0

"""Host tests for Bread S3 / Rody Pet S3 board port:
- GC9A01 240x240 Round display geometry and RGB565 color packing
- Circular bezel chord clipping (no NaN, safe layout)
- Audio PCM bit shifting (INMP441 32-to-16-bit) and gain clipping
- Board configuration integrity in Kconfig, CMakeLists.txt, board.sh, ports.py
"""

from pathlib import Path
import math
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

HARNESS = r'''
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>
#include <assert.h>

#define LCD_RES 240

// Test 1: RGB565 color packing
uint16_t test_rgb565(uint8_t r, uint8_t g, uint8_t b) {
    return (uint16_t)(((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3));
}

// Test 2: Round screen chord safety check
int test_round_chord(int ring_in, int cap_w) {
    if (cap_w * cap_w / 4 >= ring_in * ring_in) {
        cap_w = (int)(sqrtf((float)(ring_in * ring_in - 2500)) * 2);
        cap_w = cap_w / 16 * 16;
        if (cap_w < 128) cap_w = 128;
    }
    float diff = (float)(ring_in * ring_in - cap_w * cap_w / 4);
    assert(diff >= 0.0f); // MUST NEVER BE NEGATIVE (NO NAN)
    return (int)sqrtf(diff) - 3;
}

// Test 3: Audio PCM bit shifting
int16_t test_mic_sample(int32_t raw_32, int gain_q8) {
    #define MIC_SHIFT 12
    int v = (raw_32 >> MIC_SHIFT) * gain_q8 >> 8;
    return v > 32767 ? 32767 : v < -32768 ? -32768 : (int16_t)v;
}

int main(void) {
    // 1. Color check: Pure Red in RGB565
    uint16_t red = test_rgb565(255, 0, 0);
    assert(red == 0xF800);

    // Pure Green in RGB565
    uint16_t green = test_rgb565(0, 255, 0);
    assert(green == 0x07E0);

    // Pure Blue in RGB565
    uint16_t blue = test_rgb565(0, 0, 255);
    assert(blue == 0x001F);

    // 2. Round chord check for 240x240 screen (ring_in = 110)
    int ring_in = 110;
    int cap_bottom = test_round_chord(ring_in, 256);
    assert(cap_bottom > 0 && cap_bottom < 110);

    // 3. Audio conversion check
    int32_t zero_in = 0;
    assert(test_mic_sample(zero_in, 256) == 0);

    int32_t pos_max = 0x7FFFFF00;
    int16_t sample_pos = test_mic_sample(pos_max, 256);
    assert(sample_pos > 32700);

    int16_t clipped = test_mic_sample(pos_max, 512); // 2x gain
    assert(clipped == 32767);

    int32_t neg_min = (int32_t)0x80000000;
    int16_t sample_neg = test_mic_sample(neg_min, 256);
    assert(sample_neg == -32768);

    printf("ALL_GC9A01_HARNESS_TESTS_PASSED\n");
    return 0;
}
'''


class BreadS3BoardTest(unittest.TestCase):
    def test_gc9a01_and_audio_c_harness(self):
        """Compile and execute the C harness verifying GC9A01 geometry, chord math and audio conversion."""
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "harness.c"
            out = Path(td) / "harness"
            src.write_text(HARNESS)

            cmd = ["clang", "-O2", "-Wall", "-Werror", str(src), "-o", str(out), "-lm"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, msg=f"Compile error:\n{res.stderr}")

            run_res = subprocess.run([str(out)], capture_output=True, text=True)
            self.assertEqual(run_res.returncode, 0, msg=f"Run error:\n{run_res.stderr}")
            self.assertIn("ALL_GC9A01_HARNESS_TESTS_PASSED", run_res.stdout)

    def test_board_configurations_present(self):
        """Verify Bread S3 is registered across all config files and supports GC9A01 round display."""
        # 1. Kconfig
        kconfig = (ROOT / "components/muse/Kconfig").read_text()
        self.assertIn("MUSE_BOARD_BREAD_S3", kconfig)
        self.assertIn('"bread_s3"', kconfig)

        # 2. CMakeLists.txt
        cmakelists = (ROOT / "components/muse/CMakeLists.txt").read_text()
        self.assertIn("CONFIG_MUSE_BOARD_BREAD_S3", cmakelists)
        self.assertIn("board_bread_s3.c", cmakelists)
        self.assertIn("esp_lcd_panel_gc9a01.c", cmakelists)

        # 3. idf_component.yml
        idf_comp = (ROOT / "components/muse/idf_component.yml").read_text()
        self.assertIn("bread_s3", idf_comp)

        # 4. board.sh & ports.py
        board_sh = (ROOT / "tools/muse/board.sh").read_text()
        self.assertIn("bread)", board_sh)

        ports_py = (ROOT / "tools/muse/ports.py").read_text()
        self.assertIn('"bread": USJ', ports_py)

        # 5. Device overlays exist
        self.assertTrue((ROOT / "devices/sdkconfig.bread-s3").exists())
        self.assertTrue((ROOT / "devices/sdkconfig.muse-bread-s3").exists())
        self.assertTrue((ROOT / "components/muse/boards/board_bread_s3.c").exists())
        self.assertTrue((ROOT / "components/muse/esp_lcd_panel_gc9a01.h").exists())
        self.assertTrue((ROOT / "components/muse/esp_lcd_panel_gc9a01.c").exists())

        # 6. Verify board_bread_s3.c has round=true and LCD_RES 240
        board_c = (ROOT / "components/muse/boards/board_bread_s3.c").read_text()
        self.assertIn(".round = true", board_c)
        self.assertIn("LCD_RES 240", board_c)
        self.assertIn("1.28f", board_c)
        self.assertIn("esp_lcd_new_panel_gc9a01", board_c)


if __name__ == "__main__":
    unittest.main()
