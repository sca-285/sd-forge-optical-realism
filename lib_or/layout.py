"""Which control sits where, and the short guide text."""

# Top of the accordion, above the preset.
DEPTH_CONTROLS = ["auto_depth", "depth_model", "moge_refine", "scale_with_resolution"]
DEPTH_GUIDE = ("*Depth map is used only by Depth of Field, Atmosphere, Light wrap and depth-aware Blur. "
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
        "basic": ["en_lens", "lens_distortion", "chromatic_aberration", "field_curvature", "vignette"],
    },
    {
        "title": "Atmosphere",
        "guide": "Fog and washed-out shadows that grow with distance. Haze start: higher = only the far "
                 "background.",
        "basic": ["en_atmos", "haze", "lift_blacks", "depth_offset"],
    },
    {
        "title": "Depth of Field",
        "guide": "f/1.2-2 = very blurry background, f/5.6+ = mostly sharp. If the subject blurs, turn "
                 "Auto focus off and raise Manual focus depth.",
        "basic": ["en_dof", "aperture", "auto_focus", "focus_point", "dof_amount", "dof_radius"],
    },
    {
        "title": "Optical Effects",
        "guide": "Glow and reflections from bright light. Pro-Mist = soft cinema glow; Light wrap suits "
                 "backlit shots.",
        "basic": ["en_light", "bloom", "promist", "halation", "flare", "light_wrap"],
    },
    {
        "title": "Film Emulation",
        "guide": "Colour temperature and tint, grain (same seed = same grain), softer highlights.",
        "basic": ["en_film", "temperature", "tint", "grain", "mono_grain", "highlight_rolloff"],
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
