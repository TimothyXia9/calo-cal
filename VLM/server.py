from fastapi import FastAPI, UploadFile
from InternVL3 import InternVL3_model, analyze_food_image
import torch

app = FastAPI()

# 模型只加载一次！
intern_model = InternVL3_model(model_path="OpenGVLab/InternVL3-2B")
model, tokenizer = intern_model.model, intern_model.tokenizer
device = intern_model.device


@app.post("/analyze")
async def analyze(file: UploadFile):
    with open("temp.jpg", "wb") as f:
        f.write(await file.read())

    result = analyze_food_image(
        "temp.jpg", model, tokenizer, max_tiles=4, device=device
    )
    return {"result": result}
