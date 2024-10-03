from unsloth import FastLanguageModel
import json
import difflib
import re

class ChatLLAMAdolu:
    def __init__(self):
        self.max_seq_length = 2048 # Choose any! We auto support RoPE Scaling internally!
        self.dtype = None # None for auto detection. Float16 for Tesla T4, V100, Bfloat16 for Ampere+
        self.load_in_4bit = False # Use 4bit quantization to reduce memory usage. Can be False.
        self.init_model()
        self.load_regional_dictionary() 
    
    def init_model(self):
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name = "lora_model", # YOUR MODEL YOU USED FOR TRAINING
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
