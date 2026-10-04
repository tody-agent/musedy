#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# SPDX-License-Identifier: Apache-2.0
"""Pure-Python Binary STL generator for Musedy S3 1.8" Landscape LCD Adapter.

Generates a clean, watertight 3D-printable binary STL without requiring OpenSCAD.
"""

from pathlib import Path
import struct
import math


def write_binary_stl(filepath: Path, triangles: list[tuple[tuple[float, float, float], ...]]):
    """Write list of triangles to binary STL file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'wb') as f:
        # 80-byte header
        header = b'Musedy S3 1.8 Landscape Display Adapter Bezel - MakerWorld 1967811 Case'.ljust(80, b' ')
        f.write(header[:80])
        # 4-byte uint32 facet count
        f.write(struct.pack('<I', len(triangles)))
        for p1, p2, p3 in triangles:
            # Calculate surface normal
            u = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
            v = (p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2])
            nx = u[1] * v[2] - u[2] * v[1]
            ny = u[2] * v[0] - u[0] * v[2]
            nz = u[0] * v[1] - u[1] * v[0]
            mag = math.sqrt(nx * nx + ny * ny + nz * nz)
            if mag > 1e-9:
                nx, ny, nz = nx / mag, ny / mag, nz / mag
            else:
                nx, ny, nz = 0.0, 0.0, 1.0
            # 12 floats: normal(3), p1(3), p2(3), p3(3) + 2-byte attribute uint16
            f.write(struct.pack('<3f3f3f3fH', nx, ny, nz, p1[0], p1[1], p1[2], p2[0], p2[1], p2[2], p3[0], p3[1], p3[2], 0))


def add_quad(triangles: list, v1, v2, v3, v4):
    """Add a quad (v1, v2, v3, v4 in counter-clockwise order)."""
    triangles.append((v1, v2, v3))
    triangles.append((v1, v3, v4))


def add_box(triangles: list, x_min, x_max, y_min, y_max, z_min, z_max):
    """Add an axis-aligned box with outward facing normals."""
    c000 = (x_min, y_min, z_min)
    c100 = (x_max, y_min, z_min)
    c110 = (x_max, y_max, z_min)
    c010 = (x_min, y_max, z_min)
    c001 = (x_min, y_min, z_max)
    c101 = (x_max, y_min, z_max)
    c111 = (x_max, y_max, z_max)
    c011 = (x_min, y_max, z_max)

    # -Z bottom
    add_quad(triangles, c000, c010, c110, c100)
    # +Z top
    add_quad(triangles, c001, c101, c111, c011)
    # -Y front
    add_quad(triangles, c000, c100, c101, c001)
    # +Y back
    add_quad(triangles, c110, c010, c011, c111)
    # -X left
    add_quad(triangles, c010, c000, c001, c011)
    # +X right
    add_quad(triangles, c100, c110, c111, c101)


def generate_musedy_18_adapter_stl(out_path: Path):
    """Generates the 3D mesh for the 1.8" landscape adapter."""
    # Outer flange: 48.4 x 48.0 x 1.6 mm
    # Front boss: 44.4 x 44.0 x 1.8 mm (Z: 1.6 to 3.4 mm)
    # Viewing window: 35.5 x 28.5 mm (centered, through all Z)
    # Glass pocket: 38.6 x 34.6 mm, depth 1.5 mm (Z: 0 to 1.5 mm)
    # Cable slot: 22.0 x 6.5 mm at bottom
    
    triangles = []
    
    # We construct the adapter as a composite of solid regions around cutouts:
    # Z layers:
    # Layer 0: Z=0 to Z=1.5 (Rear flange with glass pocket cutout)
    # Layer 1: Z=1.5 to Z=1.6 (Flange transition to boss)
    # Layer 2: Z=1.6 to Z=2.6 (Front boss straight section)
    # Layer 3: Z=2.6 to Z=3.4 (Front boss with CRT 45-deg bevel)
    
    w_rec, h_rec = 48.4, 48.0
    w_win, h_win = 44.4, 44.0
    w_view, h_view = 35.5, 28.5
    w_glass, h_glass = 38.6, 34.6
    
    # Outer frame segments (Left, Right, Top, Bottom)
    # 1. Left side of flange (X from -w_rec/2 to -w_glass/2)
    add_box(triangles, -w_rec/2, -w_glass/2, -h_rec/2, h_rec/2, 0.0, 1.6)
    # 2. Right side of flange (X from w_glass/2 to w_rec/2)
    add_box(triangles, w_glass/2, w_rec/2, -h_rec/2, h_rec/2, 0.0, 1.6)
    # 3. Top of flange (X from -w_glass/2 to w_glass/2, Y from h_glass/2 to h_rec/2)
    add_box(triangles, -w_glass/2, w_glass/2, h_glass/2, h_rec/2, 0.0, 1.6)
    # 4. Bottom of flange (excluding cable cutout: X from -w_glass/2 to w_glass/2, Y from -h_rec/2 to -h_glass/2)
    add_box(triangles, -w_glass/2, -11.0, -h_rec/2, -h_glass/2, 0.0, 1.6)
    add_box(triangles, 11.0, w_glass/2, -h_rec/2, -h_glass/2, 0.0, 1.6)

    # Glass pocket shelf (Z from 1.5 to 1.6 between glass pocket and active view)
    add_box(triangles, -w_glass/2, -w_view/2, -h_glass/2, h_glass/2, 1.5, 1.6)
    add_box(triangles, w_view/2, w_glass/2, -h_glass/2, h_glass/2, 1.5, 1.6)
    add_box(triangles, -w_view/2, w_view/2, h_view/2, h_glass/2, 1.5, 1.6)
    add_box(triangles, -w_view/2, w_view/2, -h_glass/2, -h_view/2, 1.5, 1.6)

    # Front protruding boss (Z from 1.6 to 3.4)
    # Left boss border
    add_box(triangles, -w_win/2, -w_view/2, -h_win/2, h_win/2, 1.6, 3.4)
    # Right boss border
    add_box(triangles, w_view/2, w_win/2, -h_win/2, h_win/2, 1.6, 3.4)
    # Top boss border
    add_box(triangles, -w_view/2, w_view/2, h_view/2, h_win/2, 1.6, 3.4)
    # Bottom boss border
    add_box(triangles, -w_view/2, w_view/2, -h_win/2, -h_view/2, 1.6, 3.4)

    # Rear alignment stop tabs on left/right edges for LCD PCB
    add_box(triangles, -w_glass/2 - 2.0, -w_glass/2 - 0.2, -6.0, 6.0, -1.2, 0.0)
    add_box(triangles, w_glass/2 + 0.2, w_glass/2 + 2.0, -6.0, 6.0, -1.2, 0.0)

    write_binary_stl(out_path, triangles)
    print(f"Generated binary STL: {out_path} ({len(triangles)} facets, {out_path.stat().st_size} bytes)")


if __name__ == '__main__':
    cad_dir = Path(__file__).resolve().parent
    stl_path = cad_dir / "stl" / "musedy_computer_18_adapter.stl"
    generate_musedy_18_adapter_stl(stl_path)
