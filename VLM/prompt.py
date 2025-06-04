def create_prompt():
    """创建食物分析的结构化提示词"""
    prompt = """
请分析这张图片中的食物，并以JSON格式输出结果。严格按照以下格式：

{
  "foods": [
    {
      "name": "食物英文名称",
      "chinese_name": "食物中文名称",
      "estimated_weight_grams": 估算重量（数字）,
      "confidence": 0.8,
      "notes": "任何补充说明",
      "cooking_method": "raw/cooked/fried/steamed等"
    }
  ],
}

要求：
1. 仔细观察每种食物的分量
2. 重量估算要合理（参考标准餐具大小）
3. 食物名称使用USDA数据库中常见的英文名称
4. 如果不确定具体重量，给出合理范围的中值
5. confidence表示识别的置信度（0-1）
"""
    return prompt
