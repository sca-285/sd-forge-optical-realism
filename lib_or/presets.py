"""Camera / lens looks. Each lists only what it changes. Picking one ticks the
Enable box of every section it uses (that section's other controls at neutral)
and unticks the rest, so presets never inherit leftovers. Intensity and the
depth-map settings are never touched by a preset.

Only what happens in front of and inside the camera: no colour grade. For
colour, pair a look here with a Digital Mastering preset (see README)."""

from .controls import compose

CUSTOM = "Custom"
NOT_IN_PRESETS = {"strength", "auto_depth", "depth_model", "moge_refine", "scale_with_resolution"}

_P = {
    "Subtle Real Camera": dict(
        lens_distortion=0.005, chromatic_aberration=0.001, vignette=0.10, halation=0.02,
        grain=0.010, highlight_rolloff=0.10),
    "Portrait 85mm f/1.8": dict(
        aperture="f/1.8", vignette=0.12, promist=0.03, grain=0.010, highlight_rolloff=0.15),
    "Portrait f/1.2 Dreamy": dict(
        aperture="f/1.2", promist=0.15, halation=0.06, bloom=0.12, vignette=0.15,
        highlight_rolloff=0.25),
    "Street 35mm f/5.6": dict(
        aperture="f/5.6", lens_distortion=0.010, chromatic_aberration=0.002, vignette=0.15,
        grain=0.020),
    "Macro Close-up": dict(
        aperture="f/1.4", dof_amount=0.5, dof_radius=0.12, vignette=0.10, highlight_rolloff=0.10),
    "Vintage Lens": dict(
        lens_distortion=0.030, field_curvature=0.35, chromatic_aberration=0.006, vignette=0.35,
        halation=0.08, grain=0.030),
    "Film Camera 35mm": dict(
        chromatic_aberration=0.002, vignette=0.20, halation=0.08,
        grain=0.040, highlight_rolloff=0.30),
    "Heavy Film Grain": dict(
        grain=0.080, grain_size=1.6, mono_grain=True, vignette=0.30, highlight_rolloff=0.20),
    "Pro-Mist Cinema": dict(
        promist=0.20, halation=0.10, bloom=0.10, vignette=0.15, highlight_rolloff=0.25),
    "Anamorphic Flare": dict(
        flare=0.25, bloom=0.15, halation=0.06, chromatic_aberration=0.003, vignette=0.20),
    "Night City Glow": dict(
        bloom=0.35, halation=0.12, promist=0.15, flare=0.10, grain=0.030),
    "Landscape Aerial Haze": dict(
        haze=0.35, lift_blacks=0.10, depth_offset=0.10, chromatic_aberration=0.001,
        highlight_rolloff=0.20),
    "Foggy Morning": dict(
        haze=0.60, lift_blacks=0.25, depth_offset=0.0, bloom=0.10, promist=0.10),
    "Backlit Rim Light": dict(
        light_wrap=0.25, bloom=0.10, halation=0.05, highlight_rolloff=0.15),
    "Dusty Night Film": dict(
        aperture="f/1.4", bloom=0.20, halation=0.18, promist=0.05, vignette=0.30,
        grain=0.035, dust=0.45, scratches=0.15, highlight_rolloff=0.20),
    "Digital Flash": dict(
        flash=0.70, flash_reach=0.45, lens_distortion=0.010, chromatic_aberration=0.002, vignette=0.12,
        grain=0.020),
    "Anamorphic Night": dict(
        aperture="f/1.8", bokeh_shape="Oval (anamorphic)", streak=0.55, bloom=0.15, halation=0.08,
        grain=0.020),
    "Star Filter Night": dict(
        star=0.60, star_points="6", bloom=0.10, halation=0.05, grain=0.015),
    "Cathedral Light": dict(
        rays=0.60, rays_length=0.6, haze=0.25, haze_color="Warm morning", bloom=0.08, promist=0.05),
    "Miniature World": dict(
        tilt_blur=0.70, tilt_position=0.55, tilt_width=0.18),
    "Swirly Vintage Portrait": dict(
        aperture="f/1.8", bokeh_swirl=0.90, field_curvature=0.30, vignette=0.30, purple_fringe=0.25,
        halation=0.05, grain=0.020),
    "Soap Bubble Bokeh": dict(
        aperture="f/1.8", bokeh_rim=0.90, bloom=0.10, vignette=0.15, grain=0.010),
    "VHS Home Video": dict(
        vhs=0.70, scanlines=0.20, glitch=0.10, highlight_rolloff=0.15),
    "CRT Screen": dict(
        vhs=0.25, scanlines=0.70, scan_pitch=4.0, bloom=0.10, lens_distortion=0.04, vignette=0.30),
    "Hexagon Night Bokeh": dict(
        aperture="f/1.4", bokeh_shape="Hexagon (6 blades)", bloom=0.20, halation=0.08, grain=0.020),
    "Glitch Art": dict(
        glitch=0.70, vhs=0.30, chromatic_aberration=0.020, lens_distortion=0.0),
    # Old glass on a film body, with the background eased off by a depth-aware
    # lens blur (the Blur tab, needs blurgenerator): far blur 2 and 4.
    "Retro Glass": dict(
        chromatic_aberration=0.006, grain=0.040, vignette=0.15, highlight_rolloff=0.20,
        blur_type="Lens", blur_depth=True, min_blur=0, max_blur=2),
    "Retro Glass Deep": dict(
        chromatic_aberration=0.006, grain=0.040, vignette=0.20, halation=0.06, highlight_rolloff=0.25,
        blur_type="Lens", blur_depth=True, min_blur=0, max_blur=4),
}

PRESETS = {name: compose(p) for name, p in _P.items()}
CHOICES = [CUSTOM, *PRESETS]

CATEGORIES = {
    "Subtle Real Camera": "Everyday", "Street 35mm f/5.6": "Everyday",
    "Portrait 85mm f/1.8": "Lens", "Portrait f/1.2 Dreamy": "Lens", "Macro Close-up": "Lens",
    "Vintage Lens": "Lens", "Swirly Vintage Portrait": "Lens", "Soap Bubble Bokeh": "Lens",
    "Hexagon Night Bokeh": "Lens", "Miniature World": "Lens",
    "Film Camera 35mm": "Film", "Heavy Film Grain": "Film", "Pro-Mist Cinema": "Film",
    "Dusty Night Film": "Film",
    "Anamorphic Flare": "Light", "Backlit Rim Light": "Light", "Cathedral Light": "Light",
    "Landscape Aerial Haze": "Light", "Foggy Morning": "Light",
    "Night City Glow": "Night", "Anamorphic Night": "Night", "Star Filter Night": "Night",
    "Digital Flash": "Night",
    "VHS Home Video": "Retro", "CRT Screen": "Retro", "Glitch Art": "Retro",
    "Retro Glass": "Film", "Retro Glass Deep": "Film",
}

DESCRIPTIONS = {
    "Subtle Real Camera": "Barely-there lens traits that take the 'too clean' CG edge off. Safe on anything.",
    "Portrait 85mm f/1.8": "Classic portrait lens: soft background, subject sharp. Needs a depth map (auto).",
    "Portrait f/1.2 Dreamy": "Very shallow focus with a soft glow; romantic portraits.",
    "Street 35mm f/5.6": "Everyday 35mm look: mild distortion and fringing, most of the scene in focus.",
    "Macro Close-up": "A paper-thin slice of focus, like shooting close to a small subject. Needs a depth map (auto).",
    "Vintage Lens": "Old glass: soft corners, colour fringing, heavy vignette, red glow.",
    "Film Camera 35mm": "Film camera feel: halation, grain, gentle highlight roll-off.",
    "Heavy Film Grain": "Strong, coarse monochrome grain and a heavy vignette; gritty, documentary.",
    "Pro-Mist Cinema": "Diffusion-filter glow on highlights, softer contrast; cinematic.",
    "Anamorphic Flare": "Lens ghosts and flare from bright lights, with bloom.",
    "Night City Glow": "Glowing lights and halation for night and neon scenes.",
    "Landscape Aerial Haze": "Distant hills fade into atmospheric haze. Needs a depth map (auto).",
    "Foggy Morning": "Thick fog that grows with distance, soft glow.",
    "Backlit Rim Light": "Background light wraps around the subject's edges; backlit look.",
    "Dusty Night Film": "Night on old film: big bokeh, glowing lights, dust and scratches. "
                        "Needs a depth map (auto).",
    "Digital Flash": "Compact camera flash: subject lit hard, background falls dark. Needs a depth map "
                     "(auto).",
    "Anamorphic Night": "Anamorphic lens at night: oval bokeh, blue horizontal streaks through the lights.",
    "Star Filter Night": "Cross-screen filter: six-point stars on every bright light.",
    "Cathedral Light": "Light shafts through warm haze, as through a high window. Needs a depth map (auto).",
    "Miniature World": "Tilt-shift: a thin band of focus, the rest blurred, so the scene looks like a model.",
    "Swirly Vintage Portrait": "Old Soviet lens: the background swirls, soft corners, purple fringes. Needs a depth map (auto).",
    "Soap Bubble Bokeh": "Bright-rimmed bokeh discs, like a Trioplan lens. Needs a depth map (auto).",
    "VHS Home Video": "Home tape: smeared colour, tracking band, faint scanlines, the odd glitch.",
    "CRT Screen": "Shot off an old TV: strong scanlines, bulging glass, dark corners.",
    "Hexagon Night Bokeh": "Stopped-down vintage lens at night: six-sided bokeh round every light.",
    "Glitch Art": "Torn, colour-split digital glitches over a soft tape picture.",
    "Retro Glass": "Colour fringes and film grain, the background softly lens-blurred by depth (far blur 2).",
    "Retro Glass Deep": "The same old glass with a stronger depth lens blur (far blur 4) and a little halation.",
}
