# Stable Diffusion Optical Realism Adaption for Forge/reForge/Neo

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
    [All] [Everyday] [Lens] [Film] [Light] [Night] [Retro]   <- preset groups
    ‹ [icon] [icon] [icon] [icon] [icon] ... ›               <- preset carousel
    description of the picked preset          [Reset]
    [▦ Preset reference]             <- click to unfold the picture above
    Intensity  ----o-----            <- scales every effect; 0 = off, 2 = double
    [ Camera & Lens | Atmosphere | Depth of Field | Optical Effects | Film Emulation | Retro Video | Blur ]
      one-line hint
      [x] Enable ...                 <- one per tab
      the controls
```

Seven tabs, each with its **Enable** box (Depth of Field also holds Tilt-shift, with its own); a freshly ticked tab starts from the
original node's values. 28 camera presets in six groups; a preset ticks the tabs it uses and
unticks the rest, and never touches Intensity or the depth settings.

**Picking a preset**: a carousel of small icons, one per preset, each the preset on a sample picture with a short word mark and its group. The chips above it filter by group, the arrows (or a sideways scroll) move along, a click applies the preset. Hover a card for its description.

**Preset reference** unfolds a picture of every preset on three sample photos
(portrait, still life, night scene). Scroll inside the box, or click the
picture to open it full size in a new tab. Click the button again to fold it.

## Auto Color Corrector, Optical Realism and Digital Mastering

Three extensions split the work the way a photo is made, and run in this
order:

| 1. [Auto Color Corrector](https://github.com/sca-285/sd-forge-auto-color-corrector) | 2. [Optical Realism](https://github.com/sca-285/sd-forge-optical-realism) | 3. [Digital Mastering](https://github.com/sca-285/sd-webui-digital-mastering) |
|---|---|---|
| **Correction**, automatic: measures the image and fixes only what is off (colour cast, black and white points, exposure, flat or harsh contrast, dull colour, JPEG blocks, noise, a tilted horizon), or matches a reference picture | **The camera**: lens geometry, vignette, purple fringing, depth of field and bokeh, tilt-shift, blur, bloom, flare, anamorphic streak, star filter, god rays, halation, light wrap, flash, haze, grain, dust, scratches, date stamp, highlight roll-off, retro video | **The grade**, by hand or by preset: exposure, contrast, white balance, saturation, vibrance, split toning, CDL, LUT, selective colour, clarity, sharpen, overlays, HSL, colour wheels, tone curves, black & white, dehaze, skin smoothing, local light, subtitles, anti-banding |

No two of them do the same job. Auto Color Corrector and Digital Mastering
both touch exposure and white balance, but for opposite ends: the corrector
brings a faulty picture back to neutral by itself and leaves a sound one
alone; Digital Mastering moves a picture away from neutral, on purpose, by
the amount you set. Correct first, then shoot, then grade.

## Combining presets

Each extension's presets cover only its own side, so a finished look is one
preset from each, in the order they run: Auto Color Corrector cleans up, Optical
Realism adds the camera, Digital Mastering grades. Leave out any of the three
you do not need.

### Recipes

Complete looks, from the first extension to the last.

| Look | Auto Color Corrector | Optical Realism | Digital Mastering |
|---|---|---|---|
| Clean commercial portrait | Natural | Portrait 85mm f/1.8 | Portrait: Studio Skin |
| Fashion editorial | Natural | Retro Glass | Portrait: Editorial Crisp |
| Bridal, dreamy | Gentle | Portrait f/1.2 Dreamy | Portrait: Soft Glamour |
| Backlit at golden hour | Keep the Mood | Backlit Rim Light | Mood: Golden Hour |
| Contemporary film portrait | Natural | Retro Glass Deep | Film: Portra Golden |
| 35 mm travel snapshot | Natural | Film Camera 35mm | Film: Travel Ektar |
| Sixties holiday slide | Natural | Street 35mm f/5.6 | Film: Kodachrome |
| Hong Kong neon night | Keep the Mood | Night City Glow | Auteur: Chungking Neon |
| Lamp-lit interior, romance | Keep the Mood | Pro-Mist Cinema | Auteur: Mood for Love |
| Rainy city at night | Keep the Mood | Anamorphic Night | Auteur: Saigon Rain |
| Summer blockbuster | Standard | Anamorphic Flare | Cinema: Blockbuster |
| Neo-noir detective | Keep the Mood | Dusty Night Film | Cinema: Neo-Noir Blue |
| Classic black & white | Standard | Heavy Film Grain | B&W: Classic Silver |
| Mountain landscape | Standard | Landscape Aerial Haze | Film: Velvia |
| Misty northern coast | Keep the Mood | Foggy Morning | Auteur: Nordic Noir |
| Day for night | Natural | Subtle Real Camera | Cinema: Day for Night |
| House party | Natural | Digital Flash | Mood: Flash Snapshot |
| Nineties home video | Repair Only | VHS Home Video | Film: Instant Photo |
| Cyberpunk street | Keep the Mood | Hexagon Night Bokeh | Mood: Cyberpunk Neon |
| Toy town from above | Standard | Miniature World | Mood: Anime Vivid |
| Old photo brought back | Old Photo Scan | Vintage Lens | B&W: Sepia |
| Light in the nave | Keep the Mood | Cathedral Light | Film: Tungsten Amber |
| Christmas lights | Keep the Mood | Star Filter Night | Auteur: Happy Together |
| Garden storybook portrait | Gentle | Swirly Vintage Portrait | Auteur: Pastel Symmetry |
| Nature up close | Standard | Macro Close-up | Natural: HDR Detail |
| Digital breakdown | Repair Only | Glitch Art | Splash: Neon Blue |

### Partners for every camera

Every Optical Realism preset with the Digital Mastering looks that suit it
(the first one is the closest match) and the correction to run first. Every
Digital Mastering preset appears at least once.

| Optical Realism | Digital Mastering | Auto Color Corrector |
|---|---|---|
| Subtle Real Camera | Natural: Clean Polish · Natural: Crisp Clear · Film: Travel Ektar · Cinema: Day for Night | Natural |
| Portrait 85mm f/1.8 | Portrait: Studio Skin · Portrait: Golden Skin · Film: Portra Golden · Splash: Subject in Colour | Natural |
| Portrait f/1.2 Dreamy | Portrait: Soft Glamour · Mood: Lavender Dusk · Auteur: Pastel Symmetry · Film: Portra Golden | Gentle |
| Street 35mm f/5.6 | Natural: Vivid Pop · Film: Kodachrome · Auteur: Matte Street · Film: Cool Slide Stock · Splash: Golden Yellow · Splash: Red Accent | Standard |
| Macro Close-up | Natural: HDR Detail · Film: Emerald · Film: Velvia · Natural: Vivid Pop | Standard |
| Vintage Lens | Film: Faded Vintage · Film: Instant Photo · B&W: Sepia · Auteur: Hong Kong 90s | Gentle |
| Film Camera 35mm | Film: Portra Golden · Film: Olive Signature · Film: Kodachrome · Film: Travel Ektar · Auteur: Mood for Love | Natural |
| Heavy Film Grain | B&W: Classic Silver · B&W: Hard Noir · Film: Bleach Bypass · Auteur: Nordic Noir | Standard |
| Pro-Mist Cinema | Cinema: Teal & Orange · Auteur: Mood for Love · Auteur: 2046 · Auteur: Golden Anamorphic | Keep the Mood |
| Anamorphic Flare | Cinema: Blockbuster · Cinema: Desert Heat · Auteur: Golden Anamorphic · Cinema: Teal & Orange | Standard |
| Night City Glow | Auteur: Chungking Neon · Mood: Cyberpunk Neon · Film: Red Neon Night · Auteur: Saigon Rain | Keep the Mood |
| Landscape Aerial Haze | Film: Velvia · Mood: Golden Hour · Mood: Autumn Warmth · B&W: Infrared · Cinema: Day for Night | Standard |
| Foggy Morning | Natural: Soft Matte · Mood: Blue Hour · Auteur: Nordic Noir · Mood: Arctic Cold | Keep the Mood |
| Backlit Rim Light | Mood: Golden Hour · Portrait: Golden Skin · Auteur: Golden Anamorphic · Mood: Lavender Dusk | Keep the Mood |
| Dusty Night Film | Cinema: Dusty Night · Cinema: Neo-Noir Blue · Cinema: Moody Dark · Auteur: Fallen Angels | Keep the Mood |
| Digital Flash | Mood: Flash Snapshot · Film: Cross Process · Natural: Vivid Pop | Natural |
| Anamorphic Night | Cinema: Neo-Noir Blue · Auteur: Saigon Rain · Cinema: Digital Green · Auteur: 2046 | Keep the Mood |
| Star Filter Night | Auteur: Happy Together · Mood: Blue Hour · Film: Tungsten Amber | Keep the Mood |
| Cathedral Light | Film: Tungsten Amber · Cinema: Moody Dark · Auteur: Sickly Thriller · B&W: Classic Silver | Keep the Mood |
| Miniature World | Mood: Anime Vivid · Natural: Vivid Pop · Auteur: Pastel Symmetry · Film: Kodachrome | Standard |
| Swirly Vintage Portrait | Auteur: Pastel Symmetry · Film: Emerald · Film: Olive Signature · Mood: Autumn Warmth | Gentle |
| Soap Bubble Bokeh | Film: Velvia · Mood: Golden Hour · Portrait: Soft Glamour | Gentle |
| VHS Home Video | Film: Instant Photo · Film: Faded Vintage · Auteur: Hong Kong 90s | Repair Only |
| CRT Screen | Cinema: Digital Green · Mood: Cyberpunk Neon · B&W: Hard Noir | Repair Only |
| Hexagon Night Bokeh | Mood: Cyberpunk Neon · Auteur: Happy Together · Film: Red Neon Night · Auteur: Chungking Neon | Keep the Mood |
| Glitch Art | Splash: Neon Blue · Mood: Cyberpunk Neon · Cinema: Digital Green | Repair Only |
| Retro Glass | Portrait: Editorial Crisp · Film: Portra Golden · Auteur: Matte Street · Film: Faded Vintage | Natural |
| Retro Glass Deep | Film: Portra Golden · Auteur: Mood for Love · Film: Emerald · Portrait: Golden Skin | Natural |

Keep the Mood is the right correction for any picture whose colour or
darkness is the point (night, neon, candle light, fog); Repair Only for
looks that deliberately degrade the picture; Old Photo Scan for real scans.

## Lens character, filters and retro video

| Where | Effect | What it does |
|---|---|---|
| Camera & Lens | **Purple fringing** | A violet edge just outside very bright areas, as on fast or old lenses |
| Atmosphere | **Haze colour** | Blue-grey (as before), warm morning, white mist, smoke or dusk violet |
| Depth of Field | **Bokeh shape** | Round, oval (anamorphic: taller than wide) or hexagon (6 blades) |
| Depth of Field | **Bokeh rim** | Bright-edged discs, like a soap-bubble (Trioplan) lens |
| Depth of Field | **Swirl / cat-eye** | The background swirls round the centre, discs turn cat-eye at the edges (Helios) |
| Depth of Field | **Tilt-shift** | A band of focus with blur growing away from it: the miniature look |
| Optical Effects | **Anamorphic streak** | A long horizontal flare line through each bright light, blue by default |
| Optical Effects | **Star filter** | 4, 6 or 8-point rays from the brightest points (cross-screen filter) |
| Optical Effects | **God rays** | Light shafts from the strongest light, found automatically or placed by hand; far bright areas feed them most (uses the depth map) |
| Retro Video | **VHS** | Colour smeared and shifted against a softer picture, tape noise, tracking band |
| Retro Video | **CRT scanlines** | Scanlines, picture lifted to keep its brightness |
| Retro Video | **Glitch** | Torn slices and split colour; same seed, same glitch |

Retro video runs last, over everything else: the tape or the screen records the
finished picture. The streak, star filter and god rays are worked out at reduced
resolution, so large frames stay fast.

*Retro Glass* and *Retro Glass Deep* pair old-lens colour fringes (0.006) and
film grain (0.04) with the Blur tab's depth-aware lens blur, far blur 2 and 4:
the background eases off while the subject stays sharp. They need
*blurgenerator*, like the Blur tab.

## Notes

- Depth of field, haze, light wrap, flash, god rays and depth-aware blur read a depth map.
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
- Grain and dust are seeded from the image's seed: the same seed gives the
  same grain and the same specks.
- **Flash** (Optical Effects) is an on-camera flash: near things are lit, the
  background falls dark with distance. **Flash reach** sets how far it carries.
- **Dust** and **Scratches** (Film Emulation) print as light marks, most
  visible in dark areas.
- **Date stamp** (Film Emulation, folded under *Date stamp*) burns an orange
  LED date into a corner or along the left edge. Empty text = today's date in
  the chosen format; it draws digits and `' / . - :` only. Off by default, also
  in the *Digital Flash* preset. Intensity does not dim it.
- Temperature and tint moved to Digital Mastering; when an older image is
  pasted they are ignored. **Grain size** (Film Emulation) came the other way.
- With Auto depth off and no map supplied, only the depth effects are skipped.
- *Extra blur* needs `blurgenerator` (installed by `install.py`).

## X/Y/Z plot

Axes for the X/Y/Z plot script, under `[OR]`: Preset, Intensity, Aperture,
Bloom, Halation, Grain, Flash, Haze, Bokeh shape, Anamorphic streak, Star
filter, God rays, Tilt-shift blur, VHS. A cell that sets any of them switches the
extension on for that cell, and an axis ticks the tab it belongs to; a Preset
axis is applied first, then the other axes on top. Pair `[OR] Preset` with
Digital Mastering's `[DM] Preset` to compare camera and grade combinations.

## PNG info

One `Optical Realism` entry with the non-default values; Send to / Paste
restores it. The older `Geometry(...) | DOF(...)` format still pastes.

## Files

```
scripts/optical_realism.py   UI + host hooks
optical_realism_core.py      the optics (pure torch) and the depth model
lib_or/controls.py           every control, declared once (UI, presets, PNG info)
lib_or/presets.py            the 28 camera presets and their groups
lib_or/layout.py             tabs and guide texts
lib_or/blur.py               Extra blur via blurgenerator
lib_or/depth_moge.py         MoGe-3 depth maps
lib_or/moge/                 MoGe-3 model code (vendored, see its README)
lib_or/reference.py          the folded preset reference
lib_or/carousel.py           the preset carousel (HTML)
javascript/or_carousel.js    the preset carousel (clicks, filter, scroll)
preset_icons/                the preset icons, one picture per preset
lib_or/stamp.py              the seven-segment date stamp
lib_or/xyz.py                X/Y/Z plot axes
lib_or/fx.py                 bokeh shapes, streak, star filter, god rays, fringing, tilt-shift, retro video
preset_reference.jpg         the preset reference picture
style.css                    reference box, preset carousel
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
- Preset icons (`preset_icons/`): photos from the Open Images dataset, by Flickr
  photographers under CC BY 2.0 (each author and source listed in
  `preset_icons/CREDITS.md`), cropped, with the preset applied and lettering in
  Bebas Neue (SIL Open Font License 1.1; only the rendered pictures are shipped).

Thanks also to **Claude**, for help building this
extension.

## License

The original node does not state a licence yet, so none is given here for
now; see `NOTICE.md`.
