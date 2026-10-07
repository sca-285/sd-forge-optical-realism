"""Optical Realism - UI and host hooks. The optics are in optical_realism_core.py."""

import os
import sys
import traceback
import zlib

import gradio as gr
from PIL import Image
from modules import devices, script_callbacks, scripts
from modules.ui_components import InputAccordion

EXTENSION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if EXTENSION_ROOT not in sys.path:
    sys.path.insert(0, EXTENSION_ROOT)

from optical_realism_core import apply_optical_realism, generate_depth_map, park_depth_pipe  # noqa: E402
from lib_or.blur import BLUR_AVAILABLE, apply_blur_effect  # noqa: E402
from lib_or.controls import (  # noqa: E402
    APERTURES, BY_NAME, GROUP_OF, INFOTEXT_KEY, NAMES, SETTINGS_ONLY, coerce, effective, from_infotext, is_noop,
    settings, to_infotext,
)
from lib_or.layout import (  # noqa: E402
    BLUR_BASIC, BLUR_GROUPS, DEPTH_CONTROLS, DEPTH_GUIDE, DEPTH_LAYER_CONTROLS, QUICK_START, TABS,
)
from lib_or.presets import CHOICES, CUSTOM, DESCRIPTIONS, NOT_IN_PRESETS, PRESETS  # noqa: E402
from lib_or.reference import reference_html  # noqa: E402
from lib_or.stamp import stamp_mask  # noqa: E402
from lib_or.depth_moge import is_moge  # noqa: E402
from lib_or import xyz  # noqa: E402

if not BLUR_AVAILABLE:
    print("[Optical Realism] blurgenerator is not installed; 'Extra blur effect' will do nothing.")

# Effect strengths that Intensity multiplies.
SCALED = ["lens_distortion", "chromatic_aberration", "field_curvature", "vignette",
          "bloom", "promist", "halation", "flare", "light_wrap", "haze", "lift_blacks",
          "grain", "highlight_rolloff", "flash", "dust", "scratches", "purple_fringe", "streak", "star",
          "rays", "tilt_blur", "vhs", "scanlines", "glitch"]
SCALED_INT = ["gaussian_amount", "lens_radius", "motion_size", "max_blur"]


def needs_depth(s):
    """Only these read the depth map; everything else skips the depth model."""
    return bool(
        s["en_dof"]
        or (s["en_atmos"] and (s["haze"] > 0 or s["lift_blacks"] > 0))
        or (s["en_light"] and (s["light_wrap"] > 0 or s["flash"] > 0 or s["rays"] > 0))
        or (s["en_blur"] and s["blur_depth"])
    )


def _image_seed(p, image):
    """The seed of the image being processed, so grain repeats.

    The hook is not told which image of the batch it has; the host appends each
    one to p.pixels_after_sampling just before calling it, so its length says.
    Falls back to a hash of the pixels, which is at least stable per image.
    """
    try:
        i = len(p.pixels_after_sampling) - 1
        if 0 <= i < len(p.seeds):
            return int(p.seeds[i])
    except Exception:
        pass
    return zlib.crc32(image.resize((32, 32)).tobytes())


def render(image, s, depth_map, seed=None):
    """Apply settings `s` to `image`. Split out of the hook so it can be tested."""
    on = s
    s = effective(s)
    k = s["strength"]
    v = {n: s[n] * k for n in SCALED}
    for n in SCALED_INT:
        v[n] = max(1, int(round(s[n] * k)))
    # On or off: Intensity does not dim the stamp.
    stamp = (stamp_mask(image.size, s["stamp_text"], s["stamp_format"], s["stamp_position"], s["stamp_size"])
             if s["date_stamp"] else None)

    result, warped_depth = apply_optical_realism(
        image=image,
        depth_map=depth_map,
        lens_distortion=v["lens_distortion"],
        field_curvature=min(v["field_curvature"], 1.0),
        chromatic_aberration=v["chromatic_aberration"],
        # Unticked -> Manual with zero intensity, which the core skips entirely.
        f_stop=s["aperture"] if on["en_dof"] else "Manual",
        dof_intensity=s["dof_amount"] if on["en_dof"] else 0.0,
        dof_auto_focus=s["auto_focus"],
        dof_sharpness_radius=s["dof_radius"],
        dof_focus_point=s["focus_point"],
        dof_scale=k,
        bokeh_shape=s["bokeh_shape"],
        bokeh_rim=s["bokeh_rim"],
        bokeh_swirl=s["bokeh_swirl"],
        tilt_blur=min(v["tilt_blur"], 1.5),
        tilt_position=s["tilt_position"],
        tilt_width=s["tilt_width"],
        tilt_angle=s["tilt_angle"],
        bloom_strength=v["bloom"],
        flare_strength=v["flare"],
        light_wrap_strength=v["light_wrap"],
        promist_strength=v["promist"],
        halation_strength=v["halation"],
        flash_strength=min(v["flash"], 1.5),
        flash_reach=s["flash_reach"],
        streak=min(v["streak"], 1.5),
        streak_hue=s["streak_hue"],
        star=min(v["star"], 1.5),
        star_points=s["star_points"],
        star_angle=s["star_angle"],
        star_length=s["star_length"],
        rays=min(v["rays"], 1.5),
        rays_length=s["rays_length"],
        rays_auto=s["rays_auto"],
        rays_x=s["rays_x"],
        rays_y=s["rays_y"],
        purple_fringe=min(v["purple_fringe"], 1.5),
        atmosphere_enabled=v["haze"] > 0 or v["lift_blacks"] > 0,
        haze_strength=min(v["haze"], 1.0),
        lift_blacks=min(v["lift_blacks"], 1.0),
        depth_offset=s["depth_offset"],
        haze_color=s["haze_color"],
        vignette_intensity=min(v["vignette"], 1.0),
        grain_power=v["grain"],
        grain_size=s["grain_size"],
        monochrome_grain=s["mono_grain"],
        highlight_rolloff=v["highlight_rolloff"],
        dust_amount=min(v["dust"], 1.5),
        scratches=min(v["scratches"], 1.0),
        stamp_mask=stamp,
        vhs=min(v["vhs"], 1.0),
        scanlines=min(v["scanlines"], 1.0),
        scan_pitch=s["scan_pitch"],
        glitch=min(v["glitch"], 1.5),
        scale_with_resolution=s["scale_with_resolution"],
        seed=seed,
    )

    if on["en_blur"] and BLUR_AVAILABLE:
        result = apply_blur_effect(
            image=result,
            # The warped map: lens distortion has already moved the picture.
            depth_map=warped_depth,
            blur_type=s["blur_type"],
            use_depth=s["blur_depth"],
            gaussian_amount=v["gaussian_amount"],
            gaussian_sigma=int(s["gaussian_sigma"]),
            lens_radius=v["lens_radius"],
            lens_components=int(s["lens_components"]),
            exposure_gamma=float(s["exposure_gamma"]),
            motion_size=v["motion_size"],
            motion_angle=int(s["motion_angle"]),
            num_layers=int(s["num_layers"]),
            min_blur=int(s["min_blur"]),
            max_blur=v["max_blur"],
        )
    return result


XYZ_ATTR = "_or_xyz"


def _register_xyz():
    xyz.register("OR", XYZ_ATTR, [
        ("Preset", str, "preset", lambda: list(PRESETS)),
        ("Intensity", float, "strength", None),
        ("Aperture", str, "aperture", lambda: list(APERTURES)),
        ("Bloom", float, "bloom", None),
        ("Halation", float, "halation", None),
        ("Grain", float, "grain", None),
        ("Flash", float, "flash", None),
        ("Haze", float, "haze", None),
        ("Bokeh shape", str, "bokeh_shape", lambda: list(BY_NAME["bokeh_shape"].choices)),
        ("Anamorphic streak", float, "streak", None),
        ("Star filter", float, "star", None),
        ("God rays", float, "rays", None),
        ("Tilt-shift blur", float, "tilt_blur", None),
        ("VHS", float, "vhs", None),
    ])


# Once the scripts are loaded, before the UI is built: the X/Y/Z plot reads its
# axis list when it builds its own panel.
script_callbacks.on_before_ui(_register_xyz)


class Script(scripts.Script):
    # Where the accordion sits among the other extensions' panels.
    sorting_priority = 150

    def title(self):
        return "Optical Realism"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        tab = "img2img" if is_img2img else "txt2img"
        comps = {}

        def add(name):
            visible = True
            if name == "moge_refine":
                # Created after the model picker, so a saved default is already in it.
                visible = is_moge(getattr(comps.get("depth_model"), "value", ""))
            comps[name] = self._component(BY_NAME[name], tab, visible)

        def add_all(names):
            # One control per line: side by side, the info texts overlapped.
            for n in names:
                add(n)

        with InputAccordion(False, label="Optical Realism", elem_id=f"or_enabled_{tab}") as enabled:
            # Depth map first, as in the original extension.
            add_all(DEPTH_CONTROLS)
            depth_image = gr.Image(label="Your depth map (white = near)", type="pil",
                                   height=200, visible=False, elem_id=f"or_depth_image_{tab}")
            gr.Markdown(DEPTH_GUIDE)

            with gr.Row():
                preset = gr.Dropdown(label="Camera preset", choices=CHOICES, value=CUSTOM,
                                     elem_id=f"or_preset_{tab}")
                reset = gr.Button("Reset", scale=0, min_width=100, elem_id=f"or_reset_{tab}")
            about = gr.Markdown("", elem_id=f"or_preset_about_{tab}")
            gr.HTML(reference_html(EXTENSION_ROOT, "or-ref", "Optical Realism camera presets"),
                    elem_id=f"or_preset_ref_{tab}")
            add("strength")
            gr.Markdown(QUICK_START)

            blur_groups = {}
            with gr.Tabs():
                for t in TABS:
                    with gr.Tab(t["title"]):
                        gr.Markdown(f"*{t['guide']}*")
                        add_all(t["basic"])
                        for title, names in t.get("accordions", []):
                            with gr.Accordion(title, open=False):
                                add_all(names)
                        if t.get("blur"):
                            add_all(BLUR_BASIC)
                            for btype, names in BLUR_GROUPS.items():
                                with gr.Group(visible=(btype == "Gaussian")) as grp:
                                    add_all(names)
                                blur_groups[btype] = grp
                            with gr.Accordion("Depth layers (depth-aware blur)", open=False,
                                              visible=True) as layers_group:
                                add_all(DEPTH_LAYER_CONTROLS)

        outputs = [comps[n] for n in NAMES]

        comps["auto_depth"].change(lambda a: gr.update(visible=not a),
                                   [comps["auto_depth"]], [depth_image])
        # The refine-steps slider only matters for MoGe-3 with Auto depth on.
        comps["depth_model"].change(lambda m: gr.update(visible=is_moge(m)),
                                    [comps["depth_model"]], [comps["moge_refine"]])

        def show_blur(btype, depth_aware):
            return ([gr.update(visible=(btype == b)) for b in BLUR_GROUPS]
                    + [gr.update(visible=bool(depth_aware))])

        blur_outputs = [blur_groups[b] for b in BLUR_GROUPS] + [layers_group]
        for trigger in (comps["blur_type"], comps["blur_depth"]):
            trigger.change(show_blur, [comps["blur_type"], comps["blur_depth"]], blur_outputs)

        def values_for(s):
            return [gr.update() if n in NOT_IN_PRESETS else gr.update(value=s[n]) for n in NAMES]

        def apply_preset(name):
            s = PRESETS.get(name)
            if not s:
                return [gr.update(value="")] + [gr.update() for _ in NAMES]
            return [gr.update(value=f"*{DESCRIPTIONS.get(name, '')}*")] + values_for(s)

        preset.change(apply_preset, [preset], [about] + outputs)
        reset.click(lambda: [gr.update(value=CUSTOM), gr.update(value="")]
                    + [gr.update(value=v) for v in settings().values()],
                    [], [preset, about] + outputs)

        def field(name):
            def get(params):
                s = from_infotext(params.get(INFOTEXT_KEY, ""))
                return None if s is None else s[name]
            return get

        self.infotext_fields = [(enabled, lambda d: INFOTEXT_KEY in d)]
        self.infotext_fields += [(comps[n], field(n)) for n in NAMES if n not in SETTINGS_ONLY]
        self.paste_field_names = [INFOTEXT_KEY]

        return [enabled, depth_image, *outputs]

    @staticmethod
    def _component(c, tab, visible=True):
        eid = f"or_{c.name}_{tab}"
        info = c.info or None
        if c.kind == "checkbox":
            return gr.Checkbox(label=c.label, value=c.default, elem_id=eid, info=info, visible=visible)
        if c.kind == "text":
            return gr.Textbox(label=c.label, value=c.default, elem_id=eid, info=info, visible=visible,
                              max_lines=1)
        if c.kind == "choice":
            return gr.Dropdown(label=c.label, choices=list(c.choices), value=c.default,
                               elem_id=eid, info=info, visible=visible)
        return gr.Slider(label=c.label, minimum=c.minimum, maximum=c.maximum, step=c.step,
                         value=c.default, elem_id=eid, info=info, visible=visible)

    # After the composite, so lens geometry, DOF and grain apply to the whole
    # picture, not to an inpaint crop.
    def postprocess_image_after_composite(self, p, pp, enabled, depth_image, *values):
        axis = xyz.overrides(p, XYZ_ATTR)
        if not (enabled or axis) or pp.image is None:
            return
        s = settings(dict(zip(NAMES, values)))
        if axis:
            s = xyz.merged(s, axis, coerce, BY_NAME, GROUP_OF, PRESETS, NOT_IN_PRESETS)
        if is_noop(s):
            return

        try:
            image = pp.image
            if needs_depth(s):
                if s["auto_depth"]:
                    depth_map = generate_depth_map(image, model_size=s["depth_model"],
                                                   refine_steps=s["moge_refine"])
                elif depth_image is not None:
                    depth_map = depth_image.convert("L")
                else:
                    print("[Optical Realism] Auto depth is off and no depth map was given; "
                          "depth effects skipped.")
                    s = settings(s, en_dof=False, en_atmos=False, light_wrap=0.0, flash=0.0,
                                 blur_depth=False)
                    # God rays still work on a flat map, only without the far-first weighting.
                    depth_map = Image.new("L", image.size, 128)
            else:
                # A flat map is inert for every path that reads one.
                depth_map = Image.new("L", image.size, 128)

            result = render(image, s, depth_map, seed=_image_seed(p, image))
        except Exception as exc:
            traceback.print_exc()
            print(f"[Optical Realism] Error, image left untouched: {exc}")
            return

        pp.image = result
        # Written only after the work succeeded.
        p.extra_generation_params[INFOTEXT_KEY] = to_infotext(s)

    def postprocess(self, p, processed, *args):
        # Once per job: park the depth model in system RAM, reused next job.
        park_depth_pipe()
        devices.torch_gc()
