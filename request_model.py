import requests
import time

image_path = "foods/20240903_163132850_iOS.jpg"
start_time = time.time()
with open(image_path, "rb") as f:
    files = {"file": f}
    try:
        response = requests.post("http://localhost:8000/analyze/", files=files)
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        exit(1)
end_time = time.time()
print(f"总耗时: {end_time - start_time:.2f} 秒")
print("分析结果：")
print(response.json())
