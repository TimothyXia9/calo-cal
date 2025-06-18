"""
综合API服务
整合VLM分析结果和USDA营养数据，为前端提供完整的食物分析服务
"""

import logging
import json
from typing import Dict, List
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests

# 导入USDA服务
import sys

sys.path.append("USDA")
from usda_service import USDANutritionService

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="食物卡路里分析综合API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务实例
vlm_service_url = "http://localhost:8000"
usda_service = None


def initialize_services():
    """初始化服务"""
    global usda_service
    logger.info("正在初始化API服务...")

    # 初始化USDA服务
    try:
        usda_service = USDANutritionService()
        logger.info("USDA营养服务初始化完成")
    except Exception as e:
        logger.warning(f"USDA服务初始化失败: {e}")
        usda_service = None


# 在导入后立即初始化
initialize_services()


def check_vlm_service():
    """检查VLM服务状态"""
    try:
        response = requests.get(f"{vlm_service_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"VLM服务连接正常: {data}")
        else:
            logger.warning(f"VLM服务响应异常: {response.status_code}")
    except Exception as e:
        logger.error(f"无法连接到VLM服务: {e}")


@app.get("/")
async def root():
    """根路径信息"""
    return {
        "message": "食物卡路里分析综合API",
        "status": "running",
        "services": {
            "vlm_service": vlm_service_url,
            "usda_service": (
                "available"
                if usda_service and usda_service.is_available
                else "fallback"
            ),
        },
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "services": {
            "api_service": "running",
            "vlm_service": vlm_service_url,
            "usda_service": (
                "available"
                if usda_service and usda_service.is_available
                else "fallback"
            ),
        },
    }


@app.post("/analyze")
async def analyze_food_complete(file: UploadFile):
    """
    完整的食物分析API
    1. 使用VLM分析图片
    2. 获取USDA营养数据
    3. 返回综合结果
    """
    logger.info(f"收到完整分析请求: {file.filename}, 大小: {file.size} bytes")

    try:
        # Step 1: VLM图像分析
        logger.info("步骤1: 调用VLM服务进行图像分析...")
        vlm_result = await call_vlm_service(file)

        # Step 2: 解析VLM结果
        logger.info("步骤2: 解析VLM分析结果...")
        parsed_vlm = parse_vlm_result(vlm_result)

        # Step 3: 获取USDA营养信息
        logger.info("步骤3: 获取USDA营养信息...")
        enriched_foods = get_nutrition_data(parsed_vlm.get("foods", []))

        # Step 4: 计算总营养信息
        logger.info("步骤4: 计算总营养信息...")
        total_nutrition = calculate_total_nutrition(enriched_foods)

        # 构建完整响应
        complete_result = {
            "success": True,
            "analysis_timestamp": vlm_result.get("timestamp"),
            "raw_vlm_result": vlm_result.get("result", ""),
            "parsed_analysis": {
                "foods": enriched_foods,
                "food_count": len(enriched_foods),
                "total_nutrition": total_nutrition,
            },
            "data_sources": {
                "vlm_model": "InternVL3-2B",
                "nutrition_source": (
                    "USDA"
                    if usda_service and usda_service.is_available
                    else "Estimated"
                ),
            },
        }

        logger.info(
            f"分析完成 - 识别食物: {len(enriched_foods)}种, 总卡路里: {total_nutrition.get('calories', 0)}"
        )
        return JSONResponse(content=complete_result)

    except Exception as e:
        logger.error(f"完整分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/analyze/vlm-only")
async def analyze_vlm_only(file: UploadFile):
    """仅VLM分析，不进行营养数据查询"""
    logger.info(f"收到VLM分析请求: {file.filename}")

    try:
        vlm_result = await call_vlm_service(file)
        return JSONResponse(content=vlm_result)
    except Exception as e:
        logger.error(f"VLM分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"VLM分析失败: {str(e)}")


@app.post("/nutrition/lookup")
async def lookup_nutrition(foods: List[Dict]):
    """
    营养信息查询API
    输入格式: [{"en_name": "apple", "estimated_weight_grams": 150}]
    """
    logger.info(f"收到营养信息查询请求: {len(foods)}种食物")

    try:
        enriched_foods = get_nutrition_data(foods)
        total_nutrition = calculate_total_nutrition(enriched_foods)

        return JSONResponse(
            content={
                "success": True,
                "foods": enriched_foods,
                "total_nutrition": total_nutrition,
                "nutrition_source": (
                    "USDA"
                    if usda_service and usda_service.is_available
                    else "Estimated"
                ),
            }
        )

    except Exception as e:
        logger.error(f"营养信息查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"营养信息查询失败: {str(e)}")


async def call_vlm_service(file: UploadFile) -> Dict:
    """调用VLM服务进行图像分析"""
    try:
        # 重置文件指针
        await file.seek(0)
        file_content = await file.read()

        # 使用requests发送请求
        response = requests.post(
            f"{vlm_service_url}/analyze",
            files={"file": (file.filename, file_content, file.content_type)},
            timeout=60,
        )

        if response.status_code != 200:
            raise Exception(f"VLM服务错误 {response.status_code}: {response.text}")

        result = response.json()

        # 添加时间戳
        import datetime

        result["timestamp"] = datetime.datetime.now().isoformat()

        return result

    except Exception as e:
        logger.error(f"VLM服务调用失败: {str(e)}")
        raise Exception(f"VLM服务调用失败: {str(e)}")


def parse_vlm_result(vlm_result: Dict) -> Dict:
    """解析VLM分析结果"""
    try:
        result_text = vlm_result.get("result", "")
        if not result_text:
            return {"foods": []}

        # 尝试解析JSON格式的结果
        try:
            parsed = json.loads(result_text)
            if isinstance(parsed, dict) and "foods" in parsed:
                return parsed
        except json.JSONDecodeError:
            pass

        # 如果不是JSON格式，尝试解析文本格式
        logger.info("尝试解析文本格式的VLM结果")
        foods = parse_text_result(result_text)
        return {"foods": foods}

    except Exception as e:
        logger.error(f"VLM结果解析失败: {str(e)}")
        return {"foods": []}


def parse_text_result(text: str) -> List[Dict]:
    """解析文本格式的VLM结果"""
    foods = []
    lines = text.strip().split("\n")

    current_food = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 简单的文本解析逻辑（可根据实际VLM输出格式调整）
        if "食物:" in line or "Food:" in line:
            if current_food:
                foods.append(current_food)
            food_name = line.split(":")[-1].strip()
            current_food = {
                "en_name": food_name,
                "estimated_weight_grams": 100,  # 默认重量
                "confidence": 0.8,  # 默认置信度
                "method": "unknown",
            }
        elif "重量:" in line or "Weight:" in line:
            try:
                weight_str = line.split(":")[-1].strip()
                weight = float("".join(filter(str.isdigit, weight_str)))
                if weight > 0:
                    current_food["estimated_weight_grams"] = weight
            except:
                pass

    if current_food:
        foods.append(current_food)

    return foods


def get_nutrition_data(foods: List[Dict]) -> List[Dict]:
    """获取食物营养数据"""
    if not foods:
        return []

    try:
        if usda_service and usda_service.is_available:
            logger.info("使用USDA服务获取营养数据")
            return usda_service.get_nutrition_for_food_list(foods)
        else:
            logger.info("使用估算方法获取营养数据")
            return get_estimated_nutrition_data(foods)
    except Exception as e:
        logger.error(f"营养数据获取失败: {str(e)}")
        return get_estimated_nutrition_data(foods)


def get_estimated_nutrition_data(foods: List[Dict]) -> List[Dict]:
    """获取估算营养数据"""
    enriched_foods = []

    # 简化的营养数据库（每100g）
    nutrition_db = {
        "apple": {
            "calories": 52,
            "protein": 0.3,
            "fat": 0.2,
            "carbs": 14,
            "fiber": 2.4,
            "sugar": 10,
        },
        "banana": {
            "calories": 89,
            "protein": 1.1,
            "fat": 0.3,
            "carbs": 23,
            "fiber": 2.6,
            "sugar": 12,
        },
        "orange": {
            "calories": 47,
            "protein": 0.9,
            "fat": 0.1,
            "carbs": 12,
            "fiber": 2.4,
            "sugar": 9,
        },
        "broccoli": {
            "calories": 34,
            "protein": 2.8,
            "fat": 0.4,
            "carbs": 7,
            "fiber": 2.6,
            "sugar": 1.5,
        },
        "carrot": {
            "calories": 41,
            "protein": 0.9,
            "fat": 0.2,
            "carbs": 10,
            "fiber": 2.8,
            "sugar": 4.7,
        },
        "chicken": {
            "calories": 165,
            "protein": 31,
            "fat": 3.6,
            "carbs": 0,
            "fiber": 0,
            "sugar": 0,
        },
        "beef": {
            "calories": 250,
            "protein": 26,
            "fat": 15,
            "carbs": 0,
            "fiber": 0,
            "sugar": 0,
        },
        "rice": {
            "calories": 130,
            "protein": 2.7,
            "fat": 0.3,
            "carbs": 28,
            "fiber": 0.4,
            "sugar": 0.1,
        },
        "bread": {
            "calories": 265,
            "protein": 9,
            "fat": 3.2,
            "carbs": 49,
            "fiber": 2.7,
            "sugar": 5,
        },
        "default": {
            "calories": 150,
            "protein": 5,
            "fat": 5,
            "carbs": 20,
            "fiber": 2,
            "sugar": 5,
        },
    }

    for food in foods:
        food_name = food.get("en_name", "").lower()
        weight_grams = food.get("estimated_weight_grams", 100)

        # 查找匹配的营养信息
        nutrition_per_100g = nutrition_db["default"]
        for key, value in nutrition_db.items():
            if key != "default" and (key in food_name or food_name in key):
                nutrition_per_100g = value
                break

        # 计算实际重量的营养信息
        multiplier = weight_grams / 100.0
        nutrition = {
            "calories": round(nutrition_per_100g["calories"] * multiplier, 1),
            "protein": round(nutrition_per_100g["protein"] * multiplier, 1),
            "fat": round(nutrition_per_100g["fat"] * multiplier, 1),
            "carbs": round(nutrition_per_100g["carbs"] * multiplier, 1),
            "fiber": round(nutrition_per_100g["fiber"] * multiplier, 1),
            "sugar": round(nutrition_per_100g["sugar"] * multiplier, 1),
            "weight_grams": weight_grams,
            "estimated": True,
        }

        enriched_food = {**food, "nutrition": nutrition, "usda_source": False}
        enriched_foods.append(enriched_food)

    return enriched_foods


def calculate_total_nutrition(enriched_foods: List[Dict]) -> Dict:
    """计算总营养信息"""
    total = {
        "calories": 0,
        "protein": 0,
        "fat": 0,
        "carbs": 0,
        "fiber": 0,
        "sugar": 0,
        "total_weight": 0,
        "food_count": len(enriched_foods),
    }

    for food in enriched_foods:
        nutrition = food.get("nutrition", {})
        total["calories"] += nutrition.get("calories", 0)
        total["protein"] += nutrition.get("protein", 0)
        total["fat"] += nutrition.get("fat", 0)
        total["carbs"] += nutrition.get("carbs", 0)
        total["fiber"] += nutrition.get("fiber", 0)
        total["sugar"] += nutrition.get("sugar", 0)
        total["total_weight"] += nutrition.get("weight_grams", 0)

    # 四舍五入
    for key in total:
        if isinstance(total[key], float):
            total[key] = round(total[key], 1)

    return total


@app.get("/test")
async def test_endpoint():
    """测试端点"""
    return {
        "message": "API服务测试成功",
        "status": "ok",
        "services_status": {
            "usda_available": usda_service.is_available if usda_service else False,
            "vlm_service_url": vlm_service_url,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_service:app", host="0.0.0.0", port=8001, reload=True)
