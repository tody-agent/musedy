# Copyright (c) Meta Platforms, Inc. and affiliates.
# SPDX-License-Identifier: Apache-2.0
"""Unit tests verifying Musedy S3 1.8" Landscape LCD (160x128) Display Configuration."""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class DisplayConfigTest(unittest.TestCase):
    """Test suite validating 1.8" landscape display setup and hardware contracts."""

    def test_st7735_header_exists_and_declares_init(self):
        """esp_lcd_panel_st7735.h must declare esp_lcd_new_panel_st7735."""
        h_file = REPO_ROOT / "components" / "muse" / "esp_lcd_panel_st7735.h"
        self.assertTrue(h_file.exists(), "esp_lcd_panel_st7735.h is missing")
        content = h_file.read_text(encoding="utf-8")
        self.assertIn("esp_lcd_new_panel_st7735", content)
        self.assertIn("1.8\" 128x160 TFT LCD", content)

    def test_st7735_driver_implements_panel_ops(self):
        """esp_lcd_panel_st7735.c must implement swap_xy, mirror, set_gap, and draw_bitmap."""
        c_file = REPO_ROOT / "components" / "muse" / "esp_lcd_panel_st7735.c"
        self.assertTrue(c_file.exists(), "esp_lcd_panel_st7735.c is missing")
        content = c_file.read_text(encoding="utf-8")
        self.assertIn("panel_st7735_swap_xy", content)
        self.assertIn("panel_st7735_mirror", content)
        self.assertIn("panel_st7735_set_gap", content)
        self.assertIn("panel_st7735_draw_bitmap", content)
        self.assertIn("ST7735 initialized successfully", content)

    def test_kconfig_defines_180_landscape(self):
        """Kconfig must define CONFIG_MUSE_DISPLAY_180_LANDSCAPE and gap options."""
        kconfig = REPO_ROOT / "components" / "muse" / "Kconfig"
        content = kconfig.read_text(encoding="utf-8")
        self.assertIn("config MUSE_DISPLAY_180_LANDSCAPE", content)
        self.assertIn("1.8\" 160x128 Landscape ST7735/ST7789", content)
        self.assertIn("config MUSE_DISPLAY_ST7735_X_GAP", content)
        self.assertIn("config MUSE_DISPLAY_ST7735_Y_GAP", content)

    def test_cmakelists_includes_st7735_driver(self):
        """CMakeLists.txt must include esp_lcd_panel_st7735.c for board_bread_s3."""
        cmake = REPO_ROOT / "components" / "muse" / "CMakeLists.txt"
        content = cmake.read_text(encoding="utf-8")
        self.assertIn("esp_lcd_panel_st7735.c", content)

    def test_board_bread_s3_landscape_resolution(self):
        """board_bread_s3.c must configure width 160, height 128, round=false in landscape."""
        board_file = REPO_ROOT / "components" / "muse" / "boards" / "board_bread_s3.c"
        content = board_file.read_text(encoding="utf-8")
        # Check landscape dimensions
        self.assertIn("#define LCD_WIDTH 160", content)
        self.assertIn("#define LCD_HEIGHT 128", content)
        self.assertIn("#define LCD_IS_ROUND false", content)
        self.assertIn("#define LCD_DIAGONAL 1.8f", content)
        # Check panel swap_xy for landscape
        self.assertIn("esp_lcd_panel_swap_xy(s_panel, true);", content)
        self.assertIn("esp_lcd_new_panel_st7735", content)

    def test_sdkconfig_defaults_to_180_landscape(self):
        """sdkconfig.muse-bread-s3 and sdkconfig.muse-computer-18 must enable 1.8 landscape."""
        cfg1 = REPO_ROOT / "devices" / "sdkconfig.muse-bread-s3"
        content1 = cfg1.read_text(encoding="utf-8")
        self.assertIn("CONFIG_MUSE_DISPLAY_180_LANDSCAPE=y", content1)

        cfg2 = REPO_ROOT / "devices" / "sdkconfig.muse-computer-18"
        self.assertTrue(cfg2.exists(), "sdkconfig.muse-computer-18 is missing")
        content2 = cfg2.read_text(encoding="utf-8")
        self.assertIn("CONFIG_MUSE_DISPLAY_180_LANDSCAPE=y", content2)

    def test_cad_files_exist_for_18_adapter(self):
        """Both SCAD and binary STL files must exist for the 1.8 landscape adapter."""
        scad_file = REPO_ROOT / "cad" / "musedy_computer_18_adapter.scad"
        self.assertTrue(scad_file.exists(), "musedy_computer_18_adapter.scad is missing")
        scad_content = scad_file.read_text(encoding="utf-8")
        self.assertIn("w_screen_view   = 35.5", scad_content)
        self.assertIn("h_screen_view   = 28.5", scad_content)

        stl_file = REPO_ROOT / "cad" / "stl" / "musedy_computer_18_adapter.stl"
        self.assertTrue(stl_file.exists(), "musedy_computer_18_adapter.stl is missing")
        self.assertGreater(stl_file.stat().st_size, 1000, "STL file size too small")


if __name__ == '__main__':
    unittest.main()
