from unsloth import FastLanguageModel

class ChatLLAMAdolu:
    def __init__(self):
        self.max_seq_length = 2048 # Choose any! We auto support RoPE Scaling internally!
        self.dtype = None # None for auto detection. Float16 for Tesla T4, V100, Bfloat16 for Ampere+
        self.load_in_4bit = False # Use 4bit quantization to reduce memory usage. Can be False.
        self.init_model()
    
    def init_model(self):
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name = "lora_model", # YOUR MODEL YOU USED FOR TRAINING
            max_seq_length = self.max_seq_length,
            dtype = self.dtype,
            load_in_4bit = self.load_in_4bit,
        )
        FastLanguageModel.for_inference(self.model) # Enable native 2x faster inference
        
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
        return generated_text
    
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
        found_words = []
        words_in_message = message.split()

        for entry in self.regional_words:
            word = entry["Kelime"].lower()
            for message_word in words_in_message:
                message_word_lower = message_word.lower()
                
                if word in message_word_lower:
                    found_words.append(entry)

        return found_words
