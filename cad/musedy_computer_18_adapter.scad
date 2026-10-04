// ==============================================================================
// Musedy S3 AI Computer - 1.8" Landscape LCD (160x128) Adapter Bezel
// Designed for MakerWorld Model 1967811 (Xiaozhi AI Computer by 董老爺)
// License: Apache-2.0
// Description: Mounts a 1.8" TFT LCD (ST7735 / ST7789) in horizontal landscape
//              (160x128) orientation into the 44.87mm x 44.47mm monitor window
//              of obj_2_Object_1.stl (Front White Bezel).
// ==============================================================================

$fn = $preview ? 48 : 96;

// ------------------------------------------------------------------------------
// PARAMETERS
// ------------------------------------------------------------------------------
// Outer dimensions matching obj_2_Object_1.stl inner recess
w_recess        = 48.4;   // Width of inner shelf (-0.4mm tolerance)
h_recess        = 48.0;   // Height of inner shelf (-0.3mm tolerance)
t_flange        = 1.6;    // Rear seating flange thickness

// Raised front monitor boss protruding through front window (44.87 x 44.47 mm)
w_front_window  = 44.4;   // Width of front window (-0.4mm tolerance)
h_front_window  = 44.0;   // Height of front window (-0.4mm tolerance)
t_front_boss    = 1.8;    // Thickness of front bezel step
corner_radius   = 3.5;    // Monitor corner fillet radius

// 1.8" Landscape TFT LCD Dimensions (160x128 Landscape)
w_screen_view   = 35.5;   // Active view width in landscape (160px direction)
h_screen_view   = 28.5;   // Active view height in landscape (128px direction)
w_glass_pocket  = 38.6;   // Glass outline width
h_glass_pocket  = 34.6;   // Glass outline height
d_glass_pocket  = 1.5;    // Glass recess depth

// Retro CRT Screen Bevel
bevel_angle     = 45;     // Vintage CRT inner screen bevel
bevel_depth     = 0.8;    // Bevel inward chamfer depth

// Cable / Header Pass-Through
w_cable_slot    = 22.0;   // 8-pin SPI header / ribbon cutout width
h_cable_slot    = 6.5;    // Cutout height

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
// MAIN 1.8" LANDSCAPE ADAPTER MODULE
// ------------------------------------------------------------------------------
module musedy_computer_18_adapter() {
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
                    
            // Rear alignment corner guides for TFT module
            for (sx = [-1, 1]) {
                for (sy = [-1, 1]) {
                    translate([sx * (w_glass_pocket/2 + 1.2), sy * (h_glass_pocket/2 + 1.2), -1.2])
                        cylinder(r = 1.6, h = 1.2);
                }
            }
        }
        
        // Front CRT Bevel Window (160x128 landscape framing)
        translate([0, 0, t_flange + t_front_boss - bevel_depth])
            hull() {
                translate([0, 0, bevel_depth + 0.1])
                    rounded_rect_2d(w_screen_view + 2 * bevel_depth, h_screen_view + 2 * bevel_depth, 1.5);
                translate([0, 0, 0])
                    rounded_rect_2d(w_screen_view, h_screen_view, 1.2);
            }

        // Active screen window through-cutout
        translate([0, 0, -0.5])
            linear_extrude(height = t_flange + t_front_boss + 1.0)
                rounded_rect_2d(w_screen_view, h_screen_view, 1.2);

        // Rear TFT glass and polarizer pocket (38.6 x 34.6 mm)
        translate([0, 0, -0.1])
            linear_extrude(height = d_glass_pocket + 0.1)
                rounded_rect_2d(w_glass_pocket, h_glass_pocket, 1.0);

        // Cable / SPI pin header exit slot at bottom
        translate([0, -h_recess/2 + h_cable_slot/2, -0.1])
            cube([w_cable_slot, h_cable_slot + 2.0, t_flange + 1.0], center = true);
            
        // 4x Corner retention screw / snap notches
        for (sx = [-1, 1]) {
            for (sy = [-1, 1]) {
                translate([sx * (w_recess/2 - 2.5), sy * (h_recess/2 - 2.5), -0.5])
                    cylinder(r = 1.0, h = t_flange + t_front_boss + 1.0);
            }
        }
    }
}

// Render the 1.8" Landscape Adapter
musedy_computer_18_adapter();
