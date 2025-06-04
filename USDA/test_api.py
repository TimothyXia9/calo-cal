import requests
import json


class USDAFoodAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.nal.usda.gov/fdc/v1"

    def search_food(self, food_name, page_size=5):
        """搜索食物"""
        url = f"{self.base_url}/foods/search"
        params = {
            "api_key": self.api_key,
            "query": food_name,
            "pageSize": page_size,
            "dataType": ["Foundation", "SR Legacy"],  # 推荐数据类型
            "sortBy": "dataType.keyword",
            "sortOrder": "asc",
        }

        response = requests.get(url, params=params)
        return response.json()

    def get_food_details(self, fdc_id):
        """获取食物详细营养信息"""
        url = f"{self.base_url}/food/{fdc_id}"
        params = {"api_key": self.api_key}

        response = requests.get(url, params=params)
        return response.json()

    def get_calories_per_100g(self, food_data):
        """提取每100克的卡路里"""
        for nutrient in food_data.get("foodNutrients", []):
            # 能量的nutrient ID通常是208
            if nutrient.get("nutrient", {}).get("id") == 208:
                return nutrient.get("amount", 0)
        return 0
