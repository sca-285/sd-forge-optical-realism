# Optical Realism

Makes a generated image look photographed: lens traits, depth of field, light
scatter, haze and film character. Applied to every image after the inpaint
composite. Works on Forge, reForge and Forge Classic (Neo).

Adapted from [ComfyUI-Optical-Realism](https://github.com/skatardude10/ComfyUI-Optical-Realism)
by skatardude10.

![Preset reference](preset_reference.jpg)

## Layout

```
[x] Optical Realism
    [x] Auto depth map  [Depth model v]  (MoGe-3 refine steps)  [x] Scale with resolution
    (your depth map, when Auto is off)
    Camera preset [..........v]  [Reset]
    one-line description of the preset
    [▦ Preset reference]             <- click to unfold the picture above
    Intensity  ----o-----            <- scales every effect; 0 = off, 2 = double
    [ Camera & Lens | Atmosphere | Depth of Field | Optical Effects | Film Emulation | Blur ]
      one-line hint
      [x] Enable ...                 <- one per tab
      the controls
```

Six tabs, each with its **Enable** box; a freshly ticked tab starts from the
original node's values. 14 camera presets; a preset ticks the tabs it uses and
unticks the rest, and never touches Intensity or the depth settings.

**Preset reference** unfolds a picture of every preset on three sample photos
(portrait, still life, night scene). Scroll inside the box, or click the
picture to open it full size in a new tab. Click the button again to fold it.

## Notes

- Depth of field, haze, light wrap and depth-aware blur read a depth map.
  Everything else runs without one. The depth model is parked in system RAM
  between jobs. Choose it under **Depth model**:

  | Model | Size | Notes |
  |---|---|---|
  | Depth Anything V2 Small / Base / Large | 25M / 98M / 335M | fast; Large is the default |
  | MoGe-3 Large (vitl) | 370M | cleaner subject edges and depth layers (about 1 GB VRAM) |
  | MoGe-3 Giant (vitg) | 1.25B | most accurate, heaviest (about 3 GB VRAM) |

  Or turn Auto off and upload your own map (white = near).
- **MoGe-3** ([Microsoft](https://github.com/microsoft/MoGe)) downloads from
  Hugging Face on first use, or put the checkpoint in `models/MoGe/` as
  `moge-3-vitl.pt` / `moge-3-vitg.pt`. Its model code ships with the extension,
  so nothing extra is installed. **MoGe-3 refine steps** (default 3, shown
  when a MoGe-3 model is picked) sharpen edges such as hair and leaves; they
  need the optional `flex_gemm` package and a CUDA GPU. Without it MoGe-3 runs
  with the refiner off and says so once in the console. To enable it, from the
  WebUI's Python environment:

  ```
  pip install triton-windows    # Windows only; pick the version that matches your torch
  pip install --no-deps git+https://github.com/JeffreyXiang/FlexGEMM.git
  ```
- Depth-aware Extra blur blurs the far parts and keeps the subject sharp.
- Bloom, flare, pro-mist, light-wrap and soft-corner blurs run as two 1-D
  passes, and a large depth-of-field disk runs at reduced resolution, so large
  images stay fast.
- Grain is seeded from the image's seed: the same seed gives the same grain.
- With Auto depth off and no map supplied, only the depth effects are skipped.
- *Extra blur* needs `blurgenerator` (installed by `install.py`).

## PNG info

One `Optical Realism` entry with the non-default values; Send to / Paste
restores it. The older `Geometry(...) | DOF(...)` format still pastes.

## Files

```
scripts/optical_realism.py   UI + host hooks
optical_realism_core.py      the optics (pure torch) and the depth model
lib_or/controls.py           every control, declared once (UI, presets, PNG info)
lib_or/presets.py            the 14 camera presets
lib_or/layout.py             tabs and guide texts
lib_or/blur.py               Extra blur via blurgenerator
lib_or/depth_moge.py         MoGe-3 depth maps
lib_or/moge/                 MoGe-3 model code (vendored, see its README)
lib_or/reference.py          the folded preset reference
preset_reference.jpg         the preset reference picture
style.css                    reference box
```

## Credits

- [ComfyUI-Optical-Realism](https://github.com/skatardude10/ComfyUI-Optical-Realism)
  by skatardude10, the node this extension is adapted from.
- [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2) and
  [MoGe-3](https://github.com/microsoft/MoGe) (Microsoft, MIT; DINOv2 by Meta AI,
  Apache-2.0) for depth maps; [FlexGEMM](https://github.com/JeffreyXiang/FlexGEMM)
  (MIT) for the optional MoGe-3 refiner;
  [blurgenerator](https://pypi.org/project/blurgenerator/) for Extra blur.
- Sample photos in `preset_reference.jpg`, from scikit-image's sample data:
  Eileen Collins by NASA (public domain), coffee cup by Rachel Michetti (CC0),
  Falcon 9 launch by SpaceX (public domain).

Thanks also to **Claude**, Anthropic's AI assistant, for help building this
extension.

## License

The original node does not state a licence yet, so none is given here for
now; see `NOTICE.md`.
