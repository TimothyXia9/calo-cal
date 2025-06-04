import torch
from transformers import AutoModel, AutoTokenizer
from PIL import Image
import os
from unittest.mock import patch
from transformers.dynamic_module_utils import get_imports
import importlib.util
import sys
from typing import List, Dict, Any, Optional, Union, Tuple


def fixed_get_imports(filename: str | os.PathLike) -> list[str]:
    """
    解决 Mac 上 MiniCPM-V-2.6 的多个导入问题
    1. 移除 flash_attn 依赖
    2. 确保 typing 相关导入可用
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
        解决 Mac 上的多个导入问题
        """
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"Using device: {self.device}")

        # 设置环境变量优化内存
        os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

        print("Loading model with Mac-optimized settings...")

        # 修复 typing 导入问题
        patch_resampler_module()

        # 使用 patch 解决多个导入问题
        with patch("transformers.dynamic_module_utils.get_imports", fixed_get_imports):
            try:
                # Mac优化的加载配置
                model_kwargs = {
                    "trust_remote_code": True,
                    "torch_dtype": torch.float16,
                    "low_cpu_mem_usage": True,
                }

                # 设备映射
                if use_cpu_offload:
                    model_kwargs["device_map"] = "auto"
                else:
                    model_kwargs["device_map"] = self.device

                self.model = AutoModel.from_pretrained(model_name, **model_kwargs)
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_name, trust_remote_code=True
                )

                print("Model loaded successfully!")

            except Exception as e:
                print(f"Error loading model: {e}")
                raise

    def recognize_food(self, image_path, question="请识别这张图片中的食物"):
        """
        识别图片中的食物
        """
        try:
            image = Image.open(image_path).convert("RGB")
            msgs = [{"role": "user", "content": [image, question]}]

            response = self.model.chat(
                image=None,
                msgs=msgs,
                tokenizer=self.tokenizer,
                sampling=True,
                temperature=0.7,
            )

            return response
        except Exception as e:
            print(f"Recognition error: {e}")
            return None


if __name__ == "__main__":
    vlm = FoodRecognitionVLM()
