from repositories import UserRepository, ProductRepository
import os
import numpy as np
from PIL import Image
import torch
from diffusers import AutoPipelineForInpainting
from diffusers.utils import load_image
import rembg
import shutil
import subprocess
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import io

class VisionModel:
    def __init__(self):
        self.vision_pipline, self.vision_generator = self.get_vision_model()
        self.stablediff_pipeline = self.get_stablediff()
    
    
    def get_vision_model(self):
        pipeline = AutoPipelineForInpainting.from_pretrained("diffusers/stable-diffusion-xl-1.0-inpainting-0.1", 
                                                                  torch_dtype=torch.float16, variant="fp16").to('cuda')
        pipeline.enable_model_cpu_offload()
        generator = torch.Generator("cuda").manual_seed(92)
        return pipeline, generator
    
    def get_stablediff(self):
        pipeline = AutoPipelineForInpainting.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16).to('cuda')
        return pipeline
    
    # 1) Mask Oluşturma (Only in memory)
    def get_object_mask(self, image_path):
        image = Image.open(image_path)
        input_array = np.array(image)

        # Remove the background and get the alpha mask
        output_array = rembg.remove(input_array)
        mask = output_array[:, :, 3]  # Extract the alpha channel as a mask
        return mask

    # 2) Maskeyi Ters Çevirme (Only in memory)
    def invert_mask(self, mask):
        inverted_mask = 255 - mask
        return inverted_mask
    
    # 3) Maskeyi Bulanıklaştırma (Only in memory)
    def blur_mask(self, mask):
        mask_image = Image.fromarray(mask).convert('L')  # Convert to grayscale
    
        blurred_mask = self.stablediff_pipeline.mask_processor.blur(mask_image, blur_factor=20)
        return blurred_mask
    
    # 5) Upscale İşlemi
    def upscale_image_with_realesrgan(self, input_image):
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

    def apply_inpainting(self, input_image_path, mask, prompt):
        input_image = load_image(input_image_path)
        output_image = self.pipeline(prompt=prompt, image=input_image, mask_image=mask, generator=self.generator).images[0]

        return output_image
    
    # 6) Resmi Orijinal Boyuta Yeniden Boyutlandırma
    def resize_image_to_original(self, image, original_image_path):
        original_image = Image.open(original_image_path)
        original_size = original_image.size
    
        # Resize the upscaled image to match the original dimensions
        resized_image = image.resize(original_size)
        return resized_image


    # Ana işleyiş fonksiyonu
    def process_image_pipeline(self, input_image_path, prompt):
        mask = get_object_mask(input_image_path)
        inverted_mask = invert_mask(mask)
        blurred_mask = blur_mask(inverted_mask)

        inpainted_image = apply_inpainting(input_image_path, blurred_mask, prompt)
        upscaled_image = upscale_image_with_realesrgan(inpainted_image)
        resized_image = resize_image_to_original(upscaled_image, input_image_path)
    
        return resized_image
    

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()

    def check_login(self, username, password):
        """
        Check if the provided username and password are correct.

        :param username: The username entered by the user.
        :param password: The password entered by the user.
        :return: Tuple (True, user_id) if login is successful, else (False, None).
        """
        user = self.user_repo.get_user_by_username(username)
        if user:
            user_id, db_username, db_password = user

            # If passwords are stored in plain text (not recommended)
            if password == db_password:
                return True, user_id

        return False, None
    
    def username_exists(self, username):
        """
        Check if a username exists in the database.

        :param username: The username to check.
        :return: True if the username exists, False otherwise.
        """
        user = self.user_repo.get_user_by_username(username)
        return user is not None  # If a user is found, return True, else False

    def register_user(self, name, username, email, password, city=None, region=None):
        self.user_repo.create_user(name, username, email, password, city, region)

    def get_user_details(self, user_id):
        return self.user_repo.get_user(user_id)

    def update_user_info(self, user_id, **kwargs):
        self.user_repo.update_user(user_id, **kwargs)

    def delete_user_account(self, user_id):
        self.user_repo.delete_user(user_id)


class ProductService:
    def __init__(self):
        self.product_repo = ProductRepository()

    # Placeholder functions to improve image and text
    def improve_image(self, image_url):
        return f"enhanced_{image_url}"

    def improve_text(self, header_text):
        return f"Improved {header_text}"

    def generate_description(self, header_text):
        return f"Generated description for {header_text}"

    def add_product(self, user_id, header_text, image_url):
        enhanced_image = self.improve_image(image_url)
        improved_text = self.improve_text(header_text)
        description = self.generate_description(header_text)
        self.product_repo.create_product(user_id, header_text, image_url, enhanced_image, description)

    def get_product_info(self, product_id):
        return self.product_repo.get_product(product_id)

    def update_product_info(self, product_id, **kwargs):
        self.product_repo.update_product(product_id, **kwargs)

    def delete_product(self, product_id):
        self.product_repo.delete_product(product_id)


app = FastAPI()
vision_model = VisionModel()

@app.post("/process-image/")
async def process_image(input_image: UploadFile = File(...), prompt: str = Form(...)):
    # Save the uploaded image temporarily
    input_image_data = await input_image.read()
    input_image = Image.open(io.BytesIO(input_image_data))

    # Save the image to a temporary path for processing
    temp_image_path = "temp_input_image.png"
    input_image.save(temp_image_path)

    # Call the process_image_pipeline method with the temporary image path
    processed_image = vision_model.process_image_pipeline(temp_image_path, prompt)

    # Convert the processed image to bytes for the response
    output_image_bytes = io.BytesIO()
    processed_image.save(output_image_bytes, format='PNG')
    output_image_bytes.seek(0)

    # Remove the temporary image file
    # os.remove(temp_image_path)  # Uncomment if you want to delete the temporary file after processing

    return StreamingResponse(output_image_bytes, media_type="image/png")