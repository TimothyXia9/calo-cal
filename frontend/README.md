# 食物卡路里分析器 - 前端界面

一个现代化的 Web 界面，用于与食物卡路里分析后端 API 交互。

## 功能特性

-   🖼️ **图片上传**: 支持拖拽上传和点击选择，支持多图片同时上传
-   👁️ **实时预览**: 上传后立即预览图片，可单独删除
-   🧠 **智能分析**: 调用后端 VLM API 进行食物识别和卡路里计算
-   📊 **结果展示**: 美观的卡片式结果展示，包含食物名称、重量、置信度等
-   📱 **响应式设计**: 适配桌面端和移动端
-   💾 **历史记录**: 本地存储分析历史，方便回顾
-   ⚡ **现代 UI**: 渐变背景、毛玻璃效果、平滑动画

## 快速开始

### 1. 启动后端服务

首先确保 VLM 后端服务已启动：

```bash
cd ./VLM
conda activate torch
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 启动前端服务

```bash
cd frontend
python server.py
```

服务会自动在浏览器中打开 `http://localhost:3000`

### 3. 或者使用任何 HTTP 服务器

```bash
# 使用Python内置服务器
python -m http.server 3000

# 使用Node.js的http-server
npx http-server -p 3000

# 使用PHP内置服务器
php -S localhost:3000
```

## 文件结构

```
frontend/
├── index.html      # 主页面
├── style.css       # 样式文件
├── script.js       # 前端逻辑
├── server.py       # 简单HTTP服务器
└── README.md       # 本文件
```

## 使用说明

1. **上传图片**:

    - 拖拽图片到上传区域
    - 或点击"选择图片"按钮

2. **预览确认**:

    - 查看上传的图片
    - 可删除不需要的图片
    - 点击"开始分析"

3. **查看结果**:

    - 等待 AI 分析完成
    - 查看识别的食物和卡路里
    - 可保存到历史记录

4. **历史记录**:
    - 查看之前的分析结果
    - 删除不需要的记录

## 技术栈

-   **HTML5**: 语义化标签和现代 Web API
-   **CSS3**: Flexbox/Grid 布局、CSS 动画、响应式设计
-   **JavaScript ES6+**: 原生 JS，无框架依赖
-   **Fetch API**: 与后端通信
-   **LocalStorage**: 本地数据存储

## 浏览器兼容性

-   Chrome 60+
-   Firefox 55+
-   Safari 12+
-   Edge 79+

## 自定义配置

可以在 `script.js` 中修改以下配置：

```javascript
// API地址
this.apiUrl = "http://localhost:8000";

// 支持的文件类型
const validTypes = ["image/jpeg", "image/png", "image/webp", "image/jpg"];

// 卡路里估算数据
const caloriesPer100g = {
	rice: 130,
	chicken: 165,
	// ...
};
```

## 故障排除

1. **无法连接后端**: 确保后端服务在 8000 端口运行
2. **图片上传失败**: 检查文件格式是否支持
3. **样式显示异常**: 清除浏览器缓存
4. **跨域问题**: 使用提供的 server.py 启动服务

## 开发模式

如需修改前端代码：

1. 修改 HTML/CSS/JS 文件
2. 刷新浏览器页面即可看到更改
3. 使用浏览器开发者工具进行调试
