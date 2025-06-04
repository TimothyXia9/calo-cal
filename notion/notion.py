import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")


headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def get_page_info(page_id):
    """获取页面信息"""
    url = f"https://api.notion.com/v1/pages/{page_id}"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(
            f"Error fetching page info: {response.status_code} - {response.text}"
        )


webhook = {
    "id": "f275db5c-db57-45bb-a048-69ae2328b9cb",
    "timestamp": "2025-06-03T16:13:11.594Z",
    "workspace_id": "5c876111-ba2d-4973-97bb-05ebd7ffec75",
    "workspace_name": "Tianqi's Notion",
    "subscription_id": "206d872b-594c-81da-8ac2-0099ece70f59",
    "integration_id": "1dcd872b-594c-80a1-9f9b-0037a24d9a08",
    "authors": [{"id": "89178246-074d-49b0-8d8b-de698eab5b3e", "type": "person"}],
    "attempt_number": 1,
    "entity": {"id": "207505a6-7b0e-8014-a9f6-c33eec6544a2", "type": "page"},
    "type": "page.properties_updated",
    "data": {
        "parent": {"id": "207505a6-7b0e-802a-a520-f2e05ac6fe03", "type": "database"},
        "updated_properties": ["_vUL"],
    },
}


def get_page_content(page_id):
    """获取页面内容（块内容）"""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def handle_webhook(webhook_data):
    # 提取页面ID
    page_id = webhook_data["entity"]["id"]
    updated_properties = webhook_data["data"]["updated_properties"]

    print(f"页面 {page_id} 的属性已更新: {updated_properties}")

    # 获取页面信息
    page_info = get_page_info(page_id)
    if page_info:
        print("页面信息:")
        print(json.dumps(page_info, indent=2, ensure_ascii=False))

    # 获取页面内容
    page_content = get_page_content(page_id)
    if page_content:
        print("页面内容:")
        print(json.dumps(page_content, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # 模拟接收Webhook数据
    handle_webhook(webhook)
