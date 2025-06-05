def create_food_prompt():
    """创建食物分析的结构化提示词"""
    prompt = """
    Analyze food in this image. Output JSON format:
    {
      "foods": [
        {
          "en_name": "food name",
          "estimated_weight_grams": weight_number,
          "confidence": 0.0-1.0,
          "method": "raw/cooked/fried/steamed etc.",
        }
      ]
    }

    Requirements:
    - Estimate portions carefully
    - Use USDA database food names
    - Reasonable weight estimates
    - Give median if uncertain
"""
    return prompt
