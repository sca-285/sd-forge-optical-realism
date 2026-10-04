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
        aperture="f/1.2", promist=0.10, halation=0.05, bloom=0.08, vignette=0.15,
        highlight_rolloff=0.20),
    "Street 35mm f/5.6": dict(
        aperture="f/5.6", lens_distortion=0.010, chromatic_aberration=0.002, vignette=0.15,
        grain=0.020),
    "Macro Close-up": dict(
        aperture="f/2.0", dof_radius=0.20, vignette=0.10, highlight_rolloff=0.10),
    "Vintage Lens": dict(
        lens_distortion=0.030, field_curvature=0.35, chromatic_aberration=0.006, vignette=0.35,
        halation=0.08, grain=0.030),
    "Film Camera 35mm": dict(
        chromatic_aberration=0.002, vignette=0.20, halation=0.08,
        grain=0.040, highlight_rolloff=0.30),
    "Heavy Film Grain": dict(
        grain=0.060, mono_grain=True, vignette=0.20, highlight_rolloff=0.20),
    "Pro-Mist Cinema": dict(
        promist=0.20, halation=0.10, bloom=0.10, vignette=0.15, highlight_rolloff=0.25),
    "Anamorphic Flare": dict(
        flare=0.25, bloom=0.15, halation=0.06, chromatic_aberration=0.003, vignette=0.20),
    "Night City Glow": dict(
        bloom=0.25, flare=0.10, halation=0.10, promist=0.10, grain=0.030),
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
}

PRESETS = {name: compose(p) for name, p in _P.items()}
CHOICES = [CUSTOM, *PRESETS]

DESCRIPTIONS = {
    "Subtle Real Camera": "Barely-there lens traits that take the 'too clean' CG edge off. Safe on anything.",
    "Portrait 85mm f/1.8": "Classic portrait lens: soft background, subject sharp. Needs a depth map (auto).",
    "Portrait f/1.2 Dreamy": "Very shallow focus with a soft glow; romantic portraits.",
    "Street 35mm f/5.6": "Everyday 35mm look: mild distortion and fringing, most of the scene in focus.",
    "Macro Close-up": "Thin slice of focus, like shooting close to a small subject.",
    "Vintage Lens": "Old glass: soft corners, colour fringing, heavy vignette, red glow.",
    "Film Camera 35mm": "Film camera feel: halation, grain, gentle highlight roll-off.",
    "Heavy Film Grain": "Strong monochrome grain and vignette; gritty, documentary.",
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
}
