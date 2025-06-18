import requests
import json
import logging
import dotenv
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class USDAFoodAPI:
    def __init__(self, api_key: Optional[str] = None):
        dotenv.load_dotenv()
        self.api_key = (
            api_key if api_key is not None else dotenv.get_key(".env", "USDA_API")
        )
        self.base_url = "https://api.nal.usda.gov/fdc/v1"

        if not self.api_key:
            raise ValueError(
                "USDA API key is required. Set USDA_API in .env file or pass as parameter."
            )

        logger.info(
            f"USDA API initialized with key: {self.api_key[:8]}..."
        )  # 只显示前8位

    def search_food(self, food_name: str, page_size: int = 5) -> Dict:
        """搜索食物"""
        logger.info(f"搜索食物: {food_name}")
        url = f"{self.base_url}/foods/search"
        params = {
            "api_key": self.api_key,
            "query": food_name,
            "pageSize": page_size,
            "dataType": ["Foundation", "SR Legacy"],  # 推荐数据类型
            "sortBy": "dataType.keyword",
            "sortOrder": "asc",
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            foods_count = len(result.get("foods", []))
            logger.info(f"找到 {foods_count} 个食物结果")

            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"搜索食物API请求失败: {e}")
            return {"foods": [], "error": str(e)}

    def get_food_details(self, fdc_id: int) -> Dict:
        """获取食物详细营养信息"""
        logger.info(f"获取食物详情: FDC ID {fdc_id}")
        url = f"{self.base_url}/food/{fdc_id}"
        params = {"api_key": self.api_key}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            food_name = result.get("description", "未知")
            nutrients_count = len(result.get("foodNutrients", []))
            logger.info(f"获取食物详情成功: {food_name}, {nutrients_count} 个营养素")

            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"获取食物详情API请求失败: {e}")
            return {"error": str(e)}

    def get_calories_per_100g(self, food_data: Dict) -> float:
        """提取每100克的卡路里"""
        if "error" in food_data:
            return 0.0

        for nutrient in food_data.get("foodNutrients", []):
            # 能量的nutrient ID通常是208
            if nutrient.get("nutrient", {}).get("id") == 208:
                amount = nutrient.get("amount", 0)
                logger.info(f"找到卡路里信息: {amount} kcal/100g")
                return float(amount)

        logger.warning("未找到卡路里信息")
        return 0.0

    def get_comprehensive_nutrition(self, food_data: Dict) -> Dict:
        """获取全面的营养信息"""
        if "error" in food_data:
            return {"error": food_data["error"]}

        nutrition = {
            "name": food_data.get("description", "未知"),
            "fdc_id": food_data.get("fdcId"),
            "calories": 0,
            "protein": 0,
            "fat": 0,
            "carbs": 0,
            "fiber": 0,
            "sugar": 0,
        }

        # 营养素ID映射 (包含多种可能的ID)
        nutrient_map = {
            # 能量/卡路里
            208: "calories",   # 传统能量ID
            2047: "calories",  # Atwater General Factors 能量
            2048: "calories",  # Atwater Specific Factors 能量
            
            # 蛋白质
            203: "protein",    # 传统蛋白质ID
            1003: "protein",   # Protein
            
            # 脂肪
            204: "fat",        # 传统总脂肪ID
            1004: "fat",       # Total lipid (fat)
            
            # 碳水化合物
            205: "carbs",      # 传统总碳水化合物ID
            1005: "carbs",     # Carbohydrate, by difference
            1050: "carbs",     # Carbohydrate, by summation
            
            # 纤维
            291: "fiber",      # 传统膳食纤维ID
            1079: "fiber",     # Fiber, total dietary
            
            # 糖
            269: "sugar",      # 传统总糖ID
            1063: "sugar",     # Sugars, Total
            2000: "sugar",     # Total Sugars
        }

        for nutrient in food_data.get("foodNutrients", []):
            nutrient_id = nutrient.get("nutrient", {}).get("id")
            if nutrient_id in nutrient_map:
                key = nutrient_map[nutrient_id]
                amount = float(nutrient.get("amount", 0))
                # 对于有多个可能ID的营养素，取第一个非零值
                if nutrition[key] == 0 or amount > 0:
                    nutrition[key] = amount

        logger.info(f"营养信息提取完成: {nutrition['name']}")
        return nutrition

    def search_and_get_nutrition(self, food_name: str) -> Optional[Dict]:
        """搜索食物并获取营养信息的便捷方法"""
        search_results = self.search_food(food_name)

        if not search_results.get("foods"):
            logger.warning(f"未找到食物: {food_name}")
            return None

        # 取第一个结果
        first_food = search_results["foods"][0]
        fdc_id = first_food.get("fdcId")

        if not fdc_id:
            logger.error("未找到有效的FDC ID")
            return None

        # 获取详细信息
        food_details = self.get_food_details(fdc_id)
        nutrition = self.get_comprehensive_nutrition(food_details)

        return nutrition


def test_usda_api():
    """测试USDA API功能"""
    print("=" * 60)
    print("USDA Food API 测试")
    print("=" * 60)

    # 检查API密钥
    try:
        api = USDAFoodAPI()
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print("\n📝 设置说明:")
        print("1. 访问 https://fdc.nal.usda.gov/api-key-signup.html 获取免费API密钥")
        print("2. 在项目根目录创建 .env 文件")
        print("3. 添加以下内容到 .env 文件:")
        print("   USDA_API=your_api_key_here")
        print("\n💡 或者直接传入API密钥测试:")
        print("   api = USDAFoodAPI(api_key='your_key')")
        return

    # 测试食物列表
    test_foods = ["apple", "chicken breast", "brown rice", "broccoli", "salmon"]

    try:
        for food_name in test_foods:
            print(f"\n🔍 测试食物: {food_name}")
            print("-" * 40)

            # 使用便捷方法获取营养信息
            nutrition = api.search_and_get_nutrition(food_name)

            if nutrition and "error" not in nutrition:
                print(f"✅ 食物名称: {nutrition['name']}")
                print(f"   FDC ID: {nutrition['fdc_id']}")
                print(f"   卡路里: {nutrition['calories']:.1f} kcal/100g")
                print(f"   蛋白质: {nutrition['protein']:.1f} g/100g")
                print(f"   脂肪: {nutrition['fat']:.1f} g/100g")
                print(f"   碳水化合物: {nutrition['carbs']:.1f} g/100g")
                print(f"   纤维: {nutrition['fiber']:.1f} g/100g")
                print(f"   糖: {nutrition['sugar']:.1f} g/100g")
            else:
                print(f"❌ 未找到食物或获取失败")

        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 测试失败: {e}")


def demo_with_api_key():
    """演示如何使用API密钥"""
    print("\n" + "=" * 60)
    print("DEMO: 使用API密钥测试 (需要替换为真实密钥)")
    print("=" * 60)

    # 使用真实API密钥进行测试
    api_key = "eJ9uiMbB3QMS3eNEAvDcIiVWbL1r9Mbxp4QhgZve"
    
    try:
        api = USDAFoodAPI(api_key=api_key)
        print(f"✅ API密钥验证成功")
        
        # 测试多个食物查询
        test_foods = ["apple", "chicken breast", "brown rice"]
        
        for test_food in test_foods:
            print(f"\n🔍 测试查询: {test_food}")
            print("-" * 40)
            
            # 先搜索看看有什么选项
            search_results = api.search_food(test_food, page_size=3)
            print("🔍 搜索结果:")
            for i, food in enumerate(search_results.get("foods", [])[:3]):
                print(f"   {i+1}. {food.get('description')} (ID: {food.get('fdcId')})")
            
            # 获取详细信息并检查原始数据
            if search_results.get("foods"):
                fdc_id = search_results["foods"][0]["fdcId"]
                food_details = api.get_food_details(fdc_id)
                
                print(f"\n🔬 原始营养数据 (全部):")
                nutrients = food_details.get("foodNutrients", [])
                for nutrient in nutrients:
                    nutrient_info = nutrient.get("nutrient", {})
                    amount = nutrient.get('amount', 0)
                    if amount > 0:  # 只显示有数值的营养素
                        print(f"   ID {nutrient_info.get('id')}: {nutrient_info.get('name')} = {amount} {nutrient_info.get('unitName', '')}")
                
                # 获取营养信息
                nutrition = api.get_comprehensive_nutrition(food_details)
                
                if nutrition and "error" not in nutrition:
                    print(f"\n✅ 解析的营养信息:")
                    print(f"   食物名称: {nutrition['name']}")
                    print(f"   FDC ID: {nutrition['fdc_id']}")
                    print(f"   卡路里: {nutrition['calories']:.1f} kcal/100g")
                    print(f"   蛋白质: {nutrition['protein']:.1f} g/100g")
                    print(f"   脂肪: {nutrition['fat']:.1f} g/100g")
                    print(f"   碳水化合物: {nutrition['carbs']:.1f} g/100g")
                    print(f"   纤维: {nutrition['fiber']:.1f} g/100g")
                    print(f"   糖: {nutrition['sugar']:.1f} g/100g")
                else:
                    print(f"❌ 营养信息解析失败")
            
            break  # 只测试第一个食物
            
    except Exception as e:
        print(f"❌ API测试失败: {e}")


if __name__ == "__main__":
    test_usda_api()
    demo_with_api_key()
