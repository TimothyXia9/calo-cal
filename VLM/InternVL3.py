import torch
import torchvision.transforms as T
from PIL import Image
from torchvision.transforms.functional import InterpolationMode
from transformers import AutoModel, AutoTokenizer, AutoConfig
import os
import time


class InternVL3_model:
    def __init__(self, model_path="OpenGVLab/InternVL3-2B"):
        self.model_path = model_path
        if torch.backends.mps.is_available():
            self.device = "mps"
            os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        print(f"Using device: {self.device}")

        self.device_map = "auto"

        self.model, self.tokenizer = None, None
        self.load_model()

    def mps_optimize(self, model):
        if self.device == "mps":
            try:
                if hasattr(torch, "compile"):
                    model = torch.compile(model, backend="aot_eager")
                    print("模型编译成功")
            except Exception as e:
                print(f"模型编译失败: {e}")

        return model

    def load_model(self):
        try:
            model = AutoModel.from_pretrained(
                self.model_path,
                torch_dtype=torch.bfloat16,
                load_in_8bit=True,  # 8bit量化以节省显存
                low_cpu_mem_usage=True,
                use_flash_attn=False,
                trust_remote_code=True,
                device_map=self.device_map,
            ).eval()

            tokenizer = AutoTokenizer.from_pretrained(
                self.model_path, trust_remote_code=True, use_fast=False
            )
            print("模型加载成功！")

        except Exception as e:
            print(f"模型加载失败: {e}")
            print("尝试不使用量化...")
            try:
                model = (
                    AutoModel.from_pretrained(
                        self.model_path,
                        torch_dtype=torch.bfloat16,
                        low_cpu_mem_usage=True,
                        use_flash_attn=False,
                        trust_remote_code=True,
                    )
                    .eval()
                    .to(self.device)
                )

                tokenizer = AutoTokenizer.from_pretrained(
                    self.model_path, trust_remote_code=True, use_fast=False
                )
                print("模型加载成功（无量化）！")
            except Exception as e2:
                print(f"模型加载完全失败: {e2}")
                return
            self.model = self.mps_optimize(model).to(self.device)
            self.tokenizer = tokenizer


IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def build_transform(input_size):
    MEAN, STD = IMAGENET_MEAN, IMAGENET_STD
    transform = T.Compose(
        [
            T.Lambda(lambda img: img.convert("RGB") if img.mode != "RGB" else img),
            T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
            T.ToTensor(),
            T.Normalize(mean=MEAN, std=STD),
        ]
    )
    return transform


def find_closest_aspect_ratio(aspect_ratio, target_ratios, width, height, image_size):
    best_ratio_diff = float("inf")
    best_ratio = (1, 1)
    area = width * height
    for ratio in target_ratios:
        target_aspect_ratio = ratio[0] / ratio[1]
        ratio_diff = abs(aspect_ratio - target_aspect_ratio)
        if ratio_diff < best_ratio_diff:
            best_ratio_diff = ratio_diff
            best_ratio = ratio
        elif ratio_diff == best_ratio_diff:
            if area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
                best_ratio = ratio
    return best_ratio


def dynamic_preprocess(
    image, min_num=1, max_num=12, image_size=448, use_thumbnail=False
):
    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    # calculate the existing image aspect ratio
    target_ratios = set(
        (i, j)
        for n in range(min_num, max_num + 1)
        for i in range(1, n + 1)
        for j in range(1, n + 1)
        if i * j <= max_num and i * j >= min_num
    )
    target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

    # find the closest aspect ratio to the target
    target_aspect_ratio = find_closest_aspect_ratio(
        aspect_ratio, target_ratios, orig_width, orig_height, image_size
    )

    # calculate the target width and height
    target_width = image_size * target_aspect_ratio[0]
    target_height = image_size * target_aspect_ratio[1]
    blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

    # resize the image
    resized_img = image.resize((target_width, target_height))
    processed_images = []
    for i in range(blocks):
        box = (
            (i % (target_width // image_size)) * image_size,
            (i // (target_width // image_size)) * image_size,
            ((i % (target_width // image_size)) + 1) * image_size,
            ((i // (target_width // image_size)) + 1) * image_size,
        )
        # split the image
        split_img = resized_img.crop(box)
        processed_images.append(split_img)
    assert len(processed_images) == blocks
    if use_thumbnail and len(processed_images) != 1:
        thumbnail_img = image.resize((image_size, image_size))
        processed_images.append(thumbnail_img)
    return processed_images


def load_image(image_file, input_size=448, max_num=4):
    """
    加载和预处理图像
    max_num: 最大块数，用于控制内存使用
    """
    image = Image.open(image_file).convert("RGB")
    transform = build_transform(input_size=input_size)
    images = dynamic_preprocess(
        image, image_size=input_size, use_thumbnail=True, max_num=max_num
    )
    pixel_values = [transform(image) for image in images]
    pixel_values = torch.stack(pixel_values)
    return pixel_values


def get_food_prompt():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_file = os.path.join(script_dir, "prompts", "food_prompt.txt")
    if os.path.exists(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read().strip()
            return prompt.replace("\n", " ").strip()


def analyze_food_image(image_path, model, tokenizer, max_tiles=4, device="cpu"):
    """
    分析食物图片的主函数
    """
    # 检查文件是否存在
    if not os.path.exists(image_path):
        return f"错误：图片文件不存在 - {image_path}"

    try:
        # 加载图像，限制最大块数以节省内存
        print(f"正在加载图像: {image_path}")
        pixel_values = (
            load_image(image_path, max_num=max_tiles).to(torch.bfloat16).to(device)
        )
        print(f"图像已处理为 {pixel_values.shape[0]} 个块")

        # 生成配置
        generation_config = dict(
            max_new_tokens=512,
            do_sample=True,
            temperature=0.1,
        )

        # 构建问题
        question = "<image>\n" + get_food_prompt()

        # 进行推理
        print("正在分析图像...")
        response = model.chat(tokenizer, pixel_values, question, generation_config)

        return response

    except Exception as e:
        return f"分析过程中出现错误: {str(e)}"


def main():
    start_time = time.time()
    # 分析图像
    image_path = r"foods/20240903_163132850_IOS.jpg"
    intern_model = InternVL3_model(model_path="OpenGVLab/InternVL3-2B")
    model, tokenizer = intern_model.model, intern_model.tokenizer

    # 根据你的显存情况调整max_tiles
    # 4GB显存: max_tiles=1
    # 8GB显存: max_tiles=4
    # 16GB显存: max_tiles=9
    max_tiles = 4  # 你可以根据显存情况调整

    print(f"\n开始分析图像，最大块数限制: {max_tiles}")
    result = analyze_food_image(
        image_path, model, tokenizer, max_tiles=max_tiles, device=model.device
    )
    end_time = time.time()
    print(f"分析完成，耗时: {end_time - start_time:.2f} 秒")
    print("\n" + "=" * 50)
    print("食物分析结果:")
    print("=" * 50)
    print(result)


if __name__ == "__main__":

    main()
