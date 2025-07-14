import json
import pandas as pd
import uuid
import os
import re
from urllib.parse import urlparse
from typing import Callable

def _is_valid_json(json_data: str, logger: Callable) -> bool:
    """
    Checks if a string is valid JSON.
    """
    try:
        json.loads(json_data)
        return True
    except ValueError as e:
        logger(f"Invalid JSON format: {e}", "error")
        return False

def _process_text(input_text: str) -> str:
    """
    Cleans and processes text fields.
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
    Reads content from a template file.
    """
    template_file_path = os.path.join(templates_path, f"{template_name}.json")
    if not os.path.exists(template_file_path):
        logger(f"Template file not found: {template_file_path}", "error")
        raise FileNotFoundError(f"Template file not found: {template_file_path}")
    
    with open(template_file_path, "r", encoding="utf-8") as f:
        return f.read()

def generate_tools_json(csv_path: str, templates_path: str, logger: Callable = print) -> str | None:
    """
    Generates a combined JSON string from a CSV input and several JSON templates.

    Args:
        csv_path (str): The path to the input CSV file.
        templates_path (str): The path to the directory containing JSON templates.
        logger (Callable): A logger function (like `add_output_message`) to send feedback.

    Returns:
        str | None: The generated JSON string, or None if an error occurred.
    """
    try:
        df = pd.read_csv(csv_path)
        logger(f"Successfully loaded {len(df)} rows from {os.path.basename(csv_path)}.", "info")
    except FileNotFoundError:
        logger(f"CSV file not found at: {csv_path}", "error")
        return None
    except Exception as e:
        logger(f"Error reading CSV file: {e}", "error")
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
        return None # Error already logged by _get_template_content

    tools_2_json = json.loads(tools_2_template)
    tools_3_json = json.loads(tools_3_template)
    
    df_sorted = df.sort_values(by='title', key=lambda x: x.str.lower())

    for index, row in df_sorted.iterrows():
        if pd.notna(row['type']) and pd.notna(row['title']) and pd.notna(row['link']):
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
                tools_part = tools_2_part
                for key, value in replacements.items():
                    tools_part = tools_part.replace(key, value)
                tools_2_json['children'].append(json.loads(tools_part))
                tool_2_count += 1
            elif category == '3.0':
                tools_part = tools_3_part
                for key, value in replacements.items():
                    tools_part = tools_part.replace(key, value)
                tools_3_json['children'].append(json.loads(tools_part))
                tool_3_count += 1
        else:
            continue

    tools_2_json_result = json.dumps(tools_2_json, ensure_ascii=False, indent=2)
    tools_3_json_result = json.dumps(tools_3_json, ensure_ascii=False, indent=2)
    
    final_json_str = tools_main_template.replace("<tools_2_placeholder>", tools_2_json_result).replace("<tools_3_placeholder>", tools_3_json_result)
    
    if _is_valid_json(final_json_str, logger):
        logger(f"Successfully generated JSON. Found {tool_2_count} tools in category 2.0 and {tool_3_count} in 3.0.", "success")
        return final_json_str
    else:
        logger("Failed to generate valid JSON.", "error")
        return None
