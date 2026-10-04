#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# SPDX-License-Identifier: Apache-2.0

"""Automated STL generator and CAD validator for Rody S3 Round Enclosure.
Extracts individual components from rody_s3_astropod.scad:
- front_bezel.stl: Space Gray front bezel for GC9A01 LCD and 2.5D lens
- main_shell.stl: Matte Ceramic White spherical body with internal spine
- acoustic_base.stl: Dark Charcoal bottom base with speaker chamber & 360-deg vents
- modular_ears.stl: Pair of detachable magnetic mecha-cat ears

Usage:
    python3 generate_stl.py [--output-dir stl] [--resolution 96]
"""

import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys

CAD_DIR = Path(__file__).resolve().parent
SCAD_FILE = CAD_DIR / "rody_s3_astropod.scad"

PARTS = [
    {
        "name": "front_bezel",
        "description": "Front bezel for GC9A01 1.28 IPS LCD & 36mm acrylic lens",
        "material": "Resin / PLA+ / CNC Anodized Aluminum",
        "color": "Space Gray Metallic",
        "orientation": "Flat front face down on build plate (Z=0)",
        "infill": "100%",
        "layer_height": "0.12mm (FDM) or 0.05mm (Resin)",
    },
    {
        "name": "main_shell",
        "description": "Spherical Astro-Pod body with ESP32-S3 spine & ear magnet sockets",
        "material": "PLA+ / PETG / ABS Matte",
        "color": "Matte Ceramic White",
        "orientation": "Base mating flange down, 65-deg display opening facing up",
        "infill": "25% Gyroid",
        "layer_height": "0.16mm (Tree supports enabled for internal overhangs)",
    },
    {
        "name": "acoustic_base",
        "description": "Sealed 28mm speaker chamber, MPU6050 tray, Halo ring channel & 360-deg vents",
        "material": "ABS / PETG (high mass damping)",
        "color": "Dark Charcoal",
        "orientation": "Bottom face down on build plate",
        "infill": "100% (Dense to prevent acoustic resonance)",
        "layer_height": "0.16mm",
    },
    {
        "name": "modular_ears",
        "description": "Pair of detachable mecha-cat ears with N52 6.1mm magnet pockets",
        "material": "Silicone molding or TPU 85A",
        "color": "Pastel Cyberpunk Mint",
        "orientation": "Magnet mating face flat on build plate",
        "infill": "20% Gyroid",
        "layer_height": "0.12mm",
    },
    {
        "name": "xiaozhi_gc9a01_adapter",
        "description": "Round-to-Square CRT Adapter Bezel for 1.28 GC9A01 LCD inside Xiaozhi Computer Case",
        "material": "Resin / PLA+ Matte",
        "color": "Vintage Computer Warm White",
        "orientation": "Rear flange flat on build plate",
        "infill": "100%",
        "layer_height": "0.12mm (FDM) or 0.05mm (Resin)",
        "file": "xiaozhi_gc9a01_adapter.scad",
    },
]


def find_openscad_binary() -> str | None:
    """Locate openscad executable across macOS, Linux, and Windows."""
    # Check PATH
    exe = shutil.which("openscad")
    if exe:
        return exe

    # macOS standard bundle paths
    mac_paths = [
        Path("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"),
        Path.home() / "Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD",
    ]
    for p in mac_paths:
        if p.exists() and p.is_file():
            return str(p)

    # Windows standard paths
    win_paths = [
        Path(r"C:\Program Files\OpenSCAD\openscad.exe"),
        Path(r"C:\Program Files (x86)\OpenSCAD\openscad.exe"),
    ]
    for p in win_paths:
        if p.exists() and p.is_file():
            return str(p)

    return None


def validate_scad_syntax(scad_path: Path) -> bool:
    """Validate CSG bracket pairing and module declarations."""
    content = scad_path.read_text(encoding="utf-8")
    
    # Check module definitions
    required_modules = ["front_bezel", "main_shell", "acoustic_base", "modular_ears"]
    missing = [m for m in required_modules if f"module {m}" not in content]
    if missing:
        print(f"[ERROR] Missing modules in SCAD file: {missing}", file=sys.stderr)
        return False
        
    # Check bracket balance
    open_curly = content.count("{")
    close_curly = content.count("}")
    if open_curly != close_curly:
        print(f"[ERROR] Curly brace mismatch: {{={open_curly}, }}={close_curly}", file=sys.stderr)
        return False

    open_paren = content.count("(")
    close_paren = content.count(")")
    if open_paren != close_paren:
        print(f"[ERROR] Parenthesis mismatch: (={open_paren}, )={close_paren}", file=sys.stderr)
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Export STLs from rody_s3_astropod.scad")
    parser.add_argument("--output-dir", default=str(CAD_DIR / "stl"), help="Output directory for STL files")
    parser.add_argument("--fn", type=int, default=96, help="Fragment resolution ($fn)")
    parser.add_argument("--validate-only", action="store_true", help="Only validate SCAD file syntax")
    args = parser.parse_args()

    print("=== Rody S3 Round Enclosure CAD & STL Pipeline ===")
    print(f"Target SCAD: {SCAD_FILE}")
    
    if not SCAD_FILE.exists():
        print(f"[FATAL] SCAD file not found: {SCAD_FILE}", file=sys.stderr)
        sys.exit(1)

    # Step 1: Validate syntax
    if not validate_scad_syntax(SCAD_FILE):
        print("[FATAL] SCAD syntax validation failed.", file=sys.stderr)
        sys.exit(1)
    print("✓ SCAD syntax and module structure validated successfully.")

    if args.validate_only:
        return

    # Step 2: Check OpenSCAD binary
    openscad_bin = find_openscad_binary()
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\nTarget Parts ({len(PARTS)} items):")
    for idx, part in enumerate(PARTS, 1):
        print(f"  {idx}. {part['name']}.stl: {part['description']}")
        print(f"     Material: {part['material']} | Color: {part['color']}")
        print(f"     Print: {part['orientation']} (Infill: {part['infill']}, Layer: {part['layer_height']})")

    if not openscad_bin:
        print("\n[NOTE] OpenSCAD binary is not installed on this host.")
        print("To generate STL files locally on your computer:")
        print("  1. Download OpenSCAD: https://openscad.org/downloads.html")
        print("  2. Run:")
        for part in PARTS:
            target_scad = CAD_DIR / part.get("file", SCAD_FILE.name)
            if "file" in part:
                print(f"     openscad -o stl/{part['name']}.stl -D '$fn={args.fn}' {target_scad.name}")
            else:
                name = part["name"].replace("front_", "").replace("main_", "").replace("acoustic_", "").replace("modular_", "")
                print(f"     openscad -o stl/{part['name']}.stl -D 'render_part=\"{name}\"' -D '$fn={args.fn}' {target_scad.name}")
        print("\nAlternatively, open the SCAD file in OpenSCAD GUI and press F6 (Render) -> F7 (Export STL).")
        return

    print(f"\nFound OpenSCAD: {openscad_bin}")
    print(f"Exporting STLs to: {output_path.resolve()} ($fn = {args.fn})...")

    for part in PARTS:
        name = part["name"]
        target_scad = CAD_DIR / part.get("file", SCAD_FILE.name)
        stl_file = output_path / f"{name}.stl"
        cmd = [openscad_bin, "-o", str(stl_file), "-D", f"$fn={args.fn}"]
        if "file" not in part:
            render_flag = name.replace("front_", "").replace("main_", "").replace("acoustic_", "").replace("modular_", "")
            cmd.extend(["-D", f'render_part="{render_flag}"'])
        cmd.append(str(target_scad))

        print(f"  Rendering [{name}.stl]...", end="", flush=True)
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            size_kb = stl_file.stat().st_size / 1024.0
            print(f" DONE ({size_kb:.1f} KB)")
        else:
            print(f" FAILED!\nError: {res.stderr}")


if __name__ == "__main__":
    main()
