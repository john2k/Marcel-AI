import os
import shutil
from huggingface_hub import hf_hub_download

print("Downloading DreamShaper 8...")
ds_path = hf_hub_download(
    repo_id="Lykon/DreamShaper",
    filename="DreamShaper_8_pruned.safetensors",
    local_dir="/datastore/ComfyUI/models/checkpoints",
    local_dir_use_symlinks=False
)
print("DreamShaper downloaded to:", ds_path)

print("Downloading SD 1.5 VAE...")
vae_path = hf_hub_download(
    repo_id="stabilityai/sd-vae-ft-mse-original",
    filename="vae-ft-mse-840000-ema-pruned.safetensors",
    local_dir="/datastore/ComfyUI/models/vae",
    local_dir_use_symlinks=False
)
print("VAE downloaded to:", vae_path)

print("Downloading AnimateDiff v3 Motion Module...")
ad_path = hf_hub_download(
    repo_id="guoyww/animatediff",
    filename="v3_sd15_mm.ckpt",
    local_dir="/datastore/ComfyUI/models/animatediff_models",
    local_dir_use_symlinks=False
)
os.makedirs("/datastore/ComfyUI/custom_nodes/ComfyUI-AnimateDiff-Evolved/models", exist_ok=True)
shutil.copy(ad_path, "/datastore/ComfyUI/custom_nodes/ComfyUI-AnimateDiff-Evolved/models/v3_sd15_mm.ckpt")
print("AnimateDiff motion module installed to:", ad_path)
