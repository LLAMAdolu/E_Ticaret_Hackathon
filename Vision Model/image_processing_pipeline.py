import os
import numpy as np
from PIL import Image
import torch
from diffusers import AutoPipelineForInpainting
from diffusers.utils import load_image
import rembg
import shutil
import subprocess

# 1) Mask Oluşturma (Only in memory)
def get_object_mask(image_path):
    image = Image.open(image_path)
    input_array = np.array(image)

    # Remove the background and get the alpha mask
    output_array = rembg.remove(input_array)
    mask = output_array[:, :, 3]  # Extract the alpha channel as a mask
    return mask

# 2) Maskeyi Ters Çevirme (Only in memory)
def invert_mask(mask):
    inverted_mask = 255 - mask
    return inverted_mask

# 3) Maskeyi Bulanıklaştırma (Only in memory)
def blur_mask(mask):
    mask_image = Image.fromarray(mask).convert('L')  # Convert to grayscale
    
    # Load inpainting pipeline
    pipeline = AutoPipelineForInpainting.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16).to('cuda')
    
    blurred_mask = pipeline.mask_processor.blur(mask_image, blur_factor=20)
    return blurred_mask

# 4) Model ile Inpainting (Save final result)
def apply_inpainting(input_image_path, mask, prompt):
    input_image = load_image(input_image_path)

    pipeline = AutoPipelineForInpainting.from_pretrained("diffusers/stable-diffusion-xl-1.0-inpainting-0.1", torch_dtype=torch.float16, variant="fp16").to('cuda')
    pipeline.enable_model_cpu_offload()

    generator = torch.Generator("cuda").manual_seed(92)
    
    # Perform inpainting
    output_image = pipeline(prompt=prompt, image=input_image, mask_image=mask, generator=generator).images[0]

    return output_image


# 5) Upscale İşlemi
def upscale_image_with_realesrgan(input_image):
    script_path = 'E_Ticaret_Hackathon/VisionModel/Real-ESRGAN/inference_realesrgan.py'
    input_image.save("temp_input_image.png")

    command = f"python ../VisionModel/Real-ESRGAN/inference_realesrgan.py -n RealESRGAN_x4plus -i temp_input_image.png -o . --outscale 3.5"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Real-ESRGAN upscale işlemi sırasında bir hata oluştu: {result.stderr}")
    
    output_image_path = "temp_input_image_out.png"
    
    if not os.path.exists(output_image_path):
        raise FileNotFoundError(f"{output_image_path} dosyası bulunamadı.")
    
    upscaled_image = Image.open(output_image_path)
    os.remove("temp_input_image.png")
    os.remove(output_image_path)
    return upscaled_image

# 6) Resmi Orijinal Boyuta Yeniden Boyutlandırma
def resize_image_to_original(image, original_image_path):
    original_image = Image.open(original_image_path)
    original_size = original_image.size
    
    # Resize the upscaled image to match the original dimensions
    resized_image = image.resize(original_size)
    return resized_image


# Ana işleyiş fonksiyonu
def process_image_pipeline(input_image_path, prompt):
    mask = get_object_mask(input_image_path)
    inverted_mask = invert_mask(mask)
    blurred_mask = blur_mask(inverted_mask)

    inpainted_image = apply_inpainting(input_image_path, blurred_mask, prompt)
    upscaled_image = upscale_image_with_realesrgan(inpainted_image)
    resized_image = resize_image_to_original(upscaled_image, input_image_path)
    
    return resized_image