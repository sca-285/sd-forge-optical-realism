import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from modules import devices

# ============================================================
# Depth Anything V2 (via Transformers)
# ============================================================
_depth_pipe = None
_depth_pipe_name = None

def get_depth_pipe(model_size="vitl"):
    """Lazy-load Depth Anything V2 pipeline"""
    global _depth_pipe, _depth_pipe_name

    model_map = {
        "vitl": "depth-anything/Depth-Anything-V2-Large-hf",
        "vitb": "depth-anything/Depth-Anything-V2-Base-hf",
        "vits": "depth-anything/Depth-Anything-V2-Small-hf",
        "Large (vitl)": "depth-anything/Depth-Anything-V2-Large-hf",
        "Base (vitb)": "depth-anything/Depth-Anything-V2-Base-hf",
        "Small (vits)": "depth-anything/Depth-Anything-V2-Small-hf",
    }

    model_id = model_map.get(model_size, "depth-anything/Depth-Anything-V2-Large-hf")

    if _depth_pipe is None or _depth_pipe_name != model_id:
        from transformers import pipeline
        print(f"[Optical Realism] Loading Depth Anything V2: {model_id}")
        # fp16 on CUDA: Depth-Anything-V2-Large is ~1.3 GB in fp32 and it sits
        # next to the checkpoint for the whole session. Half of that is enough
        # for a depth map that gets quantised to 8 bits anyway.
        kwargs = {}
        if str(devices.device).startswith("cuda"):
            kwargs["torch_dtype"] = torch.float16
        _depth_pipe = pipeline(
            task="depth-estimation",
            model=model_id,
            device=str(devices.device),
            **kwargs
        )
        _depth_pipe_name = model_id
        print("[Optical Realism] Depth model loaded.")
    else:
        # Back from the CPU if park_depth_pipe() put it there after the last job.
        _depth_pipe.model.to(_depth_pipe.device)

    return _depth_pipe


def park_depth_pipe():
    """Move the depth model to system RAM between jobs.

    This frees the VRAM and brings the model back far faster than re-reading
    it from disk (1.3 GB for Large).
    """
    if _depth_pipe is not None:
        try:
            _depth_pipe.model.to("cpu")
        except Exception:
            pass
    from lib_or import depth_moge
    depth_moge.park()
    devices.torch_gc()


def unload_depth_pipe():
    """Drop the depth model completely (frees system RAM too)."""
    global _depth_pipe, _depth_pipe_name
    park_depth_pipe()
    _depth_pipe = None
    _depth_pipe_name = None
    from lib_or import depth_moge
    depth_moge.unload()
    devices.torch_gc()


def generate_depth_map(pil_image: Image.Image, model_size="vitl", refine_steps=3) -> Image.Image:
    if pil_image is None:
        return None

    from lib_or import depth_moge
    if depth_moge.is_moge(model_size):
        # One depth model in VRAM at a time.
        park_depth_pipe()
        return depth_moge.depth_map(pil_image, model_size, devices.device, refine_steps)
    depth_moge.park()

    pipe = get_depth_pipe(model_size)
    result = pipe(pil_image)
    depth = result["depth"]          # PIL Image (mode L)

    depth_np = np.array(depth).astype(np.float32)
    depth_np = (depth_np - depth_np.min()) / (depth_np.max() - depth_np.min() + 1e-8)

    depth_img = Image.fromarray((depth_np * 255).astype(np.uint8), mode="L")
    return depth_img


# ============================================================
# Optical Realism Core
# ============================================================

def pil_to_tensor(pil_img: Image.Image, device="cuda") -> torch.Tensor:
    """PIL → torch tensor BHWC float32 [0,1]"""
    img = np.array(pil_img).astype(np.float32) / 255.0
    if img.ndim == 2:
        img = np.stack([img] * 3, axis=-1)
    if img.shape[-1] == 4:
        img = img[..., :3]
    tensor = torch.from_numpy(img).unsqueeze(0).to(device)  # 1,H,W,3
    return tensor


def tensor_to_pil(tensor: torch.Tensor) -> Image.Image:
    """torch BHWC [0,1] → PIL"""
    tensor = tensor.detach().cpu().clamp(0, 1)
    # np.rint, not a bare cast: truncation biases every channel down half a level.
    img = np.rint(tensor[0].numpy() * 255.0).astype(np.uint8)
    return Image.fromarray(img)


_kernels = {}


def _gauss1d(ks, sigma, device):
    key = (ks, round(float(sigma), 4), str(device))
    k = _kernels.get(key)
    if k is None:
        x = torch.linspace(-(ks - 1) / 2, (ks - 1) / 2, ks, device=device)
        k = torch.exp(-0.5 * (x / sigma) ** 2)
        k = k / k.sum()
        _kernels[key] = k
    return k


def _blur(x, kernel_size, sigma):
    """torchvision's gaussian_blur, done as two 1-D passes.

    Same kernel, same reflect padding, same result - but a 63-tap bloom at
    2048px costs 2 x 127 taps per pixel instead of 127 x 127. The bloom,
    flare, light-wrap and pro-mist kernels grow with the frame, so this is
    where the time went on large images.
    """
    c = x.shape[1]
    k = _gauss1d(kernel_size, sigma, x.device).to(x.dtype)
    r = kernel_size // 2
    if kernel_size <= 7:
        # Small kernels: one 2-D pass is faster than two 1-D ones.
        k2 = torch.outer(k, k).view(1, 1, kernel_size, kernel_size).expand(c, 1, -1, -1)
        return F.conv2d(F.pad(x, (r, r, r, r), mode="reflect"), k2, groups=c)
    x = F.pad(x, (r, r, 0, 0), mode="reflect")
    x = F.conv2d(x, k.view(1, 1, 1, -1).expand(c, 1, 1, -1), groups=c)
    x = F.pad(x, (0, 0, r, r), mode="reflect")
    return F.conv2d(x, k.view(1, 1, -1, 1).expand(c, 1, -1, 1), groups=c)


def _disk_blur(x, radius):
    """Uniform disk (bokeh) blur. Large radii run at reduced resolution.

    A 101x101 disk at 2048px is ~10k taps per pixel per channel. Above a
    radius of 12 the image is pooled down, blurred with a proportionally
    smaller disk and scaled back up; the result is a blur either way, so the
    detail lost to the round trip was never going to survive it.
    """
    h, w = x.shape[-2:]
    factor = max(1, int(np.ceil(radius / 12)))
    small = F.avg_pool2d(x, factor, ceil_mode=True) if factor > 1 else x
    r = max(1, int(round(radius / factor)))
    yy, xx = torch.meshgrid(torch.arange(-r, r + 1, device=x.device),
                            torch.arange(-r, r + 1, device=x.device), indexing="ij")
    disk = (xx ** 2 + yy ** 2 <= r ** 2).to(x.dtype)
    disk = (disk / disk.sum()).view(1, 1, 2 * r + 1, 2 * r + 1).expand(x.shape[1], 1, -1, -1)
    out = F.conv2d(F.pad(small, (r, r, r, r), mode="replicate"), disk, groups=x.shape[1])
    if factor > 1:
        out = F.interpolate(out, size=(h, w), mode="bilinear", align_corners=False)
    return out


def _seeded(device, seed, salt):
    """A generator for one effect, so each repeats with the seed but none
    shares the grain's random stream."""
    if seed is None:
        return None
    gen = torch.Generator(device=device)
    gen.manual_seed((int(seed) * 1000003 + salt) & 0x7FFFFFFFFFFFFFFF)
    return gen


def _flash(img, depth, strength, reach):
    """A small flash on the camera: lights what is near, leaves the rest dark.

    Flash light falls off with the square of the distance, so with the exposure
    set for the subject the background sinks. depth is 1 = near. The light is
    a little cooler than tungsten ambient, strongest at the centre of the
    frame, and lifts the subject's shadows (it comes from the lens axis).
    """
    _, h, w, _ = img.shape
    # reach 0: only the nearest things are lit; 1: most of the scene.
    k = 6.0 - 5.0 * float(reach)
    lit = torch.clamp(depth, 0.0, 1.0) ** k
    y = torch.linspace(-1, 1, h, device=img.device).view(1, h, 1, 1)
    x = torch.linspace(-1, 1, w, device=img.device).view(1, 1, w, 1)
    lit = lit * (1.0 - 0.25 * torch.clamp((x ** 2 + y ** 2) / 2.0, 0.0, 1.0))

    lin = img ** 2.2
    # Exposure set for the flash: the ambient drops up to ~2.5 stops, and the
    # flash puts the nearest things back a little above where they were.
    cut = min(0.85, 1.1 * strength)
    gain = (1.0 - cut) + (cut + 0.5 * strength) * lit
    colour = torch.tensor([0.97, 1.0, 1.05], device=img.device).view(1, 1, 1, 3)
    lin = lin * gain * torch.lerp(torch.ones_like(colour), colour, lit * strength)
    lin = lin + 0.04 * strength * lit
    # Soft shoulder instead of a hard clip, so a lit face does not go flat white.
    knee = 0.8
    over = torch.clamp(lin - knee, min=0.0)
    lin = torch.where(lin > knee, knee + (1.0 - knee) * torch.tanh(over / (1.0 - knee)), lin)
    return torch.clamp(lin, 0.0, 1.0) ** (1.0 / 2.2)


def _dust(img, amount, scratches, res_scale, seed):
    """Dust specks and fine scratches on the negative: they print as light
    marks, most visible in the dark parts of the frame."""
    _, h, w, _ = img.shape
    device = img.device
    gen = _seeded(device, seed, 7)
    marks = torch.zeros(1, 1, h, w, device=device)
    s = max(res_scale, 0.25)

    if amount > 0:
        # Specks per megapixel; most are tiny, a few are big enough to see.
        n_total = int(amount * 900 * (h * w) / 1_048_576) + 1
        for radius, share in ((0.6, 0.70), (1.4, 0.22), (2.6, 0.08)):
            n = max(1, int(n_total * share))
            ys = torch.randint(0, h, (n,), generator=gen, device=device)
            xs = torch.randint(0, w, (n,), generator=gen, device=device)
            alpha = 0.35 + 0.65 * torch.rand(n, generator=gen, device=device)
            layer = torch.zeros(h * w, device=device)
            layer.scatter_reduce_(0, ys * w + xs, alpha, reduce="amax")
            layer = layer.view(1, 1, h, w)
            r = max(0, int(round(radius * s)))
            if r > 0:
                layer = F.max_pool2d(layer, 2 * r + 1, stride=1, padding=r)
                # Round off the square the pooling leaves.
                ks = 2 * r + 1
                layer = torch.clamp(_blur(layer, max(3, ks), max(0.6, r * 0.6)) * 1.6, 0.0, 1.0)
            marks = torch.maximum(marks, layer)
        marks = _blur(marks, 3, 0.6 * max(1.0, s))

    if scratches > 0:
        # Thin vertical lines from the film running through the gate.
        n = 1 + int(scratches * 6)
        col = torch.zeros(1, 1, h, w, device=device)
        rows = torch.arange(h, device=device).view(h, 1)
        for _ in range(n):
            x0 = int(torch.randint(0, w, (1,), generator=gen, device=device))
            y0 = int(torch.randint(0, h, (1,), generator=gen, device=device))
            length = int(h * (0.2 + 0.8 * float(torch.rand(1, generator=gen, device=device))))
            a = 0.25 + 0.5 * float(torch.rand(1, generator=gen, device=device))
            span = ((rows >= y0) & (rows < y0 + length)).float().view(h)
            col[0, 0, :, x0] = torch.maximum(col[0, 0, :, x0], span * a)
        width = max(1, int(round(0.8 * s)))
        if width > 1:
            col = F.max_pool2d(col, (1, 2 * (width // 2) + 1), stride=1, padding=(0, width // 2))
        marks = torch.maximum(marks, _blur(col, 3, 0.5) * scratches)

    m = torch.clamp(marks, 0.0, 1.0).permute(0, 2, 3, 1) * min(1.0, 0.5 + amount)
    tone = torch.tensor([1.0, 0.98, 0.95], device=device).view(1, 1, 1, 3)
    return 1.0 - (1.0 - img) * (1.0 - m * tone)


def _stamp(img, mask, res_scale):
    """The orange date, with the soft glow it gets from being burned into
    the emulsion."""
    _, h, w, _ = img.shape
    m = pil_to_tensor(mask.convert("L").resize((w, h)), img.device)[..., :1]
    m_p = m.permute(0, 3, 1, 2)
    core = _blur(m_p, 3, 0.7).permute(0, 2, 3, 1)
    ks = max(3, int(round(9 * max(res_scale, 0.5))) | 1)
    glow = _blur(m_p, ks, ks / 3.0).permute(0, 2, 3, 1)
    glow_c = torch.tensor([1.0, 0.42, 0.06], device=img.device).view(1, 1, 1, 3)
    core_c = torch.tensor([1.0, 0.66, 0.22], device=img.device).view(1, 1, 1, 3)
    light = torch.clamp(glow_c * glow * 0.7 + core_c * core * 0.95, 0.0, 1.0)
    return 1.0 - (1.0 - img) * (1.0 - light)


@torch.no_grad()
def apply_optical_realism(
    image: Image.Image,
    depth_map: Image.Image,
    # 1. Lens Geometry
    lens_distortion: float = 0.0,
    field_curvature: float = 0.0,
    chromatic_aberration: float = 0.0,
    # 2. Depth of Field
    f_stop: str = "Manual",
    dof_intensity: float = 0.0,
    dof_auto_focus: bool = True,
    dof_sharpness_radius: float = 0.35,
    dof_focus_point: float = 0.70,
    dof_scale: float = 1.0,
    # 3. Light Scatters
    bloom_strength: float = 0.0,
    flare_strength: float = 0.0,
    light_wrap_strength: float = 0.0,
    promist_strength: float = 0.0,
    halation_strength: float = 0.0,
    flash_strength: float = 0.0,
    flash_reach: float = 0.5,
    # 4. Atmosphere
    atmosphere_enabled: bool = False,
    haze_strength: float = 0.0,
    lift_blacks: float = 0.0,
    depth_offset: float = 0.0,
    # 5. Sensor & Film
    vignette_intensity: float = 0.0,
    color_temperature: float = 0.0,
    tint: float = 0.0,
    grain_power: float = 0.0,
    monochrome_grain: bool = False,
    highlight_rolloff: float = 0.0,
    dust_amount: float = 0.0,
    scratches: float = 0.0,
    stamp_mask: Image.Image = None,
    # 6. Framing
    scale_with_resolution: bool = True,
    seed: int = None,
):
    """Main Optical Realism processing function.

    Returns (image, warped_depth_map). The depth map comes back because lens
    distortion warps the picture, and a depth-aware blur applied afterwards has
    to be warped the same way or its layers drift apart from the image toward
    the frame edges.

    Both image and depth_map are PIL Images.
    """

    device = devices.device

    # Alpha is not an optical quantity; keep it aside and restore it at the end.
    alpha = image.getchannel("A") if image.mode == "RGBA" else None

    # --- 1. SETUP ---
    img_tensor = pil_to_tensor(image, device)          # 1,H,W,3
    img_tensor = torch.nan_to_num(img_tensor, nan=0.0, posinf=1.0, neginf=0.0)
    depth_tensor = pil_to_tensor(depth_map, device)    # 1,H,W,3

    b, h, w, c = img_tensor.shape

    # Every kernel below was tuned at roughly 1024px. Left in absolute pixels, a
    # 63px bloom is four times wider relative to a 512px frame than to a 2048px
    # one, so hires fix would change the look and not just the resolution.
    res_scale = (max(h, w) / 1024.0) if scale_with_resolution else 1.0

    def _k(base_kernel, base_sigma):
        """Kernel size (odd, >=3) and sigma for this frame size."""
        ks = int(round(base_kernel * res_scale))
        ks = max(3, ks + 1 - (ks % 2))
        return ks, max(0.1, base_sigma * res_scale)

    # Extract single channel depth
    depth = depth_tensor[..., 0]  # 1,H,W

    if depth.shape[1] != h or depth.shape[2] != w:
        depth = F.interpolate(
            depth.unsqueeze(1), size=(h, w), mode="bilinear", align_corners=False
        ).squeeze(1)

    # depth_offset belongs to the Atmosphere group only and is applied there,
    # so DOF focus and Light Wrap falloff do not move with it.
    depth_mask = torch.clamp(depth, 0.0, 1.0).unsqueeze(-1)  # 1,H,W,1
    final_image = img_tensor.clone()

    # --- 1b. ON-CAMERA FLASH ---
    # Light, not optics, so it comes first: everything after sees the lit scene.
    if flash_strength > 0:
        final_image = _flash(final_image, depth_mask, flash_strength, flash_reach)

    # --- 2. FIELD CURVATURE ---
    if field_curvature > 0:
        img_permuted = final_image.permute(0, 3, 1, 2)
        
        y_c = torch.linspace(-1, 1, h, device=device).view(h, 1)
        x_c = torch.linspace(-1, 1, w, device=device).view(1, w)
        radius_map = torch.sqrt(x_c**2 + y_c**2) / 1.41421356  # Normalize to ~0-1
        
        edge_mask = torch.clamp((radius_map - (1.0 - field_curvature)) * (2.0 / max(field_curvature, 0.01)), 0.0, 1.0)
        edge_mask = edge_mask.unsqueeze(0).unsqueeze(0) # 1,1,H,W
        
        kernel_size, sigma = _k(max(3.0, field_curvature * 31.0), field_curvature * 12.0)

        blurred_edges = _blur(img_permuted, kernel_size, max(1.0, sigma))
        
        img_permuted = torch.lerp(img_permuted, blurred_edges, edge_mask)
        final_image = img_permuted.permute(0, 2, 3, 1)
        
    # --- 3. LENS DISTORTION ---
    if abs(lens_distortion) > 1e-6:
        y = torch.linspace(-1, 1, h, device=device)
        x = torch.linspace(-1, 1, w, device=device)
        grid_y, grid_x = torch.meshgrid(y, x, indexing="ij")
        r2 = grid_x**2 + grid_y**2
        f = 1.0 + lens_distortion * r2
        grid = torch.stack((grid_x * f, grid_y * f), dim=-1).unsqueeze(0).repeat(b, 1, 1, 1)

        final_image = F.grid_sample(
            final_image.permute(0, 3, 1, 2), grid,
            mode="bilinear", padding_mode="reflection", align_corners=False
        ).permute(0, 2, 3, 1)

        depth_mask = F.grid_sample(
            depth_mask.permute(0, 3, 1, 2), grid,
            mode="bilinear", padding_mode="reflection", align_corners=False
        ).permute(0, 2, 3, 1)

    # --- 4. WHITE BALANCE (Color Temperature + Tint) ---
    if abs(color_temperature) > 1e-6 or abs(tint) > 1e-6:
        r_gain = 1.0 + (color_temperature * 0.15) + (tint * 0.1)
        g_gain = 1.0 - (tint * 0.15)
        b_gain = 1.0 - (color_temperature * 0.15) + (tint * 0.1)

        luma_preservation = (0.299 * r_gain + 0.587 * g_gain + 0.114 * b_gain)
        r_gain /= luma_preservation
        g_gain /= luma_preservation
        b_gain /= luma_preservation

        gains = torch.tensor([r_gain, g_gain, b_gain], device=device).view(1, 1, 1, 3)
        final_image = torch.clamp(final_image * gains, 0.0, 1.0)

    # --- 5. DEPTH OF FIELD ---
    if f_stop != "Manual":
        f_stop_map = {
            "f/1.2": {"intensity": 0.80, "radius": 0.05},
            "f/1.4": {"intensity": 0.60, "radius": 0.10},
            "f/1.8": {"intensity": 0.45, "radius": 0.15},
            "f/2.0": {"intensity": 0.40, "radius": 0.20},
            "f/2.8": {"intensity": 0.30, "radius": 0.30},
            "f/3.2": {"intensity": 0.26, "radius": 0.35},
            "f/4.0": {"intensity": 0.20, "radius": 0.45},
            "f/5.6": {"intensity": 0.10, "radius": 0.60},
            "f/6.3": {"intensity": 0.08, "radius": 0.65},
            "f/8.0": {"intensity": 0.05, "radius": 0.75},
            "f/11":  {"intensity": 0.02, "radius": 0.85},
            "f/16":  {"intensity": 0.00, "radius": 1.00},
            "f/22":  {"intensity": 0.00, "radius": 1.00},
        }
        if f_stop in f_stop_map:
            # Multiply, do not replace: the sliders are trims around the
            # aperture, with their own defaults (0.0 / 0.35) as the neutral
            # point, so they keep working with any f-stop.
            dof_intensity = f_stop_map[f_stop]["intensity"] * (1.0 + dof_intensity)
            dof_sharpness_radius = f_stop_map[f_stop]["radius"] * (dof_sharpness_radius / 0.35)

    # Intensity scales the blur after the aperture has set it.
    dof_intensity = dof_intensity * dof_scale

    if dof_intensity > 0:
        if dof_auto_focus:
            h_start, h_end = int(h * 0.2), int(h * 0.8)
            w_start, w_end = int(w * 0.2), int(w * 0.8)
            roi = depth_mask[:, h_start:h_end, w_start:w_end, :]
            roi_flat = roi.reshape(b, -1)
            target_focus = torch.quantile(roi_flat, 0.90, dim=1).view(b, 1, 1, 1)
        else:
            target_focus = torch.tensor(dof_focus_point, device=device).view(1, 1, 1, 1)

        radius = min(int(25 * res_scale), max(1, int(dof_intensity * 25.0 * res_scale)))
        blurred_img = _disk_blur(final_image.permute(0, 3, 1, 2), radius).permute(0, 2, 3, 1)

        dist_from_focus = torch.abs(depth_mask - target_focus)
        blur_mask = torch.clamp(dist_from_focus - dof_sharpness_radius, 0.0, 1.0)
        blur_mask = torch.clamp(blur_mask * 4.0, 0.0, 1.0)

        final_image = torch.lerp(final_image, blurred_img, blur_mask)

    # --- 6. ATMOSPHERIC HAZE & LIFT ---
    if atmosphere_enabled:
        atmos_depth = torch.clamp(depth_mask + depth_offset, 0.0, 1.0)
        distance_mask = torch.clamp(1.0 - atmos_depth, 0.0, 1.0)
        
        # A. Atmospheric Fog & Desaturation
        if haze_strength > 0:
            atmos_color = torch.tensor([0.17, 0.20, 0.26], device=device).view(1, 1, 1, 3)
            haze_mask = torch.pow(distance_mask, 1.55) * haze_strength
            final_image = torch.lerp(final_image, atmos_color, haze_mask)

            grayscale = (
                0.299 * final_image[..., 0:1] +
                0.587 * final_image[..., 1:2] +
                0.114 * final_image[..., 2:3]
            ).repeat(1, 1, 1, 3)
            final_image = torch.lerp(final_image, grayscale, haze_mask * 0.55)

        # B. Distance-Based Black Lift
        if lift_blacks > 0:
            local_lift = distance_mask * (lift_blacks * 0.5)
            
            final_image = final_image * (1.0 - local_lift) + local_lift

    # --- 7. LIGHT WRAP ---
    if light_wrap_strength > 0:
        img_permuted = final_image.permute(0, 3, 1, 2)
        _ks, _sg = _k(41, 16.0)
        bloom = _blur(img_permuted, _ks, _sg)
        bloom = bloom.permute(0, 2, 3, 1)

        wrap_mod = 0.40 + 0.60 * depth_mask
        final_image = torch.clamp(
            final_image + bloom * light_wrap_strength * wrap_mod,
            0.0, 1.0
        )

    # --- 8. CLASSIC BLOOM ---
    if bloom_strength > 0:
        img_permuted = final_image.permute(0, 3, 1, 2)
        luma = 0.299 * img_permuted[:, 0:1] + 0.587 * img_permuted[:, 1:2] + 0.114 * img_permuted[:, 2:3]

        bloom_mask = torch.clamp((luma - 0.8) * 5.0, 0.0, 1.0)
        bloom_source = img_permuted * bloom_mask

        _ks, _sg = _k(63, 25.0)
        bloom_blur = _blur(bloom_source, _ks, _sg)
        bloom_blur = bloom_blur.permute(0, 2, 3, 1)
        final_image = torch.clamp(final_image + bloom_blur * bloom_strength, 0.0, 1.0)

    # --- 9. PROCEDURAL FLARE / GHOSTING ---
    if flare_strength > 0:
        img_permuted = final_image.permute(0, 3, 1, 2)
        luma = 0.299 * img_permuted[:, 0:1] + 0.587 * img_permuted[:, 1:2] + 0.114 * img_permuted[:, 2:3]

        flare_mask = torch.clamp((luma - 0.85) * 10.0, 0.0, 1.0)
        flare_source = img_permuted * flare_mask

        ghost_cyan = torch.flip(flare_source, dims=[2, 3])
        _ks, _sg = _k(41, 15.0)
        ghost_cyan = _blur(ghost_cyan, _ks, _sg)
        tint_cyan = torch.tensor([0.1, 0.6, 0.9], device=device).view(1, 3, 1, 1)
        ghost_cyan = ghost_cyan * tint_cyan

        _ks, _sg = _k(61, 25.0)
        ghost_warm = _blur(flare_source, _ks, _sg)
        tint_warm = torch.tensor([0.9, 0.3, 0.5], device=device).view(1, 3, 1, 1)
        ghost_warm = ghost_warm * tint_warm

        combined_flare = (ghost_cyan + ghost_warm * 0.6).permute(0, 2, 3, 1)

        final_image = 1.0 - (1.0 - final_image) * (1.0 - torch.clamp(combined_flare * flare_strength, 0.0, 1.0))

    # --- 10. PRO-MIST ---
    if promist_strength > 0:
        img_permuted = final_image.permute(0, 3, 1, 2)
        luma = 0.299 * img_permuted[:, 0:1] + 0.587 * img_permuted[:, 1:2] + 0.114 * img_permuted[:, 2:3]
        high_mask = torch.clamp((luma - 0.4) * 2.0, 0.0, 1.0)
        promist_source = img_permuted * high_mask
        _ks, _sg = _k(43, 15.0)
        pm_bloom = _blur(promist_source, _ks, _sg)
        pm_bloom = pm_bloom.permute(0, 2, 3, 1)
        final_image = torch.clamp(final_image + pm_bloom * promist_strength, 0.0, 1.0)

    # --- 11. HALATION ---
    if halation_strength > 0:
        img_permuted = final_image.permute(0, 3, 1, 2)
        luma = 0.299 * img_permuted[:, 0:1] + 0.587 * img_permuted[:, 1:2] + 0.114 * img_permuted[:, 2:3]
        hal_mask = torch.clamp((luma - 0.6) * 2.5, 0.0, 1.0)
        # Only the red channel is ever used, so only the red channel is blurred.
        hal_source = img_permuted[:, 0:1] * hal_mask
        _ks, _sg = _k(31, 8.0)
        hal_blur = _blur(hal_source, _ks, _sg).permute(0, 2, 3, 1)
        red_halation = hal_blur * halation_strength
        r = final_image[..., 0:1] + red_halation
        final_image = torch.cat((r, final_image[..., 1:3]), dim=-1)
        final_image = torch.clamp(final_image, 0.0, 1.0)

    # --- 12. CHROMATIC ABERRATION ---
    if chromatic_aberration > 0:
        y = torch.linspace(-1, 1, h, device=device)
        x = torch.linspace(-1, 1, w, device=device)
        grid_y, grid_x = torch.meshgrid(y, x, indexing="ij")
        base_grid = torch.stack((grid_x, grid_y), dim=-1).unsqueeze(0).repeat(b, 1, 1, 1)

        scale_r = 1.0 / (1.0 + chromatic_aberration)
        scale_b = 1.0 / (1.0 - chromatic_aberration)

        grid_r = base_grid * scale_r
        r_channel = final_image.permute(0, 3, 1, 2)[:, 0:1]
        r_sampled = F.grid_sample(r_channel, grid_r, mode="bilinear", padding_mode="reflection", align_corners=False)

        grid_b = base_grid * scale_b
        b_channel = final_image.permute(0, 3, 1, 2)[:, 2:3]
        b_sampled = F.grid_sample(b_channel, grid_b, mode="bilinear", padding_mode="reflection", align_corners=False)

        final_image = torch.cat((
            r_sampled.permute(0, 2, 3, 1),
            final_image[..., 1:2],
            b_sampled.permute(0, 2, 3, 1)
        ), dim=-1)

    # --- 13. VIGNETTE ---
    if vignette_intensity > 0:
        y_coords = torch.linspace(-1, 1, h, device=device).view(h, 1)
        x_coords = torch.linspace(-1, 1, w, device=device).view(1, w)
        radius = torch.sqrt(x_coords**2 + y_coords**2)
        vignette_mask = 1.0 - (torch.clamp(radius - 0.4, 0, 1) * vignette_intensity)
        vignette_mask = vignette_mask.unsqueeze(0).unsqueeze(-1)
        final_image = final_image * vignette_mask

    # --- 13b. DUST & SCRATCHES ---
    # On the film, so after the lens and before the grain.
    if dust_amount > 0 or scratches > 0:
        final_image = _dust(final_image, dust_amount, scratches, res_scale, seed)

    # --- 13c. DATE STAMP ---
    # Exposed by LEDs behind the film: the lens's vignette does not reach it.
    if stamp_mask is not None:
        final_image = _stamp(final_image, stamp_mask, res_scale)

    # --- 14. FILM GRAIN ---
    if grain_power > 0:
        # Seeded from the image's seed, so the same seed gives the same grain.
        gen = None
        if seed is not None:
            gen = torch.Generator(device=final_image.device)
            gen.manual_seed(int(seed) & 0x7FFFFFFFFFFFFFFF)
        raw_noise = torch.randn(final_image.shape, generator=gen,
                                device=final_image.device, dtype=final_image.dtype)
        raw_noise_p = raw_noise.permute(0, 3, 1, 2)
        clumped = _blur(raw_noise_p, 3, 0.8)
        clumped = clumped.permute(0, 2, 3, 1) * 1.5

        if monochrome_grain:
            mono = clumped.mean(dim=-1, keepdim=True)
            clumped = mono.repeat(1, 1, 1, 3)
        else:
            mono = clumped.mean(dim=-1, keepdim=True)
            clumped = torch.lerp(mono, clumped, 0.4)

        emulsion_curve = final_image * (1.0 - final_image) * 4.0
        emulsion_curve = torch.clamp(emulsion_curve + 0.01, 0.0, 1.0)
        final_image = final_image + (clumped * grain_power * emulsion_curve)

    # --- 15. HIGHLIGHT ROLL-OFF ---
    if highlight_rolloff > 0:
        final_image = final_image / (1.0 + final_image * highlight_rolloff * 0.5)

    final_image = torch.clamp(final_image, 0.0, 1.0)
    result = tensor_to_pil(final_image)
    if alpha is not None:
        result.putalpha(alpha)

    # depth_mask went through the same grid_sample as the image in step 3, so
    # this is the map that lines up with what is being returned.
    warped_depth = Image.fromarray(
        np.rint(depth_mask[0, ..., 0].detach().cpu().clamp(0, 1).numpy() * 255.0).astype(np.uint8),
        mode="L",
    )
    return result, warped_depth
