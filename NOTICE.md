# Notice

This extension is adapted from
[ComfyUI-Optical-Realism](https://github.com/skatardude10/ComfyUI-Optical-Realism)
by skatardude10. At the time of writing, the original repository does not state
a licence, so no licence is granted here for the parts that follow it.

| File | Source |
|---|---|
| `optical_realism_core.py` | Lens, depth-of-field, light, atmosphere and film effects follow the original node; reworked for the WebUI (separable blurs, resolution scaling, seeded grain, warped depth for Extra blur). |
| `lib_or/blur.py` | Extra blur through [blurgenerator](https://pypi.org/project/blurgenerator/), as in the original node. |
| `scripts/optical_realism.py`, `lib_or/controls.py`, `lib_or/presets.py`, `lib_or/layout.py`, `lib_or/reference.py`, `style.css` | New: WebUI panel, control table, presets, PNG info and preset reference. |
| `preset_reference.jpg` | New. Rendered with this extension on scikit-image sample photos: Eileen Collins by NASA (public domain), coffee cup by Rachel Michetti (CC0), Falcon 9 launch by SpaceX (public domain). |

| `lib_or/moge/` | Vendored from [microsoft/MoGe](https://github.com/microsoft/MoGe) (MIT; `model/modules/dinov2/` by Meta AI, Apache-2.0). Licence texts in `lib_or/moge/LICENSE`, changes listed in `lib_or/moge/README.md`. |
| `lib_or/fx.py` | New: bokeh shapes, anamorphic streak, star filter, god rays, purple fringing, tilt-shift, retro video. |
| `lib_or/stamp.py` | New: seven-segment date stamp. Flash, dust and scratches in `optical_realism_core.py` are new too. |
| `lib_or/depth_moge.py` | New: loads MoGe-3 and turns its point map into a depth map. |

Depth maps come from [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2)
or [MoGe-3](https://github.com/microsoft/MoGe) (weights MIT), downloaded at run time
under their own licences. The optional MoGe-3 refiner uses
[FlexGEMM](https://github.com/JeffreyXiang/FlexGEMM) (MIT), installed separately.
