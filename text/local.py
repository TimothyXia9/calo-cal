from transformers import MarianMTModel, MarianTokenizer


class LocalTranslator:
    def __init__(self):
        # 中译英
        self.zh_en_model_name = "Helsinki-NLP/opus-mt-zh-en"
        self.zh_en_tokenizer = MarianTokenizer.from_pretrained(self.zh_en_model_name)
        self.zh_en_model = MarianMTModel.from_pretrained(self.zh_en_model_name)

        # 英译中
        self.en_zh_model_name = "Helsinki-NLP/opus-mt-en-zh"
        self.en_zh_tokenizer = MarianTokenizer.from_pretrained(self.en_zh_model_name)
        self.en_zh_model = MarianMTModel.from_pretrained(self.en_zh_model_name)

    def zh_to_en(self, chinese_text):
        inputs = self.zh_en_tokenizer(chinese_text, return_tensors="pt", padding=True)
        translated = self.zh_en_model.generate(**inputs)
        return self.zh_en_tokenizer.decode(translated[0], skip_special_tokens=True)

    def en_to_zh(self, english_text):
        inputs = self.en_zh_tokenizer(english_text, return_tensors="pt", padding=True)
        translated = self.en_zh_model.generate(**inputs)
        return self.en_zh_tokenizer.decode(translated[0], skip_special_tokens=True)


translator = LocalTranslator()
english_result = translator.zh_to_en("一碗带肉丸的意面和西兰花")
print(english_result)
