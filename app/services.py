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
from unsloth import FastLanguageModel
import json
import difflib
import io
import re

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
    
        blurred_mask = self.vision_pipline.mask_processor.blur(mask_image, blur_factor=20)
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
        output_image = self.vision_pipline(prompt=prompt, image=input_image, mask_image=mask, generator=self.vision_generator).images[0]

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
        mask = self.get_object_mask(input_image_path)
        inverted_mask = self.invert_mask(mask)
        blurred_mask = self.blur_mask(inverted_mask)

        inpainted_image = self.apply_inpainting(input_image_path, blurred_mask, prompt)
        upscaled_image = self.upscale_image_with_realesrgan(inpainted_image)
        resized_image = self.resize_image_to_original(upscaled_image, input_image_path)
    
        return resized_image
    

class ChatLLAMAdolu:
    def __init__(self):
        self.max_seq_length = 2048 # Choose any! We auto support RoPE Scaling internally!
        self.dtype = None # None for auto detection. Float16 for Tesla T4, V100, Bfloat16 for Ampere+
        self.load_in_4bit = False # Use 4bit quantization to reduce memory usage. Can be False.
        self.init_model()
        self.load_regional_dictionary() 
    
    def init_model(self):
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name = "../TextModel/lora_model", # YOUR MODEL YOU USED FOR TRAINING
            max_seq_length = self.max_seq_length,
            dtype = self.dtype,
            load_in_4bit = self.load_in_4bit,
        )
        FastLanguageModel.for_inference(self.model) # Enable native 2x faster inference
        
    def load_regional_dictionary(self):
        # Burada sözlüğü json dosyasından yüklüyoruz.
        try:
            with open('dataset/dictionary.json', 'r', encoding='utf-8') as file:
                self.regional_words = json.load(file)
        except FileNotFoundError:
            print("dictionary.json dosyası bulunamadı!")
            self.regional_words = []    
        
    def ask_model(self, message):
        messages = self.message_formatter(message)
        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True, # Must add for generation
            return_tensors="pt",
        ).to("cuda")
        
        outputs = self.model.generate(input_ids=inputs, max_new_tokens=256, use_cache=True, temperature=0.1, min_p=0.5)
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        cleaned_text = self.split_text(generated_text)
        return cleaned_text
    
    def message_formatter(self, message):
        regional_words = self.find_regional_words(message)
        content = f"Kullanıcı inputu: \"{message}\" Yöresel kelimeler: {regional_words}"
        messages = [
            {
                "role": "system",
                "content": "You are a marketing bot that is specialized to make natural language product titles professional, eye-catching and sales-ready. Make user-entered sales descriptions professional. Also, if the user input contains regional words, you can find the meaning of this in the text below. When translating your descriptions into a global and professional form, take these words and their descriptions into account. In response: Use the template \"\"\"\n\"Profesyonel Başlık\": ...\n\"Profesyonel Açıklama\": ...\n\"\"\". If the user enters long and unprofessional additional descriptions, do not display them in the \"Profesyonel Başlık\" section, but add them to the \"Profesyonel Açıklama\" section."
            },
            {
                "role": "user",
                "content": content
            },
        ]
        return messages  # Fix: Return messages for further processing
        
    def find_regional_words(self, message):
        found_word = None
        best_similarity = 0
    
        words_in_message = message.split()  # Mesajdaki kelimeleri böl
    
        # Her bir sözlük kaydını tara
        for entry in self.regional_words:
            regional_word = entry["Kelime"].lower()  # Küçük harfe çevir
            for message_word in words_in_message:
                message_word_lower = message_word.lower()  # Mesajdaki kelimeyi küçük harfe çevir
            
                # Benzerlik oranını hesapla
                similarity = difflib.SequenceMatcher(None, regional_word, message_word_lower).ratio()
            
                # Eğer benzerlik oranı en yüksek ise, onu al
                if similarity > best_similarity:
                    best_similarity = similarity
                    found_word = entry

        # Eğer bir eşleşme bulduysak, en iyi sonucu döndür
        if found_word and best_similarity > 0.6:  # Eşik değeri %60
            return found_word
        else:
            return {}  # Eşleşme yoksa boş dictionary döndür
        
    def split_text(self, raw):
        # Extract "Profesyonel Başlık" and "Profesyonel Açıklama" using regex
        title_match = re.search(r'\"Profesyonel Başlık\": \"(.*?)\"', raw)
        description_match = re.search(r'\"Profesyonel Açıklama\": \"(.*?)\"', raw)

        pro_dict = {"pro_header":"", "pro_desc": ""}
        if title_match:
            professional_title = title_match.group(1)
            pro_dict["pro_header"] = professional_title

        if description_match:
            professional_description = description_match.group(1)
            pro_dict["pro_desc"] = professional_description

        return pro_dict

    
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
chat = ChatLLAMAdolu()

from PIL import UnidentifiedImageError
from pydantic import BaseModel
import logging

@app.post("/process-image/")
async def process_image(input_image: UploadFile = File(...), prompt: str = Form(...)):
    logging.info("Image upload process started.")
    try:
        # Save the uploaded image temporarily
        input_image_data = await input_image.read()
        input_image = Image.open(io.BytesIO(input_image_data))
        temp_image_path = os.path.join("/tmp", "temp_input_image.png")
        
        logging.info(f"Saving image to {temp_image_path}")
        input_image.save(temp_image_path)
        
        if not os.path.exists(temp_image_path):
            raise FileNotFoundError(f"Geçici dosya bulunamadı: {temp_image_path}")
        
        logging.info(f"Processing image at {temp_image_path}")
        processed_image = vision_model.process_image_pipeline(temp_image_path, prompt)

        # İşlenen görüntünün geçerli olup olmadığını kontrol et
        if processed_image is None:
            raise ValueError("Processed image is None.")
        
        try:
            # İşlenmiş görüntüyü kaydetmeye çalış
            output_image_bytes = io.BytesIO()
            processed_image.save(output_image_bytes, format='PNG')
            output_image_bytes.seek(0)
        except UnidentifiedImageError as e:
            raise ValueError(f"Processed image cannot be identified as a valid image: {e}")
        
        logging.info("Image processing completed successfully.")

        return StreamingResponse(output_image_bytes, media_type="image/png")

    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        return {"error": str(e)}

    
class AskModelRequest(BaseModel):
    message: str

@app.post("/ask-model/")
async def ask_model(request: AskModelRequest):
    message = request.message
    res = chat.ask_model(message)
    response = {"response": res}
    return response