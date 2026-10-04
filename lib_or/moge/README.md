# Vendored MoGe-3 model code

From [microsoft/MoGe](https://github.com/microsoft/MoGe), commit
`74fbce054ebed49800de42d0ad0e83495065719a`. MIT licence, except
`model/modules/dinov2/`, which is Meta AI's DINOv2 under Apache-2.0; both texts
are in `LICENSE`.

Only the inference model is kept (`model/v2.py`, `model/v3.py`, `model/utils.py`,
`model/modules/`). Changes from upstream:

- `utils3d` is optional (only the unused `infer()` methods need it).
- `model/v3.py` imports the sparse refiner (and so `flex_gemm`) only when the
  refiner is built, so the model runs without `flex_gemm` with the refiner off.
- `model/utils.py`: the DDP training hook is removed.
- `utils/geometry_torch.py` is a new file holding the few helpers the model and
  the focal / shift recovery need, taken from upstream `utils/geometry_torch.py`
  and `utils/geometry_numpy.py`.
