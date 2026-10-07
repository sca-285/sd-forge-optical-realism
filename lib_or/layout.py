"""Which control sits where, and the short guide text."""

# Top of the accordion, above the preset.
DEPTH_CONTROLS = ["auto_depth", "depth_model", "moge_refine", "scale_with_resolution"]
DEPTH_GUIDE = ("*Depth map is used only by Depth of Field, Atmosphere, Light wrap, Flash, God rays and depth-aware Blur. "
               "Auto = Depth Anything V2 (Small is fastest) or MoGe-3 (sharper subject edges). "
               "Off = upload your own: white near, black far.*")

QUICK_START = ("*Pick a preset, or tick **Enable** in a tab. "
               "Intensity scales everything (0 = off, 2 = double).*")

# The six tabs, in the original order. Each starts with its Enable box.
TABS = [
    {
        "title": "Camera & Lens",
        "guide": "Barrel/pincushion distortion, colour fringes, soft corners, dark corners. "
                 "Keep chromatic aberration under ~0.01.",
        "basic": ["en_lens", "lens_distortion", "chromatic_aberration", "field_curvature", "vignette",
                  "purple_fringe"],
    },
    {
        "title": "Atmosphere",
        "guide": "Fog and washed-out shadows that grow with distance. Haze start: higher = only the far "
                 "background.",
        "basic": ["en_atmos", "haze", "lift_blacks", "depth_offset", "haze_color"],
    },
    {
        "title": "Depth of Field",
        "guide": "f/1.2-2 = very blurry background, f/5.6+ = mostly sharp. If the subject blurs, turn "
                 "Auto focus off and raise Manual focus depth.",
        "basic": ["en_dof", "aperture", "auto_focus", "focus_point", "dof_amount", "dof_radius",
                  "bokeh_shape", "bokeh_rim", "bokeh_swirl"],
        "accordions": [
            ("Tilt-shift (miniature)", ["en_tilt", "tilt_blur", "tilt_position", "tilt_width", "tilt_angle"]),
        ],
    },
    {
        "title": "Optical Effects",
        "guide": "Glow and reflections from bright light. Pro-Mist = soft cinema glow; Light wrap suits "
                 "backlit shots; Flash = harsh on-camera flash, dark background.",
        "basic": ["en_light", "bloom", "promist", "halation", "flare", "light_wrap", "flash", "flash_reach"],
        "accordions": [
            ("Anamorphic streak", ["streak", "streak_hue"]),
            ("Star filter", ["star", "star_points", "star_angle", "star_length"]),
            ("God rays", ["rays", "rays_length", "rays_auto", "rays_x", "rays_y"]),
        ],
    },
    {
        "title": "Film Emulation",
        "guide": "Grain (same seed = same grain), softer highlights, dust, scratches and a date stamp. "
                 "Colour and white balance belong to a grading extension (Digital Mastering).",
        "basic": ["en_film", "grain", "grain_size", "mono_grain", "highlight_rolloff",
                  "dust", "scratches"],
        "accordions": [
            ("Date stamp", ["date_stamp", "stamp_text", "stamp_format", "stamp_position", "stamp_size"]),
        ],
    },
    {
        "title": "Retro Video",
        "guide": "The picture as a tape or a screen recorded it: VHS colour smear and tracking, CRT "
                 "scanlines, digital glitches. Applied last, over everything else.",
        "basic": ["en_retro", "vhs", "scanlines", "scan_pitch", "glitch"],
    },
    {
        "title": "Blur",
        "guide": "Gaussian = smooth, Lens = bokeh discs, Motion = streak. Depth-aware blurs the far parts "
                 "only. Needs *blurgenerator*.",
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
