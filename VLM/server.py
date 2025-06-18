import logging
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from InternVL3 import InternVL3_model, analyze_food_image

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

logger.info("正在加载模型...")
intern_model = InternVL3_model(model_path="OpenGVLab/InternVL3-2B")
model, tokenizer = intern_model.model, intern_model.tokenizer
device = intern_model.device
logger.info(f"模型加载完成，使用设备: {device}")


@app.get("/")
async def root():
    return {"message": "食物卡路里分析API", "status": "running", "device": device}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "device": device, "model": "InternVL3-2B"}


@app.post("/analyze")
async def analyze(file: UploadFile):
    logger.info(f"收到分析请求: {file.filename}, 大小: {file.size} bytes")

    with open("temp.jpg", "wb") as f:
        f.write(await file.read())

    logger.info("开始进行食物分析...")
    result = analyze_food_image(
        "temp.jpg", model, tokenizer, max_tiles=4, device=device
    )

    logger.info(f"分析完成，结果长度: {len(result)} 字符")
    return {"result": result}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
