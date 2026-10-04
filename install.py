import launch

packages = [
    "transformers>=4.40.0",
    "accelerate",
    "safetensors",
    "opencv-python",
    "blurgenerator>=1.0",
    "scipy",
]

for package in packages:
    if not launch.is_installed(package.split(">=")[0].split("==")[0]):
        launch.run_pip(f"install {package}", f"Optical Realism requirement: {package}")