import os
import numpy as np
from PIL import Image
import torch
from diffusers import AutoPipelineForInpainting
from diffusers.utils import load_image
import rembg
import shutil

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
    # Invert the mask (0 -> 255, 255 -> 0)
    inverted_mask = 255 - mask
    return inverted_mask

# 3) Maskeyi Bulanıklaştırma (Only in memory)
def blur_mask(mask):
    # Convert numpy array to Image and blur it using the inpainting pipeline
    mask_image = Image.fromarray(mask).convert('L')  # Convert to grayscale
    
    # Load inpainting pipeline
    pipeline = AutoPipelineForInpainting.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16).to('cuda')
    
    # Blur the mask (process within pipeline)
    blurred_mask = pipeline.mask_processor.blur(mask_image, blur_factor=20)
    return blurred_mask

# 4) Model ile Inpainting (Save final result)
def apply_inpainting(input_image_path, mask, prompt):
    input_image = load_image(input_image_path)

    # Load the inpainting pipeline
    pipeline = AutoPipelineForInpainting.from_pretrained("diffusers/stable-diffusion-xl-1.0-inpainting-0.1", torch_dtype=torch.float16, variant="fp16").to('cuda')
    pipeline.enable_model_cpu_offload()

    generator = torch.Generator("cuda").manual_seed(92)
    
    # Perform inpainting
    output_image = pipeline(prompt=prompt, image=input_image, mask_image=mask, generator=generator).images[0]
    return output_image

# 5) Upscale İşlemi
def upscale_image_with_realesrgan(input_image):
    # Real-ESRGAN modelini çalıştırmak için tam dosya yollarını kullanıyoruz
    script_path = r'Real-ESRGAN/inference_realesrgan.py'
    input_image.save("temp_input_image.png")  # Save the input image temporarily

    # Real-ESRGAN komutunu çalıştırıyoruz (orijinal modelin dosya oluşturmasını sağlıyoruz)
    os.system(f"python \"{script_path}\" -n RealESRGAN_x4plus -i temp_input_image.png -o . --outscale 3.5")

    # Load the output image back into memory and return it
    upscaled_image = Image.open("temp_input_image_out.png")
    os.remove("temp_input_image.png")  # Clean up the temp file
    os.remove("temp_input_image_out.png")  # Clean up the output file
    return upscaled_image

# 6) Resmi Orijinal Boyuta Yeniden Boyutlandırma
def resize_image_to_original(image, original_image_path):
    original_image = Image.open(original_image_path)
    original_size = original_image.size
    
    # Resize the upscaled image to match the original dimensions
    resized_image = image.resize(original_size)
    return resized_image

# Ana işleyiş fonksiyonu (Process in memory and return final result)
def process_image_pipeline(input_image_path, prompt):
    # 1) Mask Oluştur (Memory-based)
    mask = get_object_mask(input_image_path)

    # 2) Maskeyi Ters Çevir (Memory-based)
    inverted_mask = invert_mask(mask)

    # 3) Maskeyi Bulanıklaştır (Memory-based)
    blurred_mask = blur_mask(inverted_mask)

    # 4) Inpainting Uygula (Memory-based)
    inpainted_image = apply_inpainting(input_image_path, blurred_mask, prompt)

    # 5) Upscale işlemi (Memory-based)
    upscaled_image = upscale_image_with_realesrgan(inpainted_image)

    # 6) Resmi orijinal boyuta yeniden boyutlandır (Memory-based)
    resized_image = resize_image_to_original(upscaled_image, input_image_path)

    # Return the final image
    return resized_image

# Örnek kullanım
input_image_path = "../Images/Original Images/test_1.png"
prompt = "Replace the background with a soft, neutral-colored surface."

# İşlem hattını başlat
final_image = process_image_pipeline(input_image_path, prompt)
final_image.save("final_resized_image.png")
print("Son işlemden geçmiş resim kaydedildi: final_resized_image.png")
