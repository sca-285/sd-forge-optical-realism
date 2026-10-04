"""Depth maps from MoGe-3 (Microsoft), in the same form as the Depth Anything path.

The model code is vendored in lib_or/moge (MIT; DINOv2 parts Apache-2.0), so no
package is installed and nothing in the host's environment changes. The sparse
3D refiner, which gives MoGe-3 its sharper edges, needs the optional flex_gemm
package and a CUDA GPU; without them the model runs with the refiner off.

Output: an L image, white = near, black = far (the sky and anything MoGe marks
invalid count as farthest), normalised per image like the Depth Anything path.
"""

from __future__ import annotations

import os
import warnings

import numpy as np
import torch
from PIL import Image

MODELS = {
    "MoGe-3 Large (vitl)": "Ruicheng/moge-3-vitl",
    "MoGe-3 Giant (vitg)": "Ruicheng/moge-3-vitg",
}

_model = None
_model_name = None
_notes = set()


def is_moge(name) -> bool:
    return str(name) in MODELS


def _note(key, text):
    if key not in _notes:
        _notes.add(key)
        print(f"[Optical Realism] {text}")


def refiner_available() -> bool:
    try:
        import flex_gemm  # noqa: F401
        return True
    except Exception:
        return False


def _checkpoint(name):
    """A local copy in models/MoGe wins; otherwise the Hugging Face cache."""
    repo = MODELS[name]
    file = repo.split("/")[-1] + ".pt"            # e.g. moge-3-vitl.pt
    try:
        from modules import shared
        local = os.path.join(shared.models_path, "MoGe", file)
        if os.path.isfile(local):
            return local
    except Exception:
        pass
    from huggingface_hub import hf_hub_download
    print(f"[Optical Realism] Loading MoGe-3: {repo} (downloaded on first use)")
    return hf_hub_download(repo_id=repo, filename="model.pt")


def _load(name, device):
    from .moge.model.v3 import MoGeModel

    ckpt = torch.load(_checkpoint(name), map_location="cpu", weights_only=True)
    config = dict(ckpt["model_config"])
    state = ckpt["model"]
    use_refiner = "refiner" in config and device.type == "cuda" and refiner_available()
    if not use_refiner:
        config.pop("refiner", None)
        state = {k: v for k, v in state.items() if not k.startswith("refiner.")}
        if device.type == "cuda":
            _note("no-refiner", "MoGe-3 refiner needs the flex_gemm package; running without it "
                                "(see the README to enable it).")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = MoGeModel(**config)
    missing, _ = model.load_state_dict(state, strict=False)
    if missing:
        print(f"[Optical Realism] MoGe-3: {len(missing)} weights missing from the checkpoint.")
    model.eval()
    if device.type == "cuda":
        # The ViT backbone is most of the weights: fp16 halves its VRAM. The
        # neck and heads stay fp32, as MoGe's own mixed-precision mode does.
        model.encoder.backbone.half()
        model.enable_mixed_precision(torch.float16)
    del ckpt
    return model


def get_model(name, device):
    global _model, _model_name
    if _model is None or _model_name != name:
        _model = None
        _model = _load(name, device)
        _model_name = name
    _model.to(device)
    return _model


def park():
    """Move the model to system RAM between jobs."""
    if _model is not None:
        _model.to("cpu")


def unload():
    global _model, _model_name
    _model = None
    _model_name = None


def normalise(z, valid):
    """Metric-free depth z (H, W) -> near-white 0..1 disparity, invalid = 0."""
    disp = torch.where(valid, 1.0 / z.clamp_min(1e-6), torch.zeros_like(z))
    vals = disp[valid]
    if vals.numel() < 16:
        return torch.zeros_like(z)
    step = max(1, vals.numel() // 262144)       # percentiles on a sample
    sample = vals[::step].float()
    lo = torch.quantile(sample, 0.005)
    hi = torch.quantile(sample, 0.995)
    out = ((disp - lo) / (hi - lo).clamp_min(1e-6)).clamp(0.0, 1.0)
    return torch.where(valid, out, torch.zeros_like(out))


@torch.inference_mode()
def depth_map(image: Image.Image, name: str, device, refine_steps: int = 3) -> Image.Image:
    from .moge.utils.geometry_torch import recover_focal_shift

    device = torch.device(device)
    model = get_model(name, device)
    x = torch.from_numpy(np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0)
    x = x.permute(2, 0, 1).unsqueeze(0).to(device)

    steps = int(refine_steps) if hasattr(model, "refiner") else 0
    num_tokens = int(model.num_tokens_range[1])   # MoGe's finest setting
    out = model(x, num_tokens=num_tokens, refine_steps=steps)

    points = out["points"][0].float()             # (H, W, 3), affine: z known up to a shift
    mask = out.get("mask")
    mask = (mask[0] > 0.5) if mask is not None else torch.ones(points.shape[:2], dtype=torch.bool,
                                                                device=points.device)
    _, shift = recover_focal_shift(points, mask)
    z = points[..., 2] + shift
    valid = mask & (z > 0) & torch.isfinite(z)
    d = normalise(z, valid)
    return Image.fromarray(np.rint(d.cpu().numpy() * 255.0).astype(np.uint8), mode="L")
