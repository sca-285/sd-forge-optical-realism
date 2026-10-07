"""Lens filters, lens character and retro video. Pure torch.

Images here are (B, H, W, 3) floats in 0..1, like the core's working image.
Every effect that spreads light works at reduced resolution and is scaled back
up: a streak or a star is soft by nature, so nothing is lost, and the cost
stays flat as the frame grows.
"""

from __future__ import annotations

import math

import torch
import torch.nn.functional as F

BOKEH_SHAPES = ["Round", "Oval (anamorphic)", "Hexagon (6 blades)"]
STAR_POINTS = ["4", "6", "8"]
HAZE_COLOURS = {
    "Blue-grey": (0.17, 0.20, 0.26),
    "Warm morning": (0.62, 0.50, 0.38),
    "White mist": (0.78, 0.80, 0.82),
    "Smoke": (0.32, 0.31, 0.30),
    "Dusk violet": (0.36, 0.30, 0.45),
}


def _bchw(x):
    return x.permute(0, 3, 1, 2)


def _bhwc(x):
    return x.permute(0, 2, 3, 1)


def _luma(x):
    """x: (B, H, W, 3) -> (B, H, W, 1)."""
    return 0.2126 * x[..., 0:1] + 0.7152 * x[..., 1:2] + 0.0722 * x[..., 2:3]


def _screen(base, light):
    return 1.0 - (1.0 - base) * (1.0 - light.clamp(0.0, 1.0))


def _hue_rgb(h, device, dtype):
    k = torch.tensor([5.0, 3.0, 1.0], device=device, dtype=dtype)
    k = (k + h * 6.0) % 6.0
    return (1.0 - torch.clamp(torch.minimum(k, 4.0 - k), 0.0, 1.0)).view(1, 1, 1, 3)


def _down(x, factor):
    return F.avg_pool2d(x, factor, ceil_mode=True) if factor > 1 else x


def _up(x, size):
    return F.interpolate(x, size=size, mode="bilinear", align_corners=False) if x.shape[-2:] != size else x


def _seeded(device, seed, salt):
    if seed is None:
        return None
    g = torch.Generator(device=device)
    g.manual_seed((int(seed) * 1000003 + salt) & 0x7FFFFFFFFFFFFFFF)
    return g


def _rand(g, device, *shape):
    return torch.rand(shape, generator=g, device=device)


# ------------------------------------------------------------------ bokeh

def bokeh_kernel(r, shape="Round", rim=0.0, device="cpu", dtype=torch.float32):
    """(2r+1)^2 aperture kernel, summing to 1. Oval is taller than wide, as
    an anamorphic lens squeezes it; rim brightens the edge (soap-bubble)."""
    yy, xx = torch.meshgrid(torch.arange(-r, r + 1, device=device, dtype=dtype),
                            torch.arange(-r, r + 1, device=device, dtype=dtype), indexing="ij")
    if shape.startswith("Oval"):
        d = torch.sqrt((xx * 1.8) ** 2 + yy ** 2) / max(r, 1)
    elif shape.startswith("Hexagon"):
        # Distance to a regular hexagon's edge: max over its three axes.
        a = [math.radians(t) for t in (0, 60, 120)]
        d = torch.stack([(xx * math.cos(t) + yy * math.sin(t)).abs() for t in a]).amax(0) / (max(r, 1) * 0.866)
    else:
        d = torch.sqrt(xx ** 2 + yy ** 2) / max(r, 1)
    k = (d <= 1.0).to(dtype)
    if rim > 0:
        k = k * (1.0 + 3.0 * rim * ((d > 0.75) & (d <= 1.0)).to(dtype))
    return k / k.sum().clamp_min(1e-6)


def swirl(x, amount):
    """Swirly (Helios) / cat-eye bokeh: the out-of-focus image is smeared
    round the frame's centre, more towards the edges. x: (B, H, W, 3)."""
    if amount <= 0:
        return x
    b, h, w, _ = x.shape
    yy, xx = torch.meshgrid(torch.linspace(-1, 1, h, device=x.device, dtype=x.dtype),
                            torch.linspace(-1, 1, w, device=x.device, dtype=x.dtype), indexing="ij")
    aspect = w / h
    px, py = xx * aspect, yy
    r2 = (px * px + py * py) / (aspect * aspect + 1.0)
    src = _bchw(x)
    acc = torch.zeros_like(src)
    taps = 9
    for t in torch.linspace(-1.0, 1.0, taps).tolist():
        theta = t * amount * 0.10 * r2
        c, s = torch.cos(theta), torch.sin(theta)
        gx = (px * c - py * s) / aspect
        gy = px * s + py * c
        grid = torch.stack((gx, gy), -1).unsqueeze(0).expand(b, -1, -1, -1)
        acc = acc + F.grid_sample(src, grid, mode="bilinear", padding_mode="reflection", align_corners=True)
    return _bhwc(acc / taps)


# ------------------------------------------------------------------ light

def _highlights(x, threshold, softness):
    return x * ((_luma(x) - threshold) / softness).clamp(0.0, 1.0)


def anamorphic_streak(x, amount, hue=0.6, res_scale=1.0):
    """The horizontal flare of an anamorphic lens: every bright light throws a
    long thin line across the frame, blue by default."""
    if amount <= 0:
        return x
    b, h, w, _ = x.shape
    src = _bchw(_luma(_highlights(x, 0.80, 0.15)))
    f = max(1, int(round(4 * max(res_scale, 0.5))))
    small = _down(src, f)
    sw = small.shape[-1]
    out = torch.zeros_like(small)
    for frac, weight in ((0.04, 0.6), (0.18, 0.4)):
        sigma = max(1.0, sw * frac)
        r = min(int(sigma * 3), sw - 1)
        xs = torch.arange(-r, r + 1, device=x.device, dtype=x.dtype)
        k = torch.exp(-0.5 * (xs / sigma) ** 2)
        k = (k / k.max()).view(1, 1, 1, -1)
        out = out + weight * F.conv2d(F.pad(small, (r, r, 0, 0), mode="replicate"), k)
    # A line is thin: a touch of vertical spread only.
    out = F.avg_pool2d(out, (3, 1), stride=1, padding=(1, 0))
    line = _bhwc(_up(out, (h, w))) * 0.12
    tint = torch.lerp(torch.ones(1, 1, 1, 3, device=x.device, dtype=x.dtype),
                      _hue_rgb(hue, x.device, x.dtype), 0.75)
    return _screen(x, line * tint * amount * 2.0)


def star_filter(x, amount, points="6", angle=15.0, length=0.08, res_scale=1.0):
    """A cross-screen (star) filter: thin rays from the brightest points."""
    if amount <= 0:
        return x
    b, h, w, _ = x.shape
    src = _bchw(_highlights(x, 0.88, 0.08))
    length_px = max(4.0, length * max(h, w))
    f = max(1, int(math.ceil(length_px / 24)))
    small = _down(src, f)
    r = max(2, int(round(length_px / f)))
    yy, xx = torch.meshgrid(torch.arange(-r, r + 1, device=x.device, dtype=x.dtype),
                            torch.arange(-r, r + 1, device=x.device, dtype=x.dtype), indexing="ij")
    k = torch.zeros_like(xx)
    n = int(points) // 2
    for i in range(n):
        t = math.radians(angle + 180.0 * i / n)
        along = xx * math.cos(t) + yy * math.sin(t)
        across = (-xx * math.sin(t) + yy * math.cos(t)).abs()
        ray = (1.0 - across).clamp(0.0, 1.0) * torch.exp(-3.0 * along.abs() / r)
        k = torch.maximum(k, ray)
    k = (k / k.sum() * 6.0).view(1, 1, 2 * r + 1, 2 * r + 1).expand(3, 1, -1, -1)
    rays = F.conv2d(F.pad(small, (r, r, r, r)), k, groups=3)
    return _screen(x, _bhwc(_up(rays, (h, w))) * amount * 1.5)


def light_centre(x):
    """Where the strongest light is, (cx, cy) in 0..1."""
    y = _luma(x)[0, ..., 0]
    wgt = (y.clamp(0.0, 1.0) ** 8)
    if float(wgt.sum()) < 1e-6:
        return 0.5, 0.3
    h, w = y.shape
    ys = torch.linspace(0, 1, h, device=x.device, dtype=x.dtype).view(h, 1)
    xs = torch.linspace(0, 1, w, device=x.device, dtype=x.dtype).view(1, w)
    total = wgt.sum()
    return float((wgt * xs).sum() / total), float((wgt * ys).sum() / total)


def god_rays(x, depth, amount, length=0.5, centre=None, res_scale=1.0):
    """Light shafts: the bright parts of the frame, smeared towards the light
    source with falling strength, as light scatters in air. Far bright areas
    (sky, windows) feed the rays more than near ones. depth: (B, H, W, 1)."""
    if amount <= 0:
        return x
    b, h, w, _ = x.shape
    cx, cy = centre if centre is not None else light_centre(x)
    src = _highlights(x, 0.70, 0.25) * (1.2 - depth).clamp(0.0, 1.0)
    f = 4
    small = _down(_bchw(src), f)
    sh, sw = small.shape[-2:]
    yy, xx = torch.meshgrid(torch.linspace(-1, 1, sh, device=x.device, dtype=x.dtype),
                            torch.linspace(-1, 1, sw, device=x.device, dtype=x.dtype), indexing="ij")
    lx, ly = cx * 2 - 1, cy * 2 - 1
    # Screen-space light scattering: every pixel gathers light along the whole
    # line to the source; the weight falls off along the way, slower for a
    # longer ray, so the shafts reach further from the light.
    acc = torch.zeros_like(small)
    taps = 48
    falloff = 1.0 / max(length, 0.05)
    for i in range(taps):
        t = i / taps
        grid = torch.stack((lx + (xx - lx) * (1 - t), ly + (yy - ly) * (1 - t)), -1)
        grid = grid.unsqueeze(0).expand(b, -1, -1, -1)
        wgt = math.exp(-falloff * 3.0 * (1.0 - t)) / taps
        acc = acc + wgt * F.grid_sample(small, grid, mode="bilinear", padding_mode="zeros", align_corners=True)
    rays = _bhwc(_up(acc, (h, w)))
    return _screen(x, rays * amount * 4.0)


def purple_fringe(x, amount, res_scale=1.0):
    """Purple fringing: a violet edge just outside very bright areas, where a
    lens cannot bring blue and red to one focus."""
    if amount <= 0:
        return x
    hi = _bchw(((_luma(x) - 0.80) * 5.0).clamp(0.0, 1.0))
    r = max(1, int(round(2 * res_scale)))
    spread = F.max_pool2d(hi, 2 * r + 1, stride=1, padding=r)
    halo = _bhwc((spread - hi).clamp(0.0, 1.0))
    purple = torch.tensor([0.55, 0.15, 0.85], device=x.device, dtype=x.dtype).view(1, 1, 1, 3)
    return _screen(x, halo * purple * amount * 1.2)


def tilt_shift(x, amount, position=0.5, width=0.2, angle=0.0, blur_fn=None, res_scale=1.0):
    """Miniature look: a band of focus, growing blur above and below it."""
    if amount <= 0 or blur_fn is None:
        return x
    b, h, w, _ = x.shape
    yy, xx = torch.meshgrid(torch.linspace(0, 1, h, device=x.device, dtype=x.dtype),
                            torch.linspace(0, 1, w, device=x.device, dtype=x.dtype), indexing="ij")
    t = math.radians(angle)
    d = ((yy - position) * math.cos(t) - (xx - 0.5) * math.sin(t) * (w / h)).abs()
    m = ((d - width / 2) / 0.25).clamp(0.0, 1.0).view(1, h, w, 1)
    radius = max(1, int(round(amount * 25 * res_scale)))
    near = _bhwc(blur_fn(_bchw(x), max(1, radius // 2)))
    far = _bhwc(blur_fn(_bchw(x), radius))
    out = torch.lerp(x, near, (m * 2).clamp(0.0, 1.0))
    return torch.lerp(out, far, (m * 2 - 1).clamp(0.0, 1.0))


# ------------------------------------------------------------------ retro

def vhs(x, amount, res_scale=1.0, seed=None):
    """VHS tape: colour smeared and shifted sideways against a softer picture,
    tape noise, and the tracking band near the bottom."""
    if amount <= 0:
        return x
    b, h, w, _ = x.shape
    yiq = torch.tensor([[0.299, 0.587, 0.114], [0.596, -0.274, -0.322], [0.211, -0.523, 0.312]],
                       device=x.device, dtype=x.dtype)
    c = torch.einsum("ij,bhwj->bhwi", yiq, x)
    s = max(res_scale, 0.5)

    def hblur(t, sigma):
        r = max(1, int(sigma * 3))
        xs = torch.arange(-r, r + 1, device=x.device, dtype=x.dtype)
        k = torch.exp(-0.5 * (xs / max(sigma, 0.3)) ** 2)
        k = (k / k.sum()).view(1, 1, 1, -1).expand(t.shape[1], 1, 1, -1)
        return F.conv2d(F.pad(t, (r, r, 0, 0), mode="replicate"), k, groups=t.shape[1])

    cc = _bchw(c)
    luma = hblur(cc[:, 0:1], 1.2 * s * amount)
    chroma = hblur(cc[:, 1:3], 6.0 * s * (0.5 + amount))
    shift = int(round(4 * s * amount))
    if shift:
        chroma = torch.roll(chroma, shifts=shift, dims=3)
    chroma = chroma * (1.0 - 0.25 * amount)
    out = torch.einsum("ij,bjhw->bihw", torch.linalg.inv(yiq), torch.cat((luma, chroma), 1))
    g = _seeded(x.device, seed, 31)
    # Fine horizontal tape noise.
    noise = (_rand(g, x.device, 1, 1, h, max(1, w // 8)) - 0.5)
    noise = F.interpolate(noise, size=(h, w), mode="bilinear", align_corners=False)
    out = out + noise * 0.08 * amount
    # Tracking band: a strip near the bottom, shifted and noisy.
    band_h = max(2, int(h * 0.03))
    top = h - band_h - int(h * (0.02 + 0.05 * float(_rand(g, x.device, 1))))
    seg = out[:, :, top:top + band_h]
    seg = torch.roll(seg, shifts=int(w * 0.02 * amount) + 1, dims=3)
    seg = seg + (_rand(g, x.device, 1, 1, band_h, w) - 0.3) * 0.5 * amount
    out = torch.cat((out[:, :, :top], seg, out[:, :, top + band_h:]), 2)
    return _bhwc(out.clamp(0.0, 1.0))


def scanlines(x, amount, pitch=3.0, res_scale=1.0):
    """CRT scanlines, with the picture lifted so it keeps its brightness."""
    if amount <= 0:
        return x
    h = x.shape[1]
    p = max(2.0, pitch * max(res_scale, 0.5))
    y = torch.arange(h, device=x.device, dtype=x.dtype).view(1, h, 1, 1)
    lines = 1.0 - amount * 0.5 * (0.5 + 0.5 * torch.cos(2 * math.pi * y / p))
    return (x * lines / (1.0 - amount * 0.22)).clamp(0.0, 1.0)


def glitch(x, amount, seed=None):
    """Digital glitch: horizontal slices torn sideways, colour channels split."""
    if amount <= 0:
        return x
    b, h, w, _ = x.shape
    g = _seeded(x.device, seed, 37)
    out = x.clone()
    n = 2 + int(amount * 10)
    for _ in range(n):
        y0 = int(float(_rand(g, x.device, 1)) * h)
        hh = max(1, int(h * (0.005 + 0.05 * float(_rand(g, x.device, 1)))))
        dx = int((float(_rand(g, x.device, 1)) - 0.5) * w * 0.15 * amount)
        sl = out[:, y0:y0 + hh]
        sl = torch.roll(sl, shifts=dx, dims=2)
        split = max(1, int(abs(dx) * 0.3))
        sl = torch.cat((torch.roll(sl[..., 0:1], split, 2), sl[..., 1:2], torch.roll(sl[..., 2:3], -split, 2)), -1)
        out[:, y0:y0 + hh] = sl
    return out
