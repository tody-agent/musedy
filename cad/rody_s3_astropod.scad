// ==============================================================================
// Rody S3 Round Edition - Astro-Pod & Modular Pet 3D CAD Model
// Design Spec: RODY-S3-ENC-V1
// License: Apache-2.0
// Description: Parametric OpenSCAD design for GC9A01 1.28" Round Display,
//              ESP32-S3 Core, 28mm Down-firing Speaker, INMP441, MPU6050,
//              Capacitive Touch, and Modular Magnetic Pet Ears.
// ==============================================================================

// Quality resolution
$fn = $preview ? 48 : 96;

// ------------------------------------------------------------------------------
// GLOBAL PARAMETERS (Dimensions in mm)
// ------------------------------------------------------------------------------
d_outer          = 72.0;   // Maximum spherical body diameter
d_base           = 46.0;   // Base contact ring diameter
h_total          = 78.0;   // Total height without ears
tilt_angle       = 65.0;   // Display tilt angle from horizontal (deg)
wall             = 2.0;    // Standard shell wall thickness

// Display & Lens (GC9A01 1.28" Round IPS LCD)
d_gc9a01_pcb     = 38.2;   // GC9A01 PCB pocket diameter (+0.2mm clearance)
h_gc9a01_pcb     = 2.8;    // Depth of PCB shelf
d_gc9a01_active  = 32.5;   // Active screen view diameter
d_bezel_window   = 33.0;   // Visible front bezel aperture
d_lens           = 36.2;   // Acrylic 2.5D protective lens pocket
h_lens           = 1.5;    // Lens thickness
d_mic_hole       = 1.5;    // INMP441 microphone acoustic waveguide hole

// Internal Spine (ESP32-S3 DevKitC / Mini)
w_esp32_spine    = 26.5;   // Width of board guide rails (+1.0mm margin)
h_esp32_spine    = 52.0;   // Height of board compartment
t_esp32_pcb      = 1.6;    // PCB thickness
rail_slot_w      = 2.0;    // Rail slot width for PCB slide-in

// Acoustic Chamber & Speaker (28mm 4Ω 3W)
d_speaker        = 28.2;   // Speaker mounting basket diameter
h_speaker        = 10.0;   // Speaker depth
d_oring_groove   = 42.0;   // Silicone O-ring groove diameter
w_oring_groove   = 2.5;    // O-ring groove width
h_oring_groove   = 1.2;    // O-ring groove depth
num_vent_slots   = 8;      // 360-degree downward firing acoustic slots
slot_width       = 2.5;    // Vent slot width
slot_length      = 10.0;   // Vent slot length

// Sensors, Magnets, Fasteners & I/O
d_magnet         = 6.1;    // N52 magnet cylinder pocket (+0.1mm press-fit)
h_magnet         = 2.2;    // N52 magnet pocket depth
w_touch_pocket   = 18.0;   // Top capacitive touch foil pocket width
l_touch_pocket   = 18.0;   // Top capacitive touch foil pocket length
t_touch_wall     = 1.2;    // Thin wall for high touch sensitivity
d_screw_pilot    = 1.8;    // M2 self-tapping screw pilot hole
d_screw_head     = 3.8;    // M2 countersunk head diameter
w_usbc           = 10.2;   // USB-C rear opening width
h_usbc           = 4.8;    // USB-C rear opening height

// Render selection: "all" (exploded view), "bezel", "shell", "base", "ears"
render_part      = "all";

// ------------------------------------------------------------------------------
// HELPER MODULES
// ------------------------------------------------------------------------------
module rounded_cylinder(r, h, r_corner) {
    rotate_extrude() {
        hull() {
            square([r - r_corner, h]);
            translate([r - r_corner, r_corner, 0])
                circle(r = r_corner);
            translate([r - r_corner, h - r_corner, 0])
                circle(r = r_corner);
        }
    }
}

// ------------------------------------------------------------------------------
// PART A: FRONT BEZEL (Holds GC9A01 LCD, Lens & Mic Waveguide)
// ------------------------------------------------------------------------------
module front_bezel() {
    color([0.22, 0.24, 0.27]) // Space Gray Metallic
    difference() {
        // Outer bezel ring
        cylinder(r = d_gc9a01_pcb/2 + 2.5, h = 4.5, center = false);
        
        // Chamfered front aperture (visible screen window)
        translate([0, 0, -0.1])
            cylinder(r = d_bezel_window/2, h = 2.0);
        
        // Acrylic lens pocket (diameter 36.2mm x 1.5mm)
        translate([0, 0, 1.2])
            cylinder(r = d_lens/2, h = h_lens + 0.2);
            
        // GC9A01 PCB pocket (diameter 38.2mm x 2.8mm)
        translate([0, 0, 2.5])
            cylinder(r = d_gc9a01_pcb/2, h = h_gc9a01_pcb + 1.0);
            
        // Microphone acoustic waveguide (at 6 o'clock position, tilted 45°)
        translate([0, -(d_bezel_window/2 + 1.2), 1.0])
            rotate([45, 0, 0])
                cylinder(r = d_mic_hole/2, h = 6.0, center = true);
                
        // 3x M2 mounting screw countersunk holes
        for (a = [60, 180, 300]) {
            rotate([0, 0, a])
                translate([d_gc9a01_pcb/2 + 1.2, 0, -0.1]) {
                    cylinder(r = d_screw_pilot/2, h = 6.0);
                    cylinder(r = d_screw_head/2, h = 1.8);
                }
        }
    }
}

// ------------------------------------------------------------------------------
// PART B: MAIN SHELL (Spherical Astro-Pod body, spine, touch pocket, ear magnets)
// ------------------------------------------------------------------------------
module main_shell() {
    color([0.92, 0.93, 0.95]) // Matte Ceramic White
    difference() {
        // Outer spherical capsule body
        union() {
            intersection() {
                // Sphere shape scaled to match 72mm diameter and 78mm height
                translate([0, 0, h_total/2])
                    scale([1.0, 1.0, h_total/d_outer])
                        sphere(r = d_outer/2);
                        
                // Truncate bottom at base level and top limit
                translate([0, 0, h_total/2])
                    cylinder(r = d_outer/2 + 5, h = h_total, center = true);
            }
        }
        
        // Hollow internal cavity (wall thickness = 2.0mm)
        translate([0, 0, h_total/2 + 2.0])
            scale([1.0, 1.0, (h_total - 2*wall)/(d_outer - 2*wall)])
                sphere(r = (d_outer - 2*wall)/2);
                
        // Base opening for mating with acoustic base
        translate([0, 0, -1])
            cylinder(r = d_base/2 - wall, h = 16.0);
            
        // Front face cutout angled at 65° for display bezel insertion
        // Pivot point set at front upper surface
        translate([0, 10.0, 42.0])
            rotate([-(90 - tilt_angle), 0, 0])
                translate([0, 0, 10.0])
                    cylinder(r = d_gc9a01_pcb/2 + 2.6, h = 25.0, center = true);

        // Rear USB-C female port cutout
        translate([0, -d_outer/2 + 4.0, 12.0])
            rotate([0, 0, 0])
                cube([w_usbc, 15.0, h_usbc], center = true);

        // Reset / Boot pinholes (1.2mm access pins)
        translate([-8.0, -d_outer/2 + 3.0, 18.0])
            rotate([90, 0, 0])
                cylinder(r = 0.7, h = 8.0, center = true);
        translate([8.0, -d_outer/2 + 3.0, 18.0])
            rotate([90, 0, 0])
                cylinder(r = 0.7, h = 8.0, center = true);

        // Dual top magnetic ear pockets (diameter 6.1mm x 2.2mm)
        for (side = [-1, 1]) {
            translate([side * 22.0, -2.0, h_total - 6.0])
                rotate([0, side * 30, 0])
                    cylinder(r = d_magnet/2, h = h_magnet + 0.5);
        }

        // Top capacitive touch sensor pocket (thin wall 1.2mm for high sensitivity)
        translate([0, -2.0, h_total - t_touch_wall - 1.0])
            cube([w_touch_pocket, l_touch_pocket, 2.0], center = true);
            
        // 4x Bottom M2 assembly screw holes
        for (a = [45, 135, 225, 315]) {
            rotate([0, 0, a])
                translate([d_base/2 - 3.5, 0, -0.5])
                    cylinder(r = d_screw_pilot/2, h = 10.0);
        }
    }

    // Internal vertical spine guide rails for ESP32-S3 PCB
    color([0.85, 0.85, 0.88])
    difference() {
        union() {
            // Left & right rail ribs
            for (side = [-1, 1]) {
                translate([side * (w_esp32_spine/2 + 1.2), -4.0, 36.0])
                    cube([2.4, 8.0, 38.0], center = true);
            }
        }
        // PCB sliding slot
        for (side = [-1, 1]) {
            translate([side * (w_esp32_spine/2), -4.0, 36.0])
                cube([rail_slot_w, t_esp32_pcb + 0.4, 40.0], center = true);
        }
    }
}

// ------------------------------------------------------------------------------
// PART C: ACOUSTIC BASE (28mm Speaker Sealed Chamber, MPU6050, 360° Grille, Halo)
// ------------------------------------------------------------------------------
module acoustic_base() {
    color([0.25, 0.26, 0.28]) // Dark Charcoal
    difference() {
        union() {
            // Main base cylinder mating with shell
            cylinder(r = d_base/2, h = 15.0);
            
            // Step ring locating into main shell inner diameter
            translate([0, 0, 15.0])
                cylinder(r = d_base/2 - wall - 0.2, h = 4.0);
        }
        
        // 28mm Speaker mounting cavity (sealed back chamber)
        translate([0, 0, 3.5])
            cylinder(r = d_speaker/2, h = h_speaker + 3.0);
            
        // Speaker sound opening downward
        translate([0, 0, -0.1])
            cylinder(r = (d_speaker - 4.0)/2, h = 4.0);

        // 8x 360-degree radial sound discharge slots at bottom
        for (i = [0 : num_vent_slots - 1]) {
            rotate([0, 0, i * (360 / num_vent_slots)])
                translate([d_base/2 - slot_length/2 - 1.0, 0, 1.2])
                    cube([slot_length, slot_width, 3.0], center = true);
        }

        // Silicone O-ring non-slip groove (dia 42mm x width 2.5mm x depth 1.2mm)
        translate([0, 0, -0.1])
            difference() {
                cylinder(r = (d_oring_groove + w_oring_groove)/2, h = h_oring_groove + 0.1);
                cylinder(r = (d_oring_groove - w_oring_groove)/2, h = h_oring_groove + 0.2);
            }

        // MPU6050 sensor center tray (square pocket 20.5mm x 16.0mm x 3.5mm)
        translate([0, 0, 11.5])
            cube([20.5, 16.0, 4.0], center = true);

        // Halo Ring light guide channel (translucent acrylic/resin channel)
        translate([0, 0, 1.5])
            difference() {
                cylinder(r = d_base/2 - 1.0, h = 3.0);
                cylinder(r = d_base/2 - 3.2, h = 3.2);
            }

        // 4x M2 pass-through countersunk holes matching main shell
        for (a = [45, 135, 225, 315]) {
            rotate([0, 0, a])
                translate([d_base/2 - 3.5, 0, -0.1]) {
                    cylinder(r = d_screw_pilot/2 + 0.3, h = 16.0);
                    cylinder(r = d_screw_head/2 + 0.2, h = 2.5);
                }
        }
    }
}

// ------------------------------------------------------------------------------
// PART D: MODULAR MECHA-CAT EARS (Pair of magnetic ears, Silicone/TPU)
// ------------------------------------------------------------------------------
module single_ear() {
    difference() {
        // Organic triangular mecha ear shape
        hull() {
            cylinder(r = 6.0, h = 3.0, center = true);
            translate([0, 4.0, 16.0])
                sphere(r = 2.2);
            translate([0, -6.0, 6.0])
                cylinder(r = 4.0, h = 2.0, center = true);
        }
        
        // Inner ear cavity accent
        translate([1.2, 0, 5.0])
            scale([0.8, 0.7, 0.8])
                hull() {
                    translate([0, 2.0, 9.0])
                        sphere(r = 1.5);
                    cylinder(r = 3.0, h = 2.0, center = true);
                }
                
        // N52 magnet pocket (diameter 6.1mm x 2.2mm)
        translate([0, 0, -1.6])
            cylinder(r = d_magnet/2, h = h_magnet + 0.2);
    }
}

module modular_ears() {
    color([0.35, 0.80, 0.75]) // Pastel Cyberpunk Mint
    union() {
        // Left Ear
        translate([-22.0, -2.0, h_total - 4.0])
            rotate([0, -28, 10])
                single_ear();
                
        // Right Ear
        translate([22.0, -2.0, h_total - 4.0])
            rotate([0, 28, -10])
                mirror([1, 0, 0])
                    single_ear();
    }
}

// ------------------------------------------------------------------------------
// SCENE RENDER CONTROLLER
// ------------------------------------------------------------------------------
if (render_part == "bezel") {
    front_bezel();
} else if (render_part == "shell") {
    main_shell();
} else if (render_part == "base") {
    acoustic_base();
} else if (render_part == "ears") {
    modular_ears();
} else {
    // "all" - Assembled view with realistic positioning
    main_shell();
    
    // Front bezel mounted at 65° tilt
    translate([0, 10.0, 42.0])
        rotate([-(90 - tilt_angle), 0, 0])
            translate([0, 0, 21.0])
                front_bezel();
                
    // Acoustic base aligned at bottom
    translate([0, 0, 0])
        acoustic_base();
        
    // Modular ears attached to magnetic sockets
    modular_ears();
}
