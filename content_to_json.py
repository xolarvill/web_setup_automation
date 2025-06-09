import json
import os
from pathlib import Path
import re
from jinja2 import Template
import requests

# 模拟LLM API调用（替换为实际的xAI Grok API或其他LLM API）
def call_llm_api(text, prompt):
    """
    调用LLM API优化文案或解析指示。
    这里使用xAI Grok API的占位符，实际需替换为真实API调用。
    """
    # 模拟API调用，实际替换为requests.post调用Grok API
    # 参考：https://x.ai/api
    try:
        # 假设的Grok API端点
        api_url = "https://api.x.ai/grok"  # 替换为真实API端点
        headers = {"Authorization": "Bearer YOUR_API_KEY"}  # 替换为你的API密钥
        data = {
            "prompt": f"{prompt}\n\nInput: {text}",
            "max_tokens": 500
        }
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()
        return response.json().get("choices", [{}])[0].get("text", text)
    except Exception as e:
        print(f"LLM API调用失败: {e}")
        return text  # 失败时返回原始文本

def process_content(content, use_llm=False):
    """处理文案，优化或提取关键信息"""
    if use_llm:
        prompt = "优化以下文案，使其更简洁、吸引人，适合网页展示："
        return call_llm_api(content, prompt)
    return content

def process_images(image_dir):
    """扫描图片目录，获取图片路径和元数据"""
    image_dir = Path(image_dir)
    images = []
    for img_path in image_dir.glob("*.{jpg,png,jpeg}"):
        # 提取图片文件名和扩展名
        img_info = {
            "url": str(img_path),
            "alt": img_path.stem.replace("_", " ").title(),
            "size": img_path.stat().st_size  # 可根据需要添加尺寸处理
        }
        images.append(img_info)
    return images

def apply_variations(content, variations=None):
    """处理细小变化，例如替换关键词或调整格式"""
    if not variations:
        return content
    for pattern, replacement in variations.items():
        content = re.sub(pattern, replacement, content)
    return content

def generate_json_content(content, images, template_path, custom_fields=None):
    """根据模板生成JSON内容"""
    # 加载Jinja2模板
    with open(template_path, 'r', encoding='utf-8') as f:
        template = Template(f.read())
    
    # 准备数据
    data = {
        "title": apply_variations(content.get("title", ""), content.get("variations")),
        "body": apply_variations(content.get("body", ""), content.get("variations")),
        "images": images,
        "custom": custom_fields or {}
    }
    
    # 渲染模板
    rendered = template.render(**data)
    return json.loads(rendered)

def main(input_content, image_dir, instructions, template_path, output_path, use_llm=False):
    """主函数：处理文案、图片和指示，生成JSON"""
    # 处理文案
    content = {
        "title": input_content.get("title", ""),
        "body": input_content.get("body", ""),
        "variations": instructions.get("variations", {})  # 细小变化规则
    }
    content["title"] = process_content(content["title"], use_llm)
    content["body"] = process_content(content["body"], use_llm)
    
    # 处理图片
    images = process_images(image_dir)
    
    # 处理自定义字段
    custom_fields = instructions.get("custom_fields", {})
    
    # 生成JSON
    json_data = generate_json_content(content, images, template_path, custom_fields)
    
    # 保存输出
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"JSON文件已生成：{output_path}")

if __name__ == "__main__":
    # 示例输入
    input_content = {
        "title": "欢迎体验我们的新产品！",
        "body": "这是一个创新的产品，适合所有人使用，功能强大。"
    }
    image_dir = "./images"
    instructions = {
        "variations": {
            r"产品": "服务",  # 示例：替换“产品”为“服务”
            r"强大": "卓越"
        },
        "custom_fields": {
            "layout": "full-width",
            "theme": "light"
        }
    }
    template_path = "template.json.j2"
    output_path = "output.json"
    
    # 运行主函数
    main(input_content, image_dir, instructions, template_path, output_path, use_llm=True)