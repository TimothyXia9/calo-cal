"""
USDA营养数据库服务
用于与VLM分析结果集成，提供准确的营养信息
"""

import logging
from typing import Dict, List, Optional

from test_api import USDAFoodAPI

logger = logging.getLogger(__name__)


class USDANutritionService:
    """USDA营养服务，用于VLM结果的营养信息查询"""
    
    def __init__(self, api_key: Optional[str] = None):
        try:
            self.usda_api = USDAFoodAPI(api_key)
            self.is_available = True
            logger.info("USDA营养服务初始化成功")
        except ValueError as e:
            logger.warning(f"USDA API不可用: {e}")
            self.is_available = False
    
    def get_nutrition_for_food_list(self, foods: List[Dict]) -> List[Dict]:
        """
        为VLM识别的食物列表获取营养信息
        
        Args:
            foods: VLM识别的食物列表，格式:
                [{"en_name": "apple", "estimated_weight_grams": 150, "confidence": 0.9}]
        
        Returns:
            包含营养信息的食物列表
        """
        if not self.is_available:
            logger.warning("USDA API不可用，使用估算营养信息")
            return self._get_estimated_nutrition(foods)
        
        enriched_foods = []
        
        for food in foods:
            food_name = food.get("en_name", "")
            weight_grams = food.get("estimated_weight_grams", 0)
            
            logger.info(f"查询营养信息: {food_name} ({weight_grams}g)")
            
            # 获取USDA营养信息
            nutrition = self.usda_api.search_and_get_nutrition(food_name)
            
            if nutrition and "error" not in nutrition:
                # 计算实际重量的营养信息
                actual_nutrition = self._calculate_nutrition_for_weight(
                    nutrition, weight_grams
                )
                
                enriched_food = {
                    **food,  # 保留原始VLM信息
                    "nutrition": actual_nutrition,
                    "usda_source": True
                }
            else:
                # 使用估算营养信息
                estimated_nutrition = self._estimate_single_food_nutrition(
                    food_name, weight_grams
                )
                
                enriched_food = {
                    **food,
                    "nutrition": estimated_nutrition,
                    "usda_source": False
                }
            
            enriched_foods.append(enriched_food)
        
        return enriched_foods
    
    def _calculate_nutrition_for_weight(self, nutrition_per_100g: Dict, weight_grams: float) -> Dict:
        """根据重量计算实际营养信息"""
        multiplier = weight_grams / 100.0
        
        return {
            "calories": round(nutrition_per_100g["calories"] * multiplier, 1),
            "protein": round(nutrition_per_100g["protein"] * multiplier, 1),
            "fat": round(nutrition_per_100g["fat"] * multiplier, 1),
            "carbs": round(nutrition_per_100g["carbs"] * multiplier, 1),
            "fiber": round(nutrition_per_100g["fiber"] * multiplier, 1),
            "sugar": round(nutrition_per_100g["sugar"] * multiplier, 1),
            "weight_grams": weight_grams,
            "usda_name": nutrition_per_100g["name"],
            "fdc_id": nutrition_per_100g["fdc_id"]
        }
    
    def _get_estimated_nutrition(self, foods: List[Dict]) -> List[Dict]:
        """当USDA API不可用时，使用估算营养信息"""
        enriched_foods = []
        
        for food in foods:
            food_name = food.get("en_name", "")
            weight_grams = food.get("estimated_weight_grams", 0)
            
            estimated_nutrition = self._estimate_single_food_nutrition(
                food_name, weight_grams
            )
            
            enriched_food = {
                **food,
                "nutrition": estimated_nutrition,
                "usda_source": False
            }
            enriched_foods.append(enriched_food)
        
        return enriched_foods
    
    def _estimate_single_food_nutrition(self, food_name: str, weight_grams: float) -> Dict:
        """估算单个食物的营养信息"""
        # 简化的营养估算数据库（每100g）
        nutrition_db = {
            # 水果类
            "apple": {"calories": 52, "protein": 0.3, "fat": 0.2, "carbs": 14, "fiber": 2.4, "sugar": 10},
            "banana": {"calories": 89, "protein": 1.1, "fat": 0.3, "carbs": 23, "fiber": 2.6, "sugar": 12},
            "orange": {"calories": 47, "protein": 0.9, "fat": 0.1, "carbs": 12, "fiber": 2.4, "sugar": 9},
            
            # 蔬菜类
            "broccoli": {"calories": 34, "protein": 2.8, "fat": 0.4, "carbs": 7, "fiber": 2.6, "sugar": 1.5},
            "carrot": {"calories": 41, "protein": 0.9, "fat": 0.2, "carbs": 10, "fiber": 2.8, "sugar": 4.7},
            "tomato": {"calories": 18, "protein": 0.9, "fat": 0.2, "carbs": 3.9, "fiber": 1.2, "sugar": 2.6},
            
            # 肉类
            "chicken": {"calories": 165, "protein": 31, "fat": 3.6, "carbs": 0, "fiber": 0, "sugar": 0},
            "beef": {"calories": 250, "protein": 26, "fat": 15, "carbs": 0, "fiber": 0, "sugar": 0},
            "pork": {"calories": 242, "protein": 27, "fat": 14, "carbs": 0, "fiber": 0, "sugar": 0},
            "fish": {"calories": 206, "protein": 22, "fat": 12, "carbs": 0, "fiber": 0, "sugar": 0},
            
            # 主食类
            "rice": {"calories": 130, "protein": 2.7, "fat": 0.3, "carbs": 28, "fiber": 0.4, "sugar": 0.1},
            "bread": {"calories": 265, "protein": 9, "fat": 3.2, "carbs": 49, "fiber": 2.7, "sugar": 5},
            "pasta": {"calories": 131, "protein": 5, "fat": 1.1, "carbs": 25, "fiber": 1.8, "sugar": 0.6},
            
            # 默认值
            "default": {"calories": 150, "protein": 5, "fat": 5, "carbs": 20, "fiber": 2, "sugar": 5}
        }
        
        # 查找匹配的营养信息
        food_name_lower = food_name.lower()
        nutrition_per_100g = nutrition_db.get("default", nutrition_db["default"])
        
        for key, value in nutrition_db.items():
            if key in food_name_lower or food_name_lower in key:
                nutrition_per_100g = value
                break
        
        # 计算实际重量的营养信息
        multiplier = weight_grams / 100.0
        
        return {
            "calories": round(nutrition_per_100g["calories"] * multiplier, 1),
            "protein": round(nutrition_per_100g["protein"] * multiplier, 1),
            "fat": round(nutrition_per_100g["fat"] * multiplier, 1),
            "carbs": round(nutrition_per_100g["carbs"] * multiplier, 1),
            "fiber": round(nutrition_per_100g["fiber"] * multiplier, 1),
            "sugar": round(nutrition_per_100g["sugar"] * multiplier, 1),
            "weight_grams": weight_grams,
            "estimated": True
        }
    
    def get_total_nutrition(self, foods_with_nutrition: List[Dict]) -> Dict:
        """计算总营养信息"""
        total = {
            "total_calories": 0,
            "total_protein": 0,
            "total_fat": 0,
            "total_carbs": 0,
            "total_fiber": 0,
            "total_sugar": 0,
            "total_weight": 0,
            "food_count": len(foods_with_nutrition)
        }
        
        for food in foods_with_nutrition:
            nutrition = food.get("nutrition", {})
            total["total_calories"] += nutrition.get("calories", 0)
            total["total_protein"] += nutrition.get("protein", 0)
            total["total_fat"] += nutrition.get("fat", 0)
            total["total_carbs"] += nutrition.get("carbs", 0)
            total["total_fiber"] += nutrition.get("fiber", 0)
            total["total_sugar"] += nutrition.get("sugar", 0)
            total["total_weight"] += nutrition.get("weight_grams", 0)
        
        # 四舍五入
        for key in total:
            if isinstance(total[key], float):
                total[key] = round(total[key], 1)
        
        return total


# 测试函数
def test_nutrition_service():
    """测试营养服务"""
    print("=" * 60)
    print("USDA营养服务测试")
    print("=" * 60)
    
    # 模拟VLM识别的食物列表
    vlm_foods = [
        {"en_name": "apple", "estimated_weight_grams": 150, "confidence": 0.9, "method": "raw"},
        {"en_name": "chicken breast", "estimated_weight_grams": 100, "confidence": 0.85, "method": "grilled"},
        {"en_name": "brown rice", "estimated_weight_grams": 200, "confidence": 0.8, "method": "cooked"}
    ]
    
    service = USDANutritionService()
    
    print(f"USDA API 可用性: {'✅ 可用' if service.is_available else '❌ 不可用'}")
    print(f"测试食物数量: {len(vlm_foods)}")
    
    # 获取营养信息
    enriched_foods = service.get_nutrition_for_food_list(vlm_foods)
    
    print("\n🍎 详细营养信息:")
    print("-" * 60)
    
    for food in enriched_foods:
        nutrition = food["nutrition"]
        source = "USDA数据库" if food["usda_source"] else "估算数据"
        
        print(f"\n📍 {food['en_name']} ({food['estimated_weight_grams']}g)")
        print(f"   数据来源: {source}")
        print(f"   卡路里: {nutrition['calories']:.1f} kcal")
        print(f"   蛋白质: {nutrition['protein']:.1f}g")
        print(f"   脂肪: {nutrition['fat']:.1f}g")
        print(f"   碳水: {nutrition['carbs']:.1f}g")
        print(f"   纤维: {nutrition['fiber']:.1f}g")
        print(f"   糖: {nutrition['sugar']:.1f}g")
    
    # 计算总营养
    total_nutrition = service.get_total_nutrition(enriched_foods)
    
    print("\n📊 总营养统计:")
    print("-" * 60)
    print(f"总卡路里: {total_nutrition['total_calories']:.1f} kcal")
    print(f"总蛋白质: {total_nutrition['total_protein']:.1f}g")
    print(f"总脂肪: {total_nutrition['total_fat']:.1f}g")
    print(f"总碳水: {total_nutrition['total_carbs']:.1f}g")
    print(f"总重量: {total_nutrition['total_weight']:.0f}g")
    print(f"食物种类: {total_nutrition['food_count']} 种")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    test_nutrition_service()