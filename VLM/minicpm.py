import torch
from PIL import Image
from transformers.dynamic_module_utils import get_imports
from transformers import AutoModel, AutoTokenizer
import json
import gc
from unittest.mock import patch
import os
from prompt import create_prompt
from typing import List, Dict, Any, Optional, Union, Tuple
from time import time


def fixed_get_imports(filename: str | os.PathLike) -> list[str]:
    """
    解决 Mac 上 MiniCPM-V-2.6 的多个导入问题
    移除 flash_attn 依赖
    """
    imports = get_imports(filename)

    if not torch.cuda.is_available() and "flash_attn" in imports:
        imports.remove("flash_attn")

    return imports


def patch_resampler_module():
    """
    修复 resampler.py 中缺失的 List 导入
    """
    import builtins

    if not hasattr(builtins, "List"):
        from typing import List, Dict, Any, Optional, Union, Tuple

        builtins.List = List
        builtins.Dict = Dict
        builtins.Any = Any
        builtins.Optional = Optional
        builtins.Union = Union
        builtins.Tuple = Tuple


class FoodRecognitionVLM:
    def __init__(self, model_name="openbmb/MiniCPM-V-2_6", use_cpu_offload=True):
        """
        初始化MiniCPM-V-2.6模型用于食物识别
        针对Mac优化，不使用bitsandbytes
        """
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            # 使用MPS设备（Mac专用）
            self.device = "mps"
        else:
            self.device = "cpu"

        print(f"Using device: {self.device}")
        patch_resampler_module()
        # 设置环境变量优化内存
        if self.device == "mps":
            os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"
        with patch("transformers.dynamic_module_utils.get_imports", fixed_get_imports):
            try:
                print("Loading model with Mac-optimized settings...")

                # Mac优化的加载配置
                model_kwargs = {
                    "trust_remote_code": True,
                    "torch_dtype": torch.float16,
                    "low_cpu_mem_usage": True,
                    "use_fast": False,
                }

                # 如果启用CPU卸载，使用device_map
                if use_cpu_offload:
                    model_kwargs["device_map"] = "auto"

                self.model = AutoModel.from_pretrained(model_name, **model_kwargs)

                if not use_cpu_offload:
                    self.model = self.model.to(self.device)

                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_name, trust_remote_code=True
                )

                # 设置为评估模式并优化
                self.model.eval()

                # 尝试编译模型以提高效率（可选）
                if hasattr(torch, "compile") and self.device == "mps":
                    try:
                        self.model = torch.compile(self.model, mode="reduce-overhead")
                        print("Model compiled for better performance")
                    except:
                        print("Model compilation not available or failed")

                print("Model loaded successfully!")

            except Exception as e:
                print(f"Failed to load model with optimizations: {e}")
                print("Trying fallback loading method...")

                # 更保守的备用方案
                try:
                    self.model = AutoModel.from_pretrained(
                        model_name,
                        trust_remote_code=True,
                        torch_dtype=torch.float32,  # 使用float32作为备用
                        low_cpu_mem_usage=True,
                    )

                    self.model = self.model.to(self.device)
                    self.model.eval()

                    self.tokenizer = AutoTokenizer.from_pretrained(
                        model_name, trust_remote_code=True
                    )

                    print("Model loaded with fallback method!")

                except Exception as e2:
                    print(f"All loading methods failed: {e2}")
                    raise e2

    def recognize_food(self, image_path, custom_format=None):
        """
        识别图片中的食物并估算份量

        Args:
            image_path (str): 图片路径
            custom_format (dict): 自定义输出格式

        Returns:
            dict: 结构化的食物识别结果
        """
        gc.collect()
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()

        # 加载图片时限制尺寸

        image = Image.open(image_path).convert("RGB")
        max_size = (448, 448)
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # 修改提示词，确保是中文
        if custom_format is None:
            format_instruction = create_prompt()
        else:
            format_instruction = f"请识别图片中的食物并按照以下格式输出：\n{json.dumps(custom_format, ensure_ascii=False, indent=2)}"

        # 修改消息格式 - 这是关键修改
        msgs = [
            {"role": "user", "content": format_instruction}  # 只传递文本，图像单独传递
        ]

        try:
            with torch.no_grad():
                # 修改调用方式
                response = self.model.chat(
                    image=image,  # 图像单独传递
                    msgs=msgs,  # 文本消息
                    tokenizer=self.tokenizer,
                    sampling=False,
                    temperature=0.1,
                    max_new_tokens=1024,
                )

            print(f"Raw response: {response}")  # 调试输出

            # 尝试解析JSON
            try:
                # 提取JSON部分
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                if json_start != -1 and json_end != 0:
                    json_str = response[json_start:json_end]
                    result = json.loads(json_str)
                    return result
                else:
                    return {"raw_response": response, "error": "No valid JSON found"}
            except json.JSONDecodeError:
                return {"raw_response": response, "error": "JSON parsing failed"}

        except Exception as e:
            return {"error": f"Model inference failed: {str(e)}"}

    def batch_recognize(self, image_paths, max_batch_size=1):
        """
        批量处理图片（建议batch_size=1以节省内存）

        Args:
            image_paths (list): 图片路径列表
            max_batch_size (int): 批处理大小

        Returns:
            list: 识别结果列表
        """
        results = []

        for i in range(0, len(image_paths), max_batch_size):
            batch_paths = image_paths[i : i + max_batch_size]

            for path in batch_paths:
                print(f"Processing: {path}")
                result = self.recognize_food(path)
                results.append({"image_path": path, "result": result})

                # 清理GPU缓存
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                elif torch.backends.mps.is_available():
                    torch.mps.empty_cache()

        return results

    def get_memory_usage(self):
        """获取当前内存使用情况"""
        if torch.backends.mps.is_available():
            # MPS内存使用情况
            allocated = torch.mps.current_allocated_memory() / 1024**3  # GB
            return f"MPS Memory allocated: {allocated:.2f} GB"

        else:
            return "CPU mode - memory tracking not available"


# 使用示例
def main():
    # 初始化模型
    vlm = FoodRecognitionVLM(use_cpu_offload=False)

    print(vlm.get_memory_usage())

    image_path = r"D:\CODE\cal-calc2\foods\20240905_000550644_iOS.jpg"

    time_start = time()
    print(f"Starting food recognition for {image_path}...")
    result = vlm.recognize_food(image_path)
    time_end = time()
    print(f"Recognition completed in {time_end - time_start:.2f} seconds")

    print("Recognition Result:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
