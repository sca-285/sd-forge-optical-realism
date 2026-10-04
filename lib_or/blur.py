"""Extra blur effects via blurgenerator (optional dependency)."""

import numpy as np
from PIL import Image

try:
    import cv2
    from blurgenerator import (
        motion_blur, motion_blur_with_depth_map,
        lens_blur, lens_blur_with_depth_map,
        gaussian_blur, gaussian_blur_with_depth_map
    )
    BLUR_AVAILABLE = True
except ImportError:
    BLUR_AVAILABLE = False


def apply_blur_effect(image: Image.Image, depth_map: Image.Image, 
                      blur_type: str, use_depth: bool,
                      gaussian_amount: int, gaussian_sigma: int,
                      lens_radius: int, lens_components: int, exposure_gamma: float,
                      motion_size: int, motion_angle: int,
                      num_layers: int, min_blur: int, max_blur: int) -> Image.Image:

    if not BLUR_AVAILABLE:
        return image

    # blurgenerator's operations are channel-symmetric, so the image stays in
    # RGB throughout (no BGR round trip).
    img_rgb = np.array(image.convert("RGB"))

    if use_depth and depth_map is not None:
        depth_np = np.array(depth_map)

        if depth_np.ndim == 3:
            depth_np = depth_np[..., 0]

        if depth_np.max() <= 1.0:
            depth_np = (depth_np * 255).astype(np.uint8)
        else:
            depth_np = depth_np.astype(np.uint8)

        depth_np = cv2.resize(depth_np, (img_rgb.shape[1], img_rgb.shape[0]))
        # blurgenerator gives the BRIGHTEST depth values the most blur, while
        # Depth Anything - and the usual convention for a hand-made map - paints
        # NEAR things bright. Invert so far = bright = most blur, and the subject
        # stays sharp.
        depth_np = 255 - depth_np
        depth_u8 = cv2.cvtColor(depth_np, cv2.COLOR_GRAY2BGR)

        safe_min_blur = max(1, int(min_blur))
        safe_max_blur = max(safe_min_blur + 1, int(max_blur))

        # blurgenerator slices the depth range with step = (max - min) // layers
        # and feeds that to range(). A flat or low-contrast depth map - a hand
        # drawn grey one, a flat scene, anything whose range is under num_layers
        # - makes that step 0 and raises "range() arg 3 must not be zero". Fall
        # back to the plain blur instead of losing the effect to an exception.
        depth_range = int(depth_np.max()) - int(depth_np.min())
        if depth_range < num_layers:
            print(f"[Optical Realism] Depth map range is {depth_range} over "
                  f"{num_layers} layers - too flat to slice, using flat blur.")
            use_depth = False

    if use_depth and depth_map is not None:
        if blur_type == "Gaussian":
            result_rgb = gaussian_blur_with_depth_map(
                img_rgb,
                depth_map=depth_u8,
                sigma=gaussian_sigma,
                num_layers=num_layers,
                min_blur=safe_min_blur,
                max_blur=safe_max_blur
            )
        elif blur_type == "Lens":
            result_rgb = lens_blur_with_depth_map(
                img_rgb,
                depth_map=depth_u8,
                components=lens_components,
                exposure_gamma=exposure_gamma,
                num_layers=num_layers,
                min_blur=safe_min_blur,
                max_blur=safe_max_blur
            )
        else:  # Motion
            result_rgb = motion_blur_with_depth_map(
                img_rgb,
                depth_map=depth_u8,
                angle=motion_angle,
                num_layers=num_layers,
                min_blur=safe_min_blur,
                max_blur=safe_max_blur
            )

        # Pixels no depth layer covered come back pure black; put the original
        # back there. Restoring a pixel that was already black is a no-op, so
        # this only ever repairs genuine gaps.
        black_mask = (result_rgb[:, :, 0] == 0) & (result_rgb[:, :, 1] == 0) & (result_rgb[:, :, 2] == 0)
        if np.any(black_mask):
            result_rgb[black_mask] = img_rgb[black_mask]

    else:
        if blur_type == "Gaussian":
            result_rgb = gaussian_blur(img_rgb, gaussian_amount)
        elif blur_type == "Lens":
            result_rgb = lens_blur(img_rgb, lens_radius, lens_components, exposure_gamma)
        else:
            result_rgb = motion_blur(img_rgb, motion_size, motion_angle)

    return Image.fromarray(result_rgb)


