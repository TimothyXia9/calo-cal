## 食物卡路里分析项目总结文档

## 项目概述

基于 Notion 前端 + 本地 Mac 后端的食物卡路里分析系统，用户可通过图片或文字描述记录食物，系统自动分析并计算卡路里含量。

## 技术架构

### 整体架构设计

```
用户输入（Notion）→ Webhook → 本地处理服务 → AI分析 → 营养数据库 → 结果回写（Notion）

```

### 核心组件

1. **前端**：Notion 数据库作为用户界面
2. **后端**：Mac 本地服务处理 AI 推理
3. **AI 模型**：多模态融合分析（图像+文本）
4. **数据源**：营养数据库查询

## Notion 数据库设计

### 主表：Food Log

| 字段名    | 类型         | 说明                        | 示例                           |
| --------- | ------------ | --------------------------- | ------------------------------ |
| 标题      | Title        | 记录名称                    | "2024-06-02 午餐"              |
| 记录时间  | Date         | 用餐时间                    | 2024-06-02 12:30               |
| 餐次      | Select       | 早餐/午餐/晚餐/加餐         | 午餐                           |
| 食物图片  | Files        | 用户上传的图片              | food_photo.jpg                 |
| 用户描述  | Rich Text    | 用户输入的文字描述          | "一份鸡肉沙拉配全麦面包"       |
| 食物类型  | Multi-select | 识别出的食物种类            | 鸡肉, 生菜, 全麦面包           |
| 分量信息  | Rich Text    | 详细的分量描述              | 鸡肉 100g, 生菜 50g, 面包 2 片 |
| 总卡路里  | Number       | 计算出的总卡路里            | 420                            |
| AI 置信度 | Number       | 识别置信度(0-100)           | 85                             |
| 处理状态  | Select       | 待处理/处理中/已完成/需确认 | 已完成                         |
| 用户确认  | Checkbox     | 用户是否确认 AI 结果        | ☑                              |

### 辅助数据库

-   **营养数据库**：标准化食物营养信息
-   **用户偏好设置**：个人设置和目标

## AI 模型技术方案

### 多模态处理架构

```python
class FoodCalorieAnalyzer:
    def __init__(self):
        self.text_processor = TextFoodProcessor()      # 文本分析模型
        self.image_processor = ImageFoodProcessor()    # 图像分析模型
        self.fusion_engine = FusionEngine()           # 融合判断引擎
        self.nutrition_calc = NutritionCalculator()   # 营养计算器

```

### 推荐的 AI 模型选择

### VLM 模型（优先推荐）

-   **API 服务**：GPT-4V / Claude 3.5 Sonnet（快速验证）
-   **本地部署**：LLaVA-7B / Qwen-VL-7B（成本优化）
-   **本地部署**：LLaVA-7B / Qwen-VL-7B（成本优化）

### 传统 CV 模型（备选）

-   **图像分类**：EfficientNet-B0（轻量级）
-   **目标检测**：YOLOv8n（检测+定位）

### 融合策略

1. **置信度权重融合**：高置信度结果优先
2. **智能冲突仲裁**：规则引擎 + LLM 判断
3. **渐进式确认**：不确定时询问用户

## 部署架构

### 推荐方案：混合部署

### OrbStack 容器化服务

```yaml
services:
    api-server: # Web API服务
    webhook-handler: # Notion webhook处理
    redis: # 缓存服务
```

### 本地原生服务

```python
# ML推理服务（可使用MPS加速）
python ml_service.py --device mps --port 8001

```

### 硬件要求分析

-   **16GB RAM M4 Mac**：完全满足需求
-   **OrbStack 限制**：无 GPU 直通，但 CPU 性能足够
-   **性能预期**：图像分析 0.5-1 秒，可接受

## 工作流程

### 用户操作流程

1. 在 Notion 中创建新食物记录
2. 上传图片和/或输入文字描述
3. 保存触发 webhook
4. 系统自动分析并回写结果
5. 用户确认或修正结果

### 系统处理流程

```python
def analyze_food(image=None, text=None):
    # 1. 多模态输入处理
    text_result = text_processor.extract_food_info(text) if text else None
    image_result = image_processor.extract_food_info(image) if image else None

    # 2. 智能融合决策
    final_result = fusion_engine.fuse_results(text_result, image_result)

    # 3. 营养数据库查询
    calories_result = nutrition_calc.calculate_calories(final_result)

    # 4. 结果回写Notion
    update_notion_page(page_id, calories_result)

```

## 实现优先级

### 第一阶段：MVP 验证

-   Notion 数据库设计和 webhook 配置
-   使用 API 服务（GPT-4V）快速验证效果
-   基础的卡路里计算功能

### 第二阶段：性能优化

-   部署本地 VLM 模型降低 API 成本
-   实现多模态融合逻辑
-   优化用户交互体验

### 第三阶段：功能扩展

-   营养分析和建议
-   历史数据分析
-   个性化推荐

## 技术栈总结

### 核心技术

-   **前端**：Notion API + Webhook
-   **后端**：FastAPI + Celery + Redis
-   **AI**：VLM 模型（优先）+ 传统 CV 模型（备选）
-   **部署**：OrbStack + 本地混合部署
-   **数据**：营养数据库 API（USDA Food Data Central）

### 开发工具

-   **容器化**：OrbStack（性能优于 Docker Desktop）
-   **API 集成**：notion-client, openai, anthropic
-   **ML 框架**：transformers, ultralytics, torch
-   **Web 框架**：FastAPI, uvicorn

## 预期效果

### 功能目标

-   准确识别常见食物种类（85%+准确率）
-   合理估算食物分量和卡路里
-   快速响应（<2 秒完成分析）
-   良好的用户交互体验

### 技术指标

-   **处理速度**：图像分析 0.5-1 秒，总响应<2 秒
-   **内存使用**：系统总占用<8GB
-   **准确率**：VLM 模式 85%+，传统 CV 模式 75%+
-   **可用性**：7×24 小时稳定运行
