import json
import csv
import uuid
import sys
import os
import re
from urllib.parse import urlparse
from typing import Callable, List, Dict, Any

def _is_valid_json(json_data: str, logger: Callable) -> bool:
    """
    检查字符串是否为有效的JSON。
    """
    try:
        json.loads(json_data)
        return True
    except ValueError as e:
        logger(f"无效的JSON格式: {e}", "error")
        return False

def _process_text(input_text: str) -> str:
    """
    清理和处理文本字段。
    """
    cleaned_text = input_text.strip()
    cleaned_text = re.sub(r"\n\s*\n", "\n", cleaned_text)
    if not cleaned_text.startswith("http") and not cleaned_text.startswith("//"):
        cleaned_text = re.sub(r"(\d) ?(x) ?(\d)", r"\1 × \3", cleaned_text)
    cleaned_text = re.sub(r" +", " ", cleaned_text)
    cleaned_text = cleaned_text.replace('"', '\"')
    if not cleaned_text.startswith("/") and not cleaned_text.startswith("http"):
        cleaned_text = cleaned_text.replace('’', "'")
    return cleaned_text

def _get_template_content(templates_path: str, template_name: str, logger: Callable) -> str:
    """
    从模板文件读取内容。
    """
    template_file_path = os.path.join(templates_path, f"{template_name}.json")
    if not os.path.exists(template_file_path):
        logger(f"未找到模板文件: {template_file_path}", "error")
        raise FileNotFoundError(f"未找到模板文件: {template_file_path}")
    
    with open(template_file_path, "r", encoding="utf-8") as f:
        return f.read()

def generate_tools_json(csv_path: str, templates_path: str, logger: Callable = print) -> str | None:
    """
    从CSV输入和多个JSON模板生成一个组合的JSON字符串。

    Args:
        csv_path (str): 输入CSV文件的路径。
        templates_path (str): 包含JSON模板的目录路径。
        logger (Callable): 用于发送反馈的日志记录函数。

    Returns:
        str | None: 生成的JSON字符串，如果发生错误则返回None。
    """
    try:
        with open(csv_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            data = [row for row in reader]
        logger(f"成功从 {os.path.basename(csv_path)} 加载 {len(data)} 行。", "info")
    except FileNotFoundError:
        logger(f"未找到CSV文件: {csv_path}", "error")
        return None
    except Exception as e:
        logger(f"读取CSV文件时出错: {e}", "error")
        return None

    tool_2_count = 0
    tool_3_count = 0

    try:
        tools_2_part = _get_template_content(templates_path, 'tools_2_part', logger)
        tools_3_part = _get_template_content(templates_path, 'tools_3_part', logger)
        tools_3_template = _get_template_content(templates_path, 'tools_3', logger)
        tools_2_template = _get_template_content(templates_path, 'tools_2', logger)
        tools_main_template = _get_template_content(templates_path, 'tools', logger)
    except FileNotFoundError:
        return None

    tools_2_json = json.loads(tools_2_template)
    tools_3_json = json.loads(tools_3_template)
    
    # 按标题不区分大小写排序
    data_sorted = sorted(data, key=lambda row: str(row.get('title', '')).lower())

    for row in data_sorted:
        # 检查'type', 'title', 'link'是否存在且不为空
        if row.get('type') and row.get('title') and row.get('link'):
            page_type = str(row['type']).strip()
            title = _process_text(str(row['title']).strip())
            
            if not title.startswith("iPhone"):
                title = title[0].upper() + title[1:]
            
            link = str(row['link']).strip().lower()
            if link.startswith(("https://", "http://")):
                link = urlparse(link).path
            
            excluded_titles = {
                "Dieline generator", "Mockup generator", "UPC-A Barcode generator",
                "QR code generator", "EAN-13 Barcode generator", "EAN-8 Barcode generator",
                "Code 128 Barcode generator", "Code 39 Barcode generator",
                "3D modeling software", "AI background generator"
            }
            if title in excluded_titles:
                continue

            category = '2.0' if page_type in ("样机工具页", "刀版工具页") else '3.0'
            
            tools_ga = ''
            uuid_1 = str(uuid.uuid4())
            uuid_2 = str(uuid.uuid4())
            uuid_3 = str(uuid.uuid4())

            replacements = {
                "tools_title": title,
                "tools_href": link,
                "tools_ga": tools_ga,
                "uuid_1": uuid_1,
                "uuid_2": uuid_2,
                "uuid_3": uuid_3
            }

            if category == '2.0':
                part_str = tools_2_part
                for key, value in replacements.items():
                    part_str = part_str.replace(key, value)
                tools_2_json['children'].append(json.loads(part_str))
                tool_2_count += 1
            elif category == '3.0':
                part_str = tools_3_part
                for key, value in replacements.items():
                    part_str = part_str.replace(key, value)
                tools_3_json['children'].append(json.loads(part_str))
                tool_3_count += 1
        else:
            continue

    tools_2_json_result = json.dumps(tools_2_json, ensure_ascii=False, indent=2)
    tools_3_json_result = json.dumps(tools_3_json, ensure_ascii=False, indent=2)
    
    final_json_str = tools_main_template.replace("<tools_2_placeholder>", tools_2_json_result).replace("<tools_3_placeholder>", tools_3_json_result)
    
    if _is_valid_json(final_json_str, logger):
        logger(f"成功生成JSON。在2.0类别中找到 {tool_2_count} 个工具，在3.0类别中找到 {tool_3_count} 个工具。", "success")
        return final_json_str
    else:
        logger("生成有效的JSON失败。", "error")
        return None