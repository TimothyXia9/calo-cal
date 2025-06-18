class FoodAnalyzer {
    constructor() {
        this.apiUrl = 'http://localhost:8001';  // 使用新的API服务端口
        this.selectedImages = [];
        this.analysisHistory = this.loadHistory();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.renderHistory();
        this.testConnection();
    }

    async testConnection() {
        try {
            console.log('正在测试后端连接...');
            const response = await fetch(`${this.apiUrl}/health`);
            if (response.ok) {
                const data = await response.json();
                console.log('✅ 后端连接正常:', data);
            } else {
                console.warn('⚠️ 后端响应异常:', response.status);
            }
        } catch (error) {
            console.error('❌ 无法连接到后端:', error.message);
            this.showError(`无法连接到后端服务 (${this.apiUrl})，请确保后端服务已启动`);
        }
    }

    async enrichWithNutrition(vlmResult) {
        try {
            // 解析VLM结果
            let foods;
            try {
                const parsed = JSON.parse(vlmResult);
                foods = parsed.foods || [];
            } catch (e) {
                foods = [];
            }

            if (foods.length === 0) {
                return { foods: [], totalNutrition: this.getEmptyNutrition() };
            }

            // 为每个食物获取USDA营养信息
            const enrichedFoods = await Promise.all(foods.map(async (food) => {
                const nutrition = await this.getUSDANutrition(food.en_name, food.estimated_weight_grams);
                return {
                    ...food,
                    nutrition: nutrition
                };
            }));

            // 计算总营养
            const totalNutrition = this.calculateTotalNutrition(enrichedFoods);

            return {
                foods: enrichedFoods,
                totalNutrition: totalNutrition
            };

        } catch (error) {
            console.error('营养信息获取失败:', error);
            // 返回估算的营养信息
            return this.getFallbackNutrition(vlmResult);
        }
    }

    async getUSDANutrition(foodName, weightGrams) {
        try {
            // 这里调用USDA API获取营养信息
            // 为了演示，我先用模拟数据，实际应该调用USDA服务
            console.log(`查询USDA营养信息: ${foodName} (${weightGrams}g)`);
            
            // 模拟USDA API调用
            const nutrition = this.getEstimatedNutrition(foodName, weightGrams);
            nutrition.source = 'estimated'; // 标记为估算数据
            
            return nutrition;
        } catch (error) {
            console.error(`获取${foodName}营养信息失败:`, error);
            return this.getEstimatedNutrition(foodName, weightGrams);
        }
    }

    getEstimatedNutrition(foodName, weightGrams) {
        // 改进的营养估算数据库（每100g）
        const nutritionDB = {
            // 水果类
            'apple': { calories: 52, protein: 0.3, fat: 0.2, carbs: 14, fiber: 2.4, sugar: 10 },
            'banana': { calories: 89, protein: 1.1, fat: 0.3, carbs: 23, fiber: 2.6, sugar: 12 },
            'orange': { calories: 47, protein: 0.9, fat: 0.1, carbs: 12, fiber: 2.4, sugar: 9 },
            
            // 蔬菜类
            'broccoli': { calories: 34, protein: 2.8, fat: 0.4, carbs: 7, fiber: 2.6, sugar: 1.5 },
            'carrot': { calories: 41, protein: 0.9, fat: 0.2, carbs: 10, fiber: 2.8, sugar: 4.7 },
            'tomato': { calories: 18, protein: 0.9, fat: 0.2, carbs: 3.9, fiber: 1.2, sugar: 2.6 },
            
            // 肉类
            'chicken': { calories: 165, protein: 31, fat: 3.6, carbs: 0, fiber: 0, sugar: 0 },
            'beef': { calories: 250, protein: 26, fat: 15, carbs: 0, fiber: 0, sugar: 0 },
            'pork': { calories: 242, protein: 27, fat: 14, carbs: 0, fiber: 0, sugar: 0 },
            'fish': { calories: 206, protein: 22, fat: 12, carbs: 0, fiber: 0, sugar: 0 },
            'salmon': { calories: 208, protein: 20, fat: 13, carbs: 0, fiber: 0, sugar: 0 },
            
            // 主食类
            'rice': { calories: 130, protein: 2.7, fat: 0.3, carbs: 28, fiber: 0.4, sugar: 0.1 },
            'bread': { calories: 265, protein: 9, fat: 3.2, carbs: 49, fiber: 2.7, sugar: 5 },
            'pasta': { calories: 131, protein: 5, fat: 1.1, carbs: 25, fiber: 1.8, sugar: 0.6 },
            'potato': { calories: 77, protein: 2, fat: 0.1, carbs: 17, fiber: 2.2, sugar: 0.8 },
            
            // 默认值
            'default': { calories: 150, protein: 5, fat: 5, carbs: 20, fiber: 2, sugar: 5 }
        };

        const foodNameLower = foodName.toLowerCase();
        let nutritionPer100g = nutritionDB.default;

        // 查找最匹配的营养信息
        for (const [key, value] of Object.entries(nutritionDB)) {
            if (key !== 'default' && (foodNameLower.includes(key) || key.includes(foodNameLower))) {
                nutritionPer100g = value;
                break;
            }
        }

        // 根据实际重量计算
        const multiplier = weightGrams / 100;
        return {
            calories: Math.round(nutritionPer100g.calories * multiplier * 10) / 10,
            protein: Math.round(nutritionPer100g.protein * multiplier * 10) / 10,
            fat: Math.round(nutritionPer100g.fat * multiplier * 10) / 10,
            carbs: Math.round(nutritionPer100g.carbs * multiplier * 10) / 10,
            fiber: Math.round(nutritionPer100g.fiber * multiplier * 10) / 10,
            sugar: Math.round(nutritionPer100g.sugar * multiplier * 10) / 10,
            weight: weightGrams,
            source: 'estimated'
        };
    }

    calculateTotalNutrition(enrichedFoods) {
        const total = {
            calories: 0,
            protein: 0,
            fat: 0,
            carbs: 0,
            fiber: 0,
            sugar: 0,
            weight: 0,
            foodCount: enrichedFoods.length
        };

        enrichedFoods.forEach(food => {
            const nutrition = food.nutrition;
            total.calories += nutrition.calories || 0;
            total.protein += nutrition.protein || 0;
            total.fat += nutrition.fat || 0;
            total.carbs += nutrition.carbs || 0;
            total.fiber += nutrition.fiber || 0;
            total.sugar += nutrition.sugar || 0;
            total.weight += nutrition.weight || 0;
        });

        // 四舍五入到一位小数
        Object.keys(total).forEach(key => {
            if (typeof total[key] === 'number' && key !== 'foodCount') {
                total[key] = Math.round(total[key] * 10) / 10;
            }
        });

        return total;
    }

    getEmptyNutrition() {
        return {
            calories: 0,
            protein: 0,
            fat: 0,
            carbs: 0,
            fiber: 0,
            sugar: 0,
            weight: 0,
            foodCount: 0
        };
    }

    getFallbackNutrition(vlmResult) {
        try {
            const parsed = JSON.parse(vlmResult);
            const foods = parsed.foods || [];
            
            const enrichedFoods = foods.map(food => ({
                ...food,
                nutrition: this.getEstimatedNutrition(food.en_name, food.estimated_weight_grams)
            }));

            return {
                foods: enrichedFoods,
                totalNutrition: this.calculateTotalNutrition(enrichedFoods)
            };
        } catch (e) {
            return { foods: [], totalNutrition: this.getEmptyNutrition() };
        }
    }

    setupEventListeners() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const clearBtn = document.getElementById('clearBtn');
        const saveBtn = document.getElementById('saveBtn');
        const newAnalysisBtn = document.getElementById('newAnalysisBtn');

        // 文件上传事件
        fileInput.addEventListener('change', (e) => this.handleFiles(e.target.files));
        
        // 拖拽上传
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            this.handleFiles(e.dataTransfer.files);
        });

        // 按钮事件
        analyzeBtn.addEventListener('click', () => this.analyzeImages());
        clearBtn.addEventListener('click', () => this.clearImages());
        saveBtn.addEventListener('click', () => this.saveResult());
        newAnalysisBtn.addEventListener('click', () => this.startNewAnalysis());
    }

    handleFiles(files) {
        const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
        this.selectedImages = [];

        Array.from(files).forEach(file => {
            if (validTypes.includes(file.type)) {
                this.selectedImages.push(file);
            } else {
                this.showError(`不支持的文件格式: ${file.name}`);
            }
        });

        if (this.selectedImages.length > 0) {
            this.showImagePreview();
        }
    }

    showImagePreview() {
        const previewSection = document.getElementById('previewSection');
        const imagePreview = document.getElementById('imagePreview');
        
        imagePreview.innerHTML = '';
        
        this.selectedImages.forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const imageCard = document.createElement('div');
                imageCard.className = 'image-card';
                imageCard.innerHTML = `
                    <img src="${e.target.result}" alt="预览图片 ${index + 1}">
                    <div class="image-info">
                        <p class="image-name">${file.name}</p>
                        <p class="image-size">${this.formatFileSize(file.size)}</p>
                    </div>
                    <button class="remove-btn" onclick="foodAnalyzer.removeImage(${index})">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                imagePreview.appendChild(imageCard);
            };
            reader.readAsDataURL(file);
        });
        
        previewSection.style.display = 'block';
        this.hideOtherSections(['previewSection']);
    }

    removeImage(index) {
        this.selectedImages.splice(index, 1);
        if (this.selectedImages.length === 0) {
            this.clearImages();
        } else {
            this.showImagePreview();
        }
    }

    clearImages() {
        this.selectedImages = [];
        document.getElementById('fileInput').value = '';
        document.getElementById('previewSection').style.display = 'none';
        this.hideOtherSections([]);
    }

    async analyzeImages() {
        if (this.selectedImages.length === 0) {
            this.showError('请先选择图片');
            return;
        }

        this.showAnalysisProgress();
        
        try {
            const results = [];
            
            for (let i = 0; i < this.selectedImages.length; i++) {
                const image = this.selectedImages[i];
                this.updateProgress((i / this.selectedImages.length) * 100, `正在分析第 ${i + 1} 张图片...`);
                
                const formData = new FormData();
                formData.append('file', image);
                
                console.log(`开始分析图片 ${i + 1}: ${image.name}`);
                
                const response = await fetch(`${this.apiUrl}/analyze`, {
                    method: 'POST',
                    body: formData
                });
                
                console.log(`API响应状态: ${response.status} ${response.statusText}`);
                
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error(`API错误响应: ${errorText}`);
                    throw new Error(`分析失败: ${response.status} ${response.statusText} - ${errorText}`);
                }
                
                const result = await response.json();
                console.log(`分析结果:`, result);
                
                // 新API服务已经包含了完整的营养信息
                this.updateProgress((i / this.selectedImages.length) * 100 + 10, `处理结果...`);
                
                results.push({
                    image: image,
                    result: result.raw_vlm_result || result.result || "",
                    enrichedResult: result.parsed_analysis || await this.enrichWithNutrition(result.result || ""),
                    timestamp: result.analysis_timestamp || new Date().toISOString()
                });
            }
            
            this.updateProgress(100, '分析完成！');
            setTimeout(() => {
                this.showResults(results);
            }, 1000);
            
        } catch (error) {
            console.error('Analysis error:', error);
            this.showError(`分析失败: ${error.message}`);
            this.hideOtherSections([]);
        }
    }

    showAnalysisProgress() {
        const analysisSection = document.getElementById('analysisSection');
        analysisSection.style.display = 'block';
        this.hideOtherSections(['analysisSection']);
        this.updateProgress(0, '准备分析图片...');
    }

    updateProgress(percent, text) {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        progressFill.style.width = `${percent}%`;
        progressText.textContent = text;
    }

    showResults(results) {
        const resultsSection = document.getElementById('resultsSection');
        const resultsContainer = document.getElementById('resultsContainer');
        
        resultsContainer.innerHTML = '';
        
        results.forEach((item, index) => {
            const resultCard = this.createResultCard(item, index);
            resultsContainer.appendChild(resultCard);
        });
        
        this.currentResults = results;
        resultsSection.style.display = 'block';
        this.hideOtherSections(['resultsSection']);
    }

    createResultCard(item, index) {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        // 使用增强的营养信息或回退到原始数据
        const enrichedResult = item.enrichedResult;
        const foods = enrichedResult?.foods || [];
        const totalNutrition = enrichedResult?.totalNutrition || this.getEmptyNutrition();
        
        // 创建食物列表HTML
        const foodsHtml = foods.map(food => {
            const nutrition = food.nutrition || {};
            const dataSource = nutrition.source === 'estimated' ? '估算' : 'USDA';
            
            return `
                <div class="food-item">
                    <div class="food-header">
                        <h4>${food.en_name}</h4>
                        <span class="confidence">置信度: ${(food.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div class="food-details">
                        <span class="weight"><i class="fas fa-weight"></i> ${food.estimated_weight_grams}g</span>
                        <span class="method"><i class="fas fa-utensils"></i> ${food.method}</span>
                        <span class="calories"><i class="fas fa-fire"></i> ${nutrition.calories || 0} 卡路里</span>
                    </div>
                    <div class="nutrition-details">
                        <div class="nutrition-row">
                            <span class="nutrition-item">
                                <i class="fas fa-drumstick-bite"></i> 蛋白质: ${nutrition.protein || 0}g
                            </span>
                            <span class="nutrition-item">
                                <i class="fas fa-oil-can"></i> 脂肪: ${nutrition.fat || 0}g
                            </span>
                            <span class="nutrition-item">
                                <i class="fas fa-bread-slice"></i> 碳水: ${nutrition.carbs || 0}g
                            </span>
                        </div>
                        <div class="nutrition-row">
                            <span class="nutrition-item">
                                <i class="fas fa-leaf"></i> 纤维: ${nutrition.fiber || 0}g
                            </span>
                            <span class="nutrition-item">
                                <i class="fas fa-candy-cane"></i> 糖: ${nutrition.sugar || 0}g
                            </span>
                            <span class="data-source">
                                <i class="fas fa-database"></i> ${dataSource}数据
                            </span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        // 创建图片预览URL
        const imageUrl = URL.createObjectURL(item.image);
        
        card.innerHTML = `
            <div class="result-header">
                <h4>图片 ${index + 1} 分析结果</h4>
                <div class="total-calories">
                    <i class="fas fa-fire-alt"></i>
                    总计: <strong>${totalNutrition.calories}</strong> 卡路里
                </div>
            </div>
            <div class="result-content">
                <div class="result-image">
                    <img src="${imageUrl}" alt="分析图片">
                </div>
                <div class="result-details">
                    <div class="foods-list">
                        ${foodsHtml}
                    </div>
                    <div class="nutrition-summary">
                        <h5><i class="fas fa-chart-pie"></i> 营养总计</h5>
                        <div class="summary-grid">
                            <div class="summary-item">
                                <span class="summary-value">${totalNutrition.calories}</span>
                                <span class="summary-label">卡路里</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-value">${totalNutrition.protein}g</span>
                                <span class="summary-label">蛋白质</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-value">${totalNutrition.fat}g</span>
                                <span class="summary-label">脂肪</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-value">${totalNutrition.carbs}g</span>
                                <span class="summary-label">碳水</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-value">${totalNutrition.weight}g</span>
                                <span class="summary-label">总重量</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-value">${totalNutrition.foodCount}</span>
                                <span class="summary-label">食物种类</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        return card;
    }


    saveResult() {
        if (this.currentResults) {
            this.analysisHistory.push({
                id: Date.now(),
                timestamp: new Date().toISOString(),
                results: this.currentResults
            });
            this.saveHistory();
            this.renderHistory();
            this.showSuccess('结果已保存到历史记录');
        }
    }

    startNewAnalysis() {
        this.clearImages();
        this.currentResults = null;
        document.getElementById('analysisSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
    }

    renderHistory() {
        const historyContainer = document.getElementById('historyContainer');
        
        if (this.analysisHistory.length === 0) {
            historyContainer.innerHTML = '<p class="no-history">暂无历史记录</p>';
            return;
        }
        
        historyContainer.innerHTML = this.analysisHistory
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, 10) // 只显示最近10条
            .map(record => this.createHistoryItem(record))
            .join('');
    }

    createHistoryItem(record) {
        const date = new Date(record.timestamp).toLocaleString('zh-CN');
        const totalCalories = record.results.reduce((sum, item) => {
            // 使用增强的营养信息或回退到估算
            if (item.enrichedResult && item.enrichedResult.totalNutrition) {
                return sum + (item.enrichedResult.totalNutrition.calories || 0);
            } else {
                // 回退到原始计算方法
                try {
                    const parsed = JSON.parse(item.result);
                    return sum + (parsed.foods || []).reduce((foodSum, food) => {
                        const nutrition = this.getEstimatedNutrition(food.en_name, food.estimated_weight_grams);
                        return foodSum + nutrition.calories;
                    }, 0);
                } catch (e) {
                    return sum;
                }
            }
        }, 0);
        
        const totalFoods = record.results.reduce((sum, item) => {
            if (item.enrichedResult && item.enrichedResult.foods) {
                return sum + item.enrichedResult.foods.length;
            } else {
                try {
                    const parsed = JSON.parse(item.result);
                    return sum + (parsed.foods || []).length;
                } catch (e) {
                    return sum;
                }
            }
        }, 0);
        
        return `
            <div class="history-item">
                <div class="history-header">
                    <span class="history-date">${date}</span>
                    <span class="history-calories">${Math.round(totalCalories)} 卡路里</span>
                </div>
                <div class="history-summary">
                    ${record.results.length} 张图片，${totalFoods} 种食物
                </div>
                <button class="btn btn-sm btn-danger" onclick="foodAnalyzer.deleteHistory('${record.id}')">
                    <i class="fas fa-trash"></i> 删除
                </button>
            </div>
        `;
    }

    deleteHistory(id) {
        this.analysisHistory = this.analysisHistory.filter(item => item.id != id);
        this.saveHistory();
        this.renderHistory();
    }

    hideOtherSections(keepVisible = []) {
        const sections = ['previewSection', 'analysisSection', 'resultsSection'];
        sections.forEach(sectionId => {
            if (!keepVisible.includes(sectionId)) {
                document.getElementById(sectionId).style.display = 'none';
            }
        });
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorModal').style.display = 'block';
    }

    showSuccess(message) {
        // 简单的成功提示
        const toast = document.createElement('div');
        toast.className = 'toast toast-success';
        toast.innerHTML = `<i class="fas fa-check"></i> ${message}`;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    loadHistory() {
        const history = localStorage.getItem('foodAnalysisHistory');
        return history ? JSON.parse(history) : [];
    }

    saveHistory() {
        localStorage.setItem('foodAnalysisHistory', JSON.stringify(this.analysisHistory));
    }
}

// 全局函数
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// 初始化应用
const foodAnalyzer = new FoodAnalyzer();