"""Every Optical Realism control, declared once.

The UI, the presets and the PNG-info round trip all read this table. Each
section has an Enable box; an unticked section is ignored whatever its sliders
say, and a freshly ticked one starts from the original extension's values.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .stamp import FORMATS as STAMP_FORMATS, POSITIONS as STAMP_POSITIONS

APERTURES = ["f/1.2", "f/1.4", "f/1.8", "f/2.0", "f/2.8", "f/3.2", "f/4.0",
             "f/5.6", "f/6.3", "f/8.0", "f/11", "f/16", "f/22", "Manual"]
BLUR_TYPES = ["Gaussian", "Lens", "Motion"]
DEPTH_MODELS = ["Large (vitl)", "Base (vitb)", "Small (vits)",
                "MoGe-3 Large (vitl)", "MoGe-3 Giant (vitg)"]


@dataclass(frozen=True)
class Control:
    name: str
    label: str
    default: object
    minimum: float = 0.0
    maximum: float = 1.0
    step: float = 0.01
    kind: str = "slider"          # slider | int | checkbox | choice | text
    info: str = ""
    choices: tuple = field(default_factory=tuple)
    neutral: object = None   # value at which it does nothing; None = same as default


C = Control
CONTROLS = [
    C("strength", "Intensity", 1.0, 0.0, 2.0, 0.05,
      info="Scales every effect at once. 1 = as set, 0.5 = half, 2 = double."),
    # --- section switches (the starting values below are what a freshly
    #     ticked section applies, as in the original extension)
    C("en_lens", "Enable Camera & Lens", False, kind="checkbox"),
    C("en_dof", "Enable Depth of Field", False, kind="checkbox"),
    C("en_blur", "Enable Blur", False, kind="checkbox"),
    C("en_light", "Enable Optical Effects", False, kind="checkbox"),
    C("en_atmos", "Enable Atmosphere / Haze", False, kind="checkbox"),
    C("en_film", "Enable Film Emulation", False, kind="checkbox"),
    # --- lens
    C("lens_distortion", "Distortion", 0.005, -0.5, 0.5, 0.001, info="+ barrel (bulges out) / - pincushion",
      neutral=0.0),
    C("chromatic_aberration", "Chromatic aberration", 0.002, 0.0, 0.05, 0.001,
      info="Red/blue colour fringes towards the edges.", neutral=0.0),
    C("field_curvature", "Soft corners", 0.15, 0.0, 1.0, 0.01, info="Field curvature: corners drift out of focus.",
      neutral=0.0),
    C("vignette", "Vignette", 0.15, 0.0, 1.0, 0.01, info="Darker corners.", neutral=0.0),
    # --- focus
    C("aperture", "Aperture", "f/5.6", kind="choice", choices=tuple(APERTURES),
      info="Lower f-number = shallower focus, blurrier background."),
    C("auto_focus", "Auto focus", True, kind="checkbox", info="Focus on the nearest thing near the centre."),
    C("focus_point", "Manual focus depth", 0.70, 0.0, 1.0, 0.01, info="1 = nearest, 0 = farthest."),
    C("dof_amount", "Extra background blur", 0.0, 0.0, 1.0, 0.01,
      info="With an f-stop: added on top (0.5 = 50% more). With Manual: the blur amount itself."),
    C("dof_radius", "In-focus depth", 0.35, 0.0, 1.0, 0.01,
      info="How much depth around the focus stays sharp. 0.35 = the f-stop's own."),
    C("blur_type", "Blur type", "Gaussian", kind="choice", choices=tuple(BLUR_TYPES)),
    C("blur_depth", "Depth-aware (blur only the far parts)", True, kind="checkbox"),
    C("gaussian_amount", "Gaussian amount", 6, 1, 100, 1, kind="int"),
    C("gaussian_sigma", "Gaussian sigma (depth-aware)", 2, 1, 50, 1, kind="int"),
    C("lens_radius", "Bokeh radius", 2, 1, 50, 1, kind="int"),
    C("lens_components", "Bokeh components", 4, 1, 6, 1, kind="int"),
    C("exposure_gamma", "Bokeh highlight gamma", 1.2, 0.1, 5.0, 0.1),
    C("motion_size", "Motion length", 8, 1, 100, 1, kind="int"),
    C("motion_angle", "Motion angle", 0, 0, 360, 1, kind="int"),
    C("num_layers", "Depth layers", 10, 4, 30, 1, kind="int", info="More = smoother, slower."),
    C("min_blur", "Near blur", 1, 0, 20, 1, kind="int"),
    C("max_blur", "Far blur", 8, 1, 60, 1, kind="int"),
    # --- light & air
    C("bloom", "Bloom", 0.05, 0.0, 1.0, 0.01, info="Glow around the brightest highlights.", neutral=0.0),
    C("promist", "Pro-Mist", 0.05, 0.0, 1.0, 0.01, info="Soft diffusion filter: glow on bright areas, lower contrast.",
      neutral=0.0),
    C("halation", "Halation", 0.03, 0.0, 1.0, 0.01, info="Red-orange film glow around bright edges.", neutral=0.0),
    C("flare", "Lens flare / ghosts", 0.05, 0.0, 1.0, 0.01, neutral=0.0),
    C("light_wrap", "Light wrap", 0.08, 0.0, 1.0, 0.01, info="Background light spilling over the subject's edges.",
      neutral=0.0),
    C("flash", "Flash", 0.0, 0.0, 1.0, 0.01,
      info="On-camera flash: lights what is near, the background falls dark. Needs a depth map."),
    C("flash_reach", "Flash reach", 0.5, 0.0, 1.0, 0.01,
      info="How far the flash carries. 0 = only the nearest things, 1 = most of the scene."),
    C("haze", "Haze", 0.10, 0.0, 1.0, 0.01, info="Atmospheric fog that grows with distance.", neutral=0.0),
    C("lift_blacks", "Distance lift", 0.05, 0.0, 1.0, 0.01, info="Far shadows wash out to grey.", neutral=0.0),
    C("depth_offset", "Haze start", 0.25, -1.0, 1.0, 0.05, info="Higher pushes haze further back."),
    # --- film & sensor
    C("grain", "Grain", 0.015, 0.0, 0.5, 0.001, info="0.01-0.03 is subtle, 0.05+ is heavy.", neutral=0.0),
    C("grain_size", "Grain size", 1.0, 0.5, 3.0, 0.1, info="How coarse the grain is. 1 = one pixel."),
    C("mono_grain", "Monochrome grain", False, kind="checkbox"),
    C("highlight_rolloff", "Highlight roll-off", 0.10, 0.0, 1.0, 0.01,
      info="Compresses harsh digital whites like film does.", neutral=0.0),
    C("dust", "Dust", 0.0, 0.0, 1.0, 0.01, info="Specks on the film, light on dark areas. Same seed = same dust."),
    C("scratches", "Scratches", 0.0, 0.0, 1.0, 0.01, info="Fine vertical lines from the film gate."),
    C("date_stamp", "Date stamp", False, kind="checkbox", info="Orange LED date of a compact camera."),
    C("stamp_text", "Stamp text", "", kind="text",
      info="Digits and ' / . - : only. Empty = today's date in the format below."),
    C("stamp_format", "Stamp date format", STAMP_FORMATS[0], kind="choice", choices=tuple(STAMP_FORMATS)),
    C("stamp_position", "Stamp position", STAMP_POSITIONS[0], kind="choice", choices=tuple(STAMP_POSITIONS)),
    C("stamp_size", "Stamp size", 1.0, 0.5, 2.5, 0.05),
    # --- depth map & settings (not part of a look)
    C("auto_depth", "Auto depth map", True, kind="checkbox",
      info="Estimate depth with Depth Anything V2 or MoGe-3. Off = use the image below."),
    C("depth_model", "Depth model", "Large (vitl)", kind="choice", choices=tuple(DEPTH_MODELS),
      info="Depth Anything V2: Small / Base / Large. MoGe-3: cleaner edges and layers; Giant is the most "
           "accurate and the heaviest."),
    C("moge_refine", "MoGe-3 refine steps", 3, 0, 8, 1, kind="int",
      info="Sharpens edges such as hair and leaves. Needs flex_gemm on a CUDA GPU; 0 = off."),
    C("scale_with_resolution", "Scale effects with resolution", True, kind="checkbox",
      info="Keeps bloom/blur the same relative size at any resolution (1024px reference)."),
]

BY_NAME = {c.name: c for c in CONTROLS}
NAMES = [c.name for c in CONTROLS]
DEFAULTS = {c.name: c.default for c in CONTROLS}
NEUTRAL = {c.name: (c.default if c.neutral is None else c.neutral) for c in CONTROLS}
SETTINGS_ONLY = {"auto_depth", "depth_model", "moge_refine", "scale_with_resolution"}

# Each Enable box and the controls it switches.
GROUPS = {
    "en_lens": ["lens_distortion", "chromatic_aberration", "field_curvature", "vignette"],
    "en_dof": ["aperture", "auto_focus", "focus_point", "dof_amount", "dof_radius"],
    "en_blur": ["blur_type", "blur_depth", "gaussian_amount", "gaussian_sigma", "lens_radius",
                "lens_components", "exposure_gamma", "motion_size", "motion_angle",
                "num_layers", "min_blur", "max_blur"],
    "en_light": ["bloom", "promist", "halation", "flare", "light_wrap", "flash", "flash_reach"],
    "en_atmos": ["haze", "lift_blacks", "depth_offset"],
    "en_film": ["grain", "grain_size", "mono_grain", "highlight_rolloff", "dust", "scratches",
                "date_stamp", "stamp_text", "stamp_format", "stamp_position", "stamp_size"],
}
GROUP_OF = {n: g for g, names in GROUPS.items() for n in names}
# Written to PNG info only while the stamp is on.
STAMP_DETAILS = {"stamp_text", "stamp_format", "stamp_position", "stamp_size"}


def coerce(name, value):
    c = BY_NAME[name]
    if c.kind == "checkbox":
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)
    if c.kind == "choice":
        value = str(value)
        return value if value in c.choices else c.default
    if c.kind == "text":
        # PNG info is "k=v; k=v": keep the separators and quotes out.
        return "".join(ch for ch in str(value) if ch not in ';="\n').strip()[:24]
    v = min(max(float(value), c.minimum), c.maximum)
    return int(round(v)) if c.kind == "int" else v


def settings(values=None, **overrides):
    s = dict(DEFAULTS)
    for src in (values or {}), overrides:
        for k, v in src.items():
            if k in BY_NAME:
                s[k] = coerce(k, v)
    return s


def is_default(name, value):
    d = DEFAULTS[name]
    if isinstance(d, float):
        return abs(float(value) - d) < 1e-9
    return value == d


def effective(s):
    """What gets applied: unticked sections replaced by their neutral values."""
    out = dict(s)
    for en, names in GROUPS.items():
        if not s[en]:
            for n in names:
                out[n] = NEUTRAL[n]
    return out


def compose(values):
    """Settings from a partial dict (a preset, pasted PNG info): every section
    it mentions is ticked with its other controls at neutral; the rest stay
    unticked at their ordinary starting values."""
    s = dict(DEFAULTS)
    for en, names in GROUPS.items():
        if any(n in values for n in names):
            s[en] = True
            for n in names:
                s[n] = NEUTRAL[n]
    for k, v in values.items():
        if k in BY_NAME:
            s[k] = coerce(k, v)
    return s


def is_noop(s) -> bool:
    return s["strength"] <= 0 or not any(s[en] for en in GROUPS)


# ------------------------------------------------------------------ infotext

INFOTEXT_KEY = "Optical Realism"


def to_infotext(s) -> str:
    """Every value of every ticked section (the Enable boxes are implied), plus
    Intensity when it is not 1."""
    parts = []
    for c in CONTROLS:
        if c.name in SETTINGS_ONLY or c.name in GROUPS:
            continue
        g = GROUP_OF.get(c.name)
        if g is not None and not s[g]:
            continue
        if g is None and is_default(c.name, s[c.name]):
            continue
        if c.name in STAMP_DETAILS and not s["date_stamp"]:
            continue
        v = s[c.name]
        parts.append(f"{c.name}={v:g}" if isinstance(v, float) else f"{c.name}={v}")
    return "; ".join(parts) or "on"


_NUM = r"([-\d.]+)"
_LEGACY = [
    (rf"Geometry\(Dist:{_NUM} Curv:{_NUM} CA:{_NUM}\)",
     ("lens_distortion", "field_curvature", "chromatic_aberration")),
    (rf"DOF\((\S+) Int:{_NUM} Rad:{_NUM} Foc:(\S+?)\)", ("aperture", "dof_amount", "dof_radius", "focus")),
    (rf"Light\(Bloom:{_NUM} Flare:{_NUM} Wrap:{_NUM} PMist:{_NUM} Hal:{_NUM}\)",
     ("bloom", "flare", "light_wrap", "promist", "halation")),
    (rf"Atmos\(Haze:{_NUM} Lift:{_NUM} Off:{_NUM}\)", ("haze", "lift_blacks", "depth_offset")),
    (rf"Film\(Vig:{_NUM} Temp:{_NUM} Tint:{_NUM} Grain:{_NUM} Mono:(\w+) Roll:{_NUM}\)",
     # Temperature and tint moved to Digital Mastering; old values are dropped.
     ("vignette", None, None, "grain", "mono_grain", "highlight_rolloff")),
]


def from_infotext(text):
    """Settings from a PNG-info value (this format or the previous one), or None."""
    if not text:
        return None
    text = text.strip().strip('"')
    values = {}
    if "=" in text or text == "on":
        for part in text.split(";"):
            if "=" in part:
                k, v = (x.strip() for x in part.split("=", 1))
                if k in BY_NAME and k not in SETTINGS_ONLY and k not in GROUPS:
                    try:
                        values[k] = coerce(k, v)
                    except ValueError:
                        pass
        return compose(values)
    for pattern, names in _LEGACY:
        m = re.search(pattern, text)
        if not m:
            continue
        for k, v in zip(names, m.groups()):
            if k is None:
                continue
            if k == "focus":
                if v == "Auto":
                    values["auto_focus"] = True
                else:
                    values["auto_focus"] = False
                    try:
                        values["focus_point"] = coerce("focus_point", v)
                    except ValueError:
                        pass
                continue
            try:
                values[k] = coerce(k, v)
            except ValueError:
                pass
    return compose(values)
