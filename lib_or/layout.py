"""Which control sits where, and the short guide text."""

# Top of the accordion, above the preset.
DEPTH_CONTROLS = ["auto_depth", "depth_model", "moge_refine", "scale_with_resolution"]
DEPTH_GUIDE = "*Depth map for depth of field, haze, light wrap, flash and god rays. Off = upload your own (white = near).*"

QUICK_START = "*Pick a preset or tick **Enable** in a tab. Intensity scales everything (0 = off).*"

# The six tabs, in the original order. Each starts with its Enable box.
TABS = [
    {
        "title": "Camera & Lens",
        "guide": "Distortion, colour fringes, soft and dark corners.",
        "basic": ["en_lens", "lens_distortion", "chromatic_aberration", "field_curvature", "vignette",
                  "purple_fringe"],
    },
    {
        "title": "Atmosphere",
        "guide": "Haze that grows with distance. Haze start: higher = only the far background.",
        "basic": ["en_atmos", "haze", "lift_blacks", "depth_offset", "haze_color"],
    },
    {
        "title": "Depth of Field",
        "guide": "f/1.2 = blurry background, f/5.6 = mostly sharp. Subject blurred? Use Manual focus.",
        "basic": ["en_dof", "aperture", "auto_focus", "focus_point", "dof_amount", "dof_radius",
                  "bokeh_shape", "bokeh_rim", "bokeh_swirl"],
        "accordions": [
            ("Tilt-shift (miniature)", ["en_tilt", "tilt_blur", "tilt_position", "tilt_width", "tilt_angle"]),
        ],
    },
    {
        "title": "Optical Effects",
        "guide": "Glow, flare and light from bright areas.",
        "basic": ["en_light", "bloom", "promist", "halation", "flare", "light_wrap", "flash", "flash_reach"],
        "accordions": [
            ("Anamorphic streak", ["streak", "streak_hue"]),
            ("Star filter", ["star", "star_points", "star_angle", "star_length"]),
            ("God rays", ["rays", "rays_length", "rays_auto", "rays_x", "rays_y"]),
        ],
    },
    {
        "title": "Film Emulation",
        "guide": "Grain, softer highlights, dust, scratches, date stamp.",
        "basic": ["en_film", "grain", "grain_size", "mono_grain", "highlight_rolloff",
                  "dust", "scratches"],
        "accordions": [
            ("Date stamp", ["date_stamp", "stamp_text", "stamp_format", "stamp_position", "stamp_size"]),
        ],
    },
    {
        "title": "Retro Video",
        "guide": "VHS smear, CRT scanlines, glitches. Applied last.",
        "basic": ["en_retro", "vhs", "scanlines", "scan_pitch", "glitch"],
    },
    {
        "title": "Blur",
        "guide": "Gaussian, lens or motion blur; depth-aware blurs only the far parts. Needs *blurgenerator*.",
        "basic": [],
        "blur": True,
    },
]

# The Blur tab.
BLUR_BASIC = ["en_blur", "blur_type", "blur_depth"]
BLUR_GROUPS = {
    "Gaussian": ["gaussian_amount", "gaussian_sigma"],
    "Lens": ["lens_radius", "lens_components", "exposure_gamma"],
    "Motion": ["motion_size", "motion_angle"],
}
DEPTH_LAYER_CONTROLS = ["num_layers", "min_blur", "max_blur"]
