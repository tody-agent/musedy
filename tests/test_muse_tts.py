# Copyright (c) Meta Platforms, Inc. and affiliates.
# SPDX-License-Identifier: Apache-2.0

"""Host tests for Free Vietnamese & English Text-to-Speech (TTS):
- Language detection for Vietnamese (UTF-8 diacritics) vs English (ASCII/Latin)
- UTF-8 URL encoding conforming to Google Translate TTS specs
- Sentence splitting on punctuation boundaries with <= 160 char limit
- Full Google Translate TTS URL generation
- Settings, Kconfig, and integration contracts
"""

from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

TTS_C_HARNESS = r'''
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include "muse_tts.h"

static void dummy_cb(const uint8_t *d, size_t l, void *c) { (void)d; (void)l; (void)c; }

int main(void) {
    muse_tts_init();

    // Test 1: Language Detection for Vietnamese
    assert(strcmp(muse_tts_detect_lang("Xin chào, tôi là Rody!"), "vi") == 0);
    assert(strcmp(muse_tts_detect_lang("Hôm nay thời tiết thế nào?"), "vi") == 0);
    assert(strcmp(muse_tts_detect_lang("Cảm ơn bạn rất nhiều."), "vi") == 0);
    assert(strcmp(muse_tts_detect_lang("Được rồi, tôi đang lắng nghe."), "vi") == 0);
    assert(strcmp(muse_tts_detect_lang("Bạn có khỏe không?"), "vi") == 0);

    // Test 2: Language Detection for English
    assert(strcmp(muse_tts_detect_lang("Hello, what is the weather today?"), "en") == 0);
    assert(strcmp(muse_tts_detect_lang("Thank you very much!"), "en") == 0);
    assert(strcmp(muse_tts_detect_lang("I am an AI robot built with ESP32-S3."), "en") == 0);
    assert(strcmp(muse_tts_detect_lang("Good morning!"), "en") == 0);

    // Test 3: URL Encoding
    char enc[256];
    size_t len = muse_tts_url_encode("Hello world!", enc, sizeof(enc));
    assert(len > 0);
    assert(strcmp(enc, "Hello%20world%21") == 0);

    len = muse_tts_url_encode("Xin chào", enc, sizeof(enc));
    assert(len > 0);
    assert(strcmp(enc, "Xin%20ch%C3%A0o") == 0);

    // Test 4: Sentence Splitting on Punctuation Boundaries
    const char *long_text =
        "Xin chào bạn! Tôi là Rody S3, một robot thông minh chạy trên ESP32. "
        "Hôm nay bạn cảm thấy thế nào? Tôi có thể giúp gì cho bạn hôm nay?";
    char chunks[8][192];
    int n = muse_tts_split_sentences(long_text, chunks, 8);
    assert(n >= 3);
    for (int i = 0; i < n; i++) {
        assert(strlen(chunks[i]) > 0);
        assert(strlen(chunks[i]) <= 160);
    }
    assert(strstr(chunks[0], "Xin chào bạn") != NULL);

    // Test 5: Full Google Translate TTS URL Construction
    char url[512];
    size_t ulen = muse_tts_build_url("Xin chào", "vi", url, sizeof(url));
    assert(ulen > 0);
    assert(strstr(url, "translate.google.com/translate_tts") != NULL);
    assert(strstr(url, "tl=vi") != NULL);
    assert(strstr(url, "client=tw-ob") != NULL);
    assert(strstr(url, "q=Xin%20ch%C3%A0o") != NULL);

    ulen = muse_tts_build_url("Hello world", "en", url, sizeof(url));
    assert(strstr(url, "tl=en") != NULL);
    assert(strstr(url, "q=Hello%20world") != NULL);

    // Test 6: Status Descriptions
    assert(strcmp(muse_tts_status_str(MUSE_TTS_STATUS_OK), "OK") == 0);
    assert(strstr(muse_tts_status_str(MUSE_TTS_STATUS_OFFLINE), "Wi-Fi") != NULL);
    assert(strstr(muse_tts_status_str(MUSE_TTS_STATUS_MUTED), "Muted") != NULL);
    assert(strstr(muse_tts_status_str(MUSE_TTS_STATUS_CANCELLED), "Cancelled") != NULL);
    assert(strstr(muse_tts_status_str(MUSE_TTS_STATUS_HTTP_FAIL), "CDN") != NULL);
    assert(strstr(muse_tts_status_str(MUSE_TTS_STATUS_INVALID_ARG), "Invalid") != NULL);

    // Test 7: Cancellation Flag and API
    assert(!muse_tts_is_cancelled());
    muse_tts_cancel();
    assert(muse_tts_is_cancelled());

    // Test 8: Exception Handling in muse_tts_speak_text
    // Case 8a: NULL or empty text
    assert(muse_tts_speak_text(NULL, "vi", dummy_cb, NULL) != 0);
    assert(muse_tts_speak_text("", "vi", dummy_cb, NULL) != 0);

    // Case 8b: NULL callback
    assert(muse_tts_speak_text("Xin chao", "vi", NULL, NULL) != 0);

    // Case 8c: Wi-Fi offline exception
    muse_tts_init(); // reset cancel flag
    muse_tts_test_set_mock_wifi(false);
    assert(muse_tts_speak_text("Xin chao", "vi", dummy_cb, NULL) != 0);
    muse_tts_test_set_mock_wifi(true);

    // Case 8d: Speaker muted exception
    muse_tts_test_set_mock_speaker(false, 0);
    assert(muse_tts_speak_text("Xin chao", "vi", dummy_cb, NULL) != 0);
    muse_tts_test_set_mock_speaker(true, 80);

    // Case 8e: Cancelled barge-in exception
    muse_tts_cancel();
    assert(muse_tts_speak_text("Xin chao", "vi", dummy_cb, NULL) != 0);
    muse_tts_init();
    assert(muse_tts_speak_text("Xin chao", "vi", dummy_cb, NULL) == 0);

    printf("ALL_TTS_TESTS_PASSED\n");
    return 0;
}
'''


class FreeTtsTest(unittest.TestCase):
    def test_tts_c_harness(self):
        """Compile and execute C harness verifying TTS language detection, encoding, and chunking."""
        tts_c = ROOT / "components/muse/muse_tts.c"
        tts_h = ROOT / "components/muse/muse_tts.h"
        self.assertTrue(tts_c.exists(), f"{tts_c} must exist")
        self.assertTrue(tts_h.exists(), f"{tts_h} must exist")

        with tempfile.TemporaryDirectory() as td:
            harness_src = Path(td) / "harness.c"
            out_bin = Path(td) / "harness"
            harness_src.write_text(TTS_C_HARNESS)

            import os
            env = dict(os.environ)
            if Path("/Library/Developer/CommandLineTools").exists():
                env["DEVELOPER_DIR"] = "/Library/Developer/CommandLineTools"

            cmd = [
                "clang", "-O2", "-Wall", "-Werror",
                f"-I{ROOT / 'components/muse'}",
                str(harness_src),
                str(tts_c),
                "-lm",
                "-o", str(out_bin)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, env=env)
            self.assertEqual(res.returncode, 0, msg=f"Compile error:\n{res.stderr}")

            run_res = subprocess.run([str(out_bin)], capture_output=True, text=True, env=env)
            self.assertEqual(run_res.returncode, 0, msg=f"Run error:\n{run_res.stderr}")
            self.assertIn("ALL_TTS_TESTS_PASSED", run_res.stdout)

    def test_settings_exports_tts(self):
        """Verify muse_settings.h has MUSE_SETTING_TTS and getter/setter."""
        hdr = (ROOT / "components/muse/muse_settings.h").read_text()
        self.assertIn("MUSE_SETTING_TTS", hdr)
        self.assertIn("muse_settings_tts_on", hdr)
        self.assertIn("muse_settings_set_tts_on", hdr)

    def test_kconfig_and_sdkconfig_tts_default(self):
        """Verify Kconfig and device sdkconfig define CONFIG_MUSE_FREE_TTS."""
        kconfig = (ROOT / "components/muse/Kconfig").read_text()
        self.assertIn("MUSE_FREE_TTS", kconfig)

        sdkconfig = (ROOT / "devices/sdkconfig.muse-bread-s3").read_text()
        self.assertIn("CONFIG_MUSE_FREE_TTS=y", sdkconfig)

    def test_serial_say_and_voice_speak(self):
        """Verify >say= command parsing in muse_input.c and muse_voice_speak_text integration."""
        input_c = (ROOT / "components/muse/muse_input.c").read_text()
        self.assertIn('!strncmp(line, "say=", 4)', input_c)
        self.assertIn("muse_voice_speak_text(text)", input_c)

        voice_h = (ROOT / "components/muse/muse_voice.h").read_text()
        self.assertIn("void muse_voice_speak_text(const char *text);", voice_h)

        voice_c = (ROOT / "components/muse/muse_voice.c").read_text()
        self.assertIn("void muse_voice_speak_text(const char *text)", voice_c)

    def test_kconfig_and_sdkconfig_tts_timeout_and_chunks(self):
        """Verify Kconfig and device sdkconfig define timeout and max chunks options."""
        kconfig = (ROOT / "components/muse/Kconfig").read_text()
        self.assertIn("MUSE_FREE_TTS_TIMEOUT_MS", kconfig)
        self.assertIn("MUSE_FREE_TTS_MAX_CHUNKS", kconfig)

        sdkconfig = (ROOT / "devices/sdkconfig.muse-bread-s3").read_text()
        self.assertIn("CONFIG_MUSE_FREE_TTS_TIMEOUT_MS=8000", sdkconfig)
        self.assertIn("CONFIG_MUSE_FREE_TTS_MAX_CHUNKS=12", sdkconfig)

    def test_barge_in_and_cancellation_wiring(self):
        """Verify muse_tts_cancel() is wired into user barge-in and session cancel."""
        voice_c = (ROOT / "components/muse/muse_voice.c").read_text()
        self.assertIn("muse_tts_cancel()", voice_c)

        chat_session_cpp = (ROOT / "components/muse/muse_chat_session.cpp").read_text()
        self.assertIn("muse_tts_cancel()", chat_session_cpp)

    def test_serial_diag_command(self):
        """Verify >diag command is parsed and outputs system diagnostics."""
        input_c = (ROOT / "components/muse/muse_input.c").read_text()
        self.assertIn('!strcmp(line, "diag")', input_c)
        self.assertIn('ram_free', input_c)
        self.assertIn('psram_free', input_c)
        self.assertIn('wifi_ssid', input_c)


if __name__ == "__main__":
    unittest.main()
