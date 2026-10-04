// ==============================================================================
// Xiaozhi AI Computer (电脑小智) - GC9A01 1.28" Round Display Adapter Plate
// Designed for MakerWorld Model 1967811 (Xiaozhi AI Computer by 董老爺)
// License: Apache-2.0
// Description: Snaps directly into the 44.87mm x 44.47mm rectangular monitor window
//              (and 48.8mm x 48.3mm back recess) of obj_2_Object_1.stl (White Front Bezel).
//              Allows mounting a 1.28" Round GC9A01 IPS LCD into the retro computer case.
// ==============================================================================

$fn = $preview ? 48 : 96;

// ------------------------------------------------------------------------------
// PARAMETERS
// ------------------------------------------------------------------------------
// Outer dimensions matching obj_2_Object_1.stl inner recess
w_recess        = 48.4;   // Width of inner shelf (-0.4mm tolerance)
h_recess        = 48.0;   // Height of inner shelf (-0.3mm tolerance)
t_flange        = 1.6;    // Rear seating flange thickness

// Raised front boss stepping through the front monitor window (44.87 x 44.47 mm)
w_front_window  = 44.4;   // Width of front window (-0.4mm tolerance)
h_front_window  = 44.0;   // Height of front window (-0.4mm tolerance)
t_front_boss    = 1.8;    // Thickness of front bezel step
corner_radius   = 3.5;    // Monitor corner fillet radius

// GC9A01 Round Display Dimensions
d_gc9a01_pcb    = 38.2;   // PCB pocket diameter (+0.2mm clearance)
h_gc9a01_pcb    = 2.8;    // Depth of PCB recess
d_screen_view   = 33.0;   // Visible active screen aperture (covers black borders)
d_lens_pocket   = 36.2;   // Acrylic 2.5D lens pocket
h_lens_pocket   = 1.2;    // Lens depth

// Cable pass-through slot for 8-pin flex / wires
w_cable_slot    = 18.0;   // Cable cutout width
h_cable_slot    = 6.0;    // Cable cutout height

// ------------------------------------------------------------------------------
// 2D Rounded Rectangle Helper
// ------------------------------------------------------------------------------
module rounded_rect_2d(w, h, r) {
    hull() {
        translate([-w/2 + r, -h/2 + r]) circle(r = r);
        translate([ w/2 - r, -h/2 + r]) circle(r = r);
        translate([ w/2 - r,  h/2 - r]) circle(r = r);
        translate([-w/2 + r,  h/2 - r]) circle(r = r);
    }
}

// ------------------------------------------------------------------------------
// MAIN ADAPTER MODULE
// ------------------------------------------------------------------------------
module xiaozhi_gc9a01_adapter() {
    color([0.94, 0.94, 0.92]) // Vintage Computer Warm White
    difference() {
        union() {
            // Rear seating flange resting against obj_2 inner frame
            linear_extrude(height = t_flange)
                rounded_rect_2d(w_recess, h_recess, corner_radius + 1.0);
                
            // Raised front monitor boss protruding through front window
            translate([0, 0, t_flange - 0.01])
                linear_extrude(height = t_front_boss)
                    rounded_rect_2d(w_front_window, h_front_window, corner_radius);
        }
        
        // Chamfered front circular aperture (CRT look)
        translate([0, 0, t_flange + t_front_boss - 0.5])
            cylinder(r1 = d_screen_view/2, r2 = d_screen_view/2 + 0.8, h = 1.0);

        // Through-hole for screen viewing
        translate([0, 0, -0.5])
            cylinder(r = d_screen_view/2, h = t_flange + t_front_boss + 1.0);
            
        // Front lens pocket (diameter 36.2mm x 1.2mm)
        translate([0, 0, t_flange + t_front_boss - h_lens_pocket])
            cylinder(r = d_lens_pocket/2, h = h_lens_pocket + 0.5);

        // Rear GC9A01 PCB pocket (diameter 38.2mm x 2.8mm)
        translate([0, 0, -0.1])
            cylinder(r = d_gc9a01_pcb/2, h = h_gc9a01_pcb);

        // FPC / ribbon cable exit slot at bottom
        translate([0, -h_recess/2 + h_cable_slot/2, -0.1])
            cube([w_cable_slot, h_cable_slot + 2.0, t_flange + 1.0], center = true);
            
        // 4x Corner retention screw / clip notches
        for (sx = [-1, 1]) {
            for (sy = [-1, 1]) {
                translate([sx * (w_recess/2 - 2.5), sy * (h_recess/2 - 2.5), -0.5])
                    cylinder(r = 1.0, h = t_flange + 2.0);
            }
        }
    }
}

// Render the adapter
xiaozhi_gc9a01_adapter();
