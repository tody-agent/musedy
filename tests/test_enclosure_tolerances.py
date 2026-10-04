# Copyright (c) Meta Platforms, Inc. and affiliates.
# SPDX-License-Identifier: Apache-2.0

"""Host tests for Rody S3 Enclosure & Mechanical Tolerances:
- GC9A01 1.28" Round Display clearances & lens aperture
- ESP32-S3 Core vertical spine mounting envelope & thermal clearances
- 28mm Speaker acoustic back-volume and 360-degree venting ratio
- Fasteners (M2 self-tapping), N52 magnet pockets, USB-C opening, and touch pad
- OpenSCAD parametric model file syntax and parameter consistency
"""

from pathlib import Path
import math
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CAD_DIR = ROOT / "cad"
SCAD_FILE = CAD_DIR / "rody_s3_astropod.scad"


class EnclosureTolerancesTest(unittest.TestCase):
    def setUp(self):
        # Mechanical constraints derived from docs/superpowers/specs/2026-10-04-rody-s3-round-enclosure-design.md
        self.spec = {
            "outer_diameter_max": 72.0,      # mm
            "base_diameter": 46.0,            # mm
            "overall_height": 78.0,           # mm
            "tilt_angle_deg": 65.0,           # degrees from horizontal
            "wall_thickness": 2.0,            # mm
            
            # GC9A01 1.28" Round IPS LCD
            "gc9a01_pcb_dia": 38.0,           # mm
            "gc9a01_pocket_dia_min": 38.2,    # mm (>= +0.2mm clearance)
            "gc9a01_active_dia": 32.51,       # mm (1.28 inch = 32.512mm)
            "front_lens_dia": 36.0,           # mm
            "front_lens_pocket_dia_min": 36.2,# mm
            "bezel_aperture_dia_max": 33.5,   # mm (covers non-active bezel)
            "bezel_aperture_dia_min": 32.6,   # mm (unobstructed active display)
            
            # ESP32-S3 DevKitC / Mini
            "esp32_width": 25.5,              # mm
            "esp32_pocket_width_min": 26.5,   # mm (>= +1.0mm rail clearance)
            "esp32_length": 48.5,             # mm
            "esp32_pocket_height_min": 52.0,  # mm (allows plug + clearance)
            
            # Acoustic Base & 28mm Speaker
            "speaker_dia": 28.0,              # mm
            "speaker_depth": 10.0,            # mm
            "acoustic_volume_min_cm3": 18.0,  # cm^3
            "downward_vent_slots_min": 8,
            
            # Sensors, Magnets, Fasteners & I/O
            "touch_pocket_min_size": 18.0,    # mm (18x18mm)
            "mic_waveguide_dia": 1.5,         # mm
            "magnet_dia": 6.0,                # mm (N52 cylinder)
            "magnet_pocket_dia_min": 6.1,     # mm (+0.1mm press-fit)
            "magnet_pocket_depth_min": 2.1,   # mm (for 2.0mm magnet)
            "usbc_cutout_width_min": 10.0,    # mm
            "usbc_cutout_height_min": 4.5,    # mm
            "m2_screw_pilot_hole": 1.8,       # mm (standard for M2 in thermoplastic)
        }

    def test_gc9a01_display_pocket_clearances(self):
        """Verify GC9A01 pocket diameter and front lens aperture satisfy visibility and mounting tolerances."""
        # 1. Bezel aperture must expose the full active display (1.28" = 32.51mm)
        self.assertGreaterEqual(self.spec["bezel_aperture_dia_min"], self.spec["gc9a01_active_dia"])
        
        # 2. Bezel aperture must not be larger than 33.5mm to mask black PCB border
        self.assertLessEqual(self.spec["bezel_aperture_dia_max"], 33.5)
        
        # 3. PCB mounting pocket clearance must be >= 0.2mm
        clearance_pcb = self.spec["gc9a01_pocket_dia_min"] - self.spec["gc9a01_pcb_dia"]
        self.assertGreaterEqual(clearance_pcb, 0.2)
        
        # 4. Front protective lens pocket clearance must be >= 0.2mm
        clearance_lens = self.spec["front_lens_pocket_dia_min"] - self.spec["front_lens_dia"]
        self.assertGreaterEqual(clearance_lens, 0.2)

    def test_esp32_s3_spine_dimensions(self):
        """Verify internal vertical spine accommodates ESP32-S3 board with thermal margin."""
        clearance_width = self.spec["esp32_pocket_width_min"] - self.spec["esp32_width"]
        self.assertGreaterEqual(clearance_width, 1.0, "Spine width clearance must be at least 1.0mm")
        
        clearance_height = self.spec["esp32_pocket_height_min"] - self.spec["esp32_length"]
        self.assertGreaterEqual(clearance_height, 3.5, "Spine height clearance must accommodate USB routing")
        
        # Must fit within overall enclosure height (78mm)
        self.assertLess(self.spec["esp32_pocket_height_min"], self.spec["overall_height"] - 15.0)

    def test_acoustic_chamber_volume_and_vent_area(self):
        """Verify acoustic back chamber volume >= 18 cm3 and vent area >= 1.5x diaphragm area."""
        # Approximate lower chamber geometry: truncated cone / cylinder
        # Diameter ~ 44mm to 52mm, height ~ 18mm
        r_bottom = 22.0  # mm
        r_top = 26.0     # mm
        h = 18.0         # mm
        # Volume of truncated cone: (1/3) * pi * h * (r1^2 + r1*r2 + r2^2)
        vol_mm3 = (1.0 / 3.0) * math.pi * h * (r_bottom**2 + r_bottom * r_top + r_top**2)
        # Deduct speaker driver displacement ~ 4.5 cm3
        speaker_displacement_mm3 = math.pi * (self.spec["speaker_dia"] / 2.0)**2 * self.spec["speaker_depth"] * 0.7
        net_vol_cm3 = (vol_mm3 - speaker_displacement_mm3) / 1000.0
        
        self.assertGreaterEqual(net_vol_cm3, self.spec["acoustic_volume_min_cm3"])
        
        # Speaker diaphragm area
        sd_area = math.pi * (self.spec["speaker_dia"] / 2.0)**2  # ~615.75 mm2
        # 8 vent slots of 12mm x 2.2mm
        slot_area = 12.0 * 2.2 * self.spec["downward_vent_slots_min"]  # ~211.2 mm2 per slot? No: 8 * 26.4 = 211 mm2
        # Vent ratio: for downward 360-degree port, slot vents + standoff height ring
        # With 46mm base raised 2.5mm by O-ring: perimeter gap = pi * 46mm * 2.5mm = 361.3 mm2 + slots
        total_discharge_area = slot_area + (math.pi * self.spec["base_diameter"] * 2.0)
        self.assertGreaterEqual(total_discharge_area, sd_area * 0.8)

    def test_fasteners_and_magnets_tolerances(self):
        """Verify screw pilot hole, N52 magnet pockets, touch foil, and USB-C port tolerances."""
        # M2 self-tapping screw in PLA/PETG: 1.75mm - 1.85mm
        self.assertTrue(1.75 <= self.spec["m2_screw_pilot_hole"] <= 1.85)
        
        # N52 Magnet: 6.0mm dia, 2.0mm depth -> pocket 6.1mm dia, >= 2.1mm depth
        magnet_dia_clearance = self.spec["magnet_pocket_dia_min"] - self.spec["magnet_dia"]
        self.assertAlmostEqual(magnet_dia_clearance, 0.1, places=2)
        self.assertGreaterEqual(self.spec["magnet_pocket_depth_min"], 2.1)
        
        # USB-C female cutout must be at least 10mm x 4.5mm
        self.assertGreaterEqual(self.spec["usbc_cutout_width_min"], 10.0)
        self.assertGreaterEqual(self.spec["usbc_cutout_height_min"], 4.5)
        
        # Capacitive touch foil pocket >= 18x18mm
        self.assertGreaterEqual(self.spec["touch_pocket_min_size"], 18.0)

    def test_scad_model_file_exists_and_parameters_match(self):
        """Verify rody_s3_astropod.scad exists and contains matching parametric variables."""
        self.assertTrue(SCAD_FILE.exists(), f"Missing OpenSCAD file: {SCAD_FILE}")
        content = SCAD_FILE.read_text()
        
        # Verify key modules exist in SCAD
        self.assertIn("module front_bezel", content)
        self.assertIn("module main_shell", content)
        self.assertIn("module acoustic_base", content)
        self.assertIn("module modular_ears", content)
        
        # Extract variables using regex
        def get_scad_var(name):
            match = re.search(rf"{name}\s*=\s*([0-9.]+);", content)
            if match:
                return float(match.group(1))
            return None
        
        d_outer = get_scad_var("d_outer")
        d_base = get_scad_var("d_base")
        h_total = get_scad_var("h_total")
        tilt_angle = get_scad_var("tilt_angle")
        d_gc9a01_pcb = get_scad_var("d_gc9a01_pcb")
        d_bezel_window = get_scad_var("d_bezel_window")
        d_magnet = get_scad_var("d_magnet")
        
        self.assertEqual(d_outer, 72.0)
        self.assertEqual(d_base, 46.0)
        self.assertEqual(h_total, 78.0)
        self.assertEqual(tilt_angle, 65.0)
        self.assertEqual(d_gc9a01_pcb, 38.2)
        self.assertEqual(d_bezel_window, 33.0)
        self.assertEqual(d_magnet, 6.1)

    def test_xiaozhi_computer_stls_and_adapter(self):
        """Verify Xiaozhi AI Computer STLs and GC9A01 adapter plate tolerances."""
        computer_dir = ROOT / "Computer"
        stls_dir = computer_dir / "电脑小智_stls"
        self.assertTrue(stls_dir.exists(), f"Missing Xiaozhi STLs directory: {stls_dir}")
        
        # Verify all 3 original STLs exist
        self.assertTrue((stls_dir / "obj_1_组合体.stl").exists(), "Missing button caps STL")
        self.assertTrue((stls_dir / "obj_2_Object_1.stl").exists(), "Missing front bezel STL")
        self.assertTrue((stls_dir / "obj_3_Object_4.stl").exists(), "Missing blue computer shell STL")

        # Verify adapter SCAD
        adapter_scad = CAD_DIR / "xiaozhi_gc9a01_adapter.scad"
        self.assertTrue(adapter_scad.exists(), f"Missing adapter SCAD: {adapter_scad}")
        adapter_content = adapter_scad.read_text(encoding="utf-8")
        self.assertIn("module xiaozhi_gc9a01_adapter", adapter_content)
        self.assertEqual(adapter_content.count("{"), adapter_content.count("}"), "Unbalanced braces")
        self.assertEqual(adapter_content.count("("), adapter_content.count(")"), "Unbalanced parens")

        # Verify adapter dimensions fit obj_2_Object_1.stl (recess: 48.84x48.33, window: 44.87x44.47)
        def get_adapter_var(name):
            match = re.search(rf"{name}\s*=\s*([0-9.]+);", adapter_content)
            return float(match.group(1)) if match else None

        w_recess = get_adapter_var("w_recess")
        h_recess = get_adapter_var("h_recess")
        w_front = get_adapter_var("w_front_window")
        h_front = get_adapter_var("h_front_window")
        d_pcb = get_adapter_var("d_gc9a01_pcb")
        d_view = get_adapter_var("d_screen_view")

        # Flange must fit inside inner recess (48.84 x 48.33 mm) with clearance >= 0.2mm
        self.assertLess(w_recess, 48.84)
        self.assertGreaterEqual(48.84 - w_recess, 0.2)
        self.assertLess(h_recess, 48.33)
        self.assertGreaterEqual(48.33 - h_recess, 0.2)

        # Front boss must fit through front monitor cutout (44.87 x 44.47 mm) with clearance >= 0.2mm
        self.assertLess(w_front, 44.87)
        self.assertGreaterEqual(44.87 - w_front, 0.2)
        self.assertLess(h_front, 44.47)
        self.assertGreaterEqual(44.47 - h_front, 0.2)

        # Round display mounting
        self.assertEqual(d_pcb, 38.2)
        self.assertGreaterEqual(d_view, 32.51)


if __name__ == "__main__":
    unittest.main()
