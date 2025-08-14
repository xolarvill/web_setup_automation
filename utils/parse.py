from typing import List
import re

def extract_structured_fields(text: str) -> dict:
    """
    从结构化文本中提取字段信息
    专门处理包含URL、Title、Meta Description、Breadcrumb和链接信息的文本
    """
    lines = text.splitlines()
    result = {}
    
    # 初始化所有字段为空
    fields = ["URL", "Title", "Meta Description", "Breadcrumb"]
    for field in fields:
        result[field] = ""
    
    # 初始化链接字段
    result["view_text"] = ""
    result["view_link"] = ""
    result["try_text"] = ""
    result["try_link"] = ""
    result["view"] = ""
    result["try"] = ""
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 处理基础字段（URL, Title, Meta Description, Breadcrumb）
        for field in fields:
            # 匹配字段标识行（不区分大小写），注意这里没有**符号
            field_pattern = f"{field.lower()}:"
            if line.lower() == field_pattern:
                # 找到字段标识行，获取下一个非空行的内容
                next_i = i + 1
                while next_i < len(lines) and not lines[next_i].strip():
                    next_i += 1
                
                if next_i < len(lines):
                    result[field] = lines[next_i].strip()
                break
        
        # 特殊处理Breadcrumb部分的链接信息
        if line.lower() == "breadcrumb:":
            # 从当前位置开始查找包含 :/ 的行
            search_start = i + 1
            
            # 先获取Breadcrumb字段的值（第一个非空行）
            breadcrumb_found = False
            j = search_start
            while j < len(lines):
                current_line = lines[j].strip()
                
                # 如果遇到下一个字段标识，停止搜索
                if current_line.lower().endswith(":") and any(current_line.lower().startswith(f.lower()) for f in fields):
                    break
                
                # 如果还没找到breadcrumb值，且当前行不包含:/（不是链接行）
                if not breadcrumb_found and current_line and ":/" not in current_line:
                    result["Breadcrumb"] = current_line
                    breadcrumb_found = True
                
                # 处理包含链接的行
                elif ":/" in current_line:
                    # 查找最后一个冒号（不是://中的冒号）
                    colon_pos = current_line.rfind(":")
                    if colon_pos > 0 and not (colon_pos > 0 and current_line[colon_pos-1:colon_pos+2] == "://"):
                        text_part = current_line[:colon_pos].strip()
                        link_part = current_line[colon_pos+1:].strip()
                        
                        # 判断是view还是try
                        if text_part.lower().startswith("view"):
                            result["view_text"] = text_part
                            result["view_link"] = link_part
                            result["view"] = current_line
                        else:
                            # 其他情况都当作try处理
                            result["try_text"] = text_part
                            result["try_link"] = link_part
                            result["try"] = current_line
                
                j += 1
        
        i += 1
    
    return result

def segment(text: str) -> List[str]:
    '''
    将输入的文本按照#进行分割，并返回分割后的结果。
    '''
    segments = []
    current = []
    for line in text.splitlines():
        if line.strip() == "#":
            if current:
                segments.append('\n'.join(current).strip())
                current = []
        else:
            current.append(line)
    if current:
        segments.append('\n'.join(current).strip())
    return [seg for seg in segments if seg]

def parse_faq_text(text: str) -> list:
    """
    解析FAQ文本，去除第一行，按空行分块处理问答对。
    答案中的段落将用<p>标签包裹，有序列表将用<ol>和<li>标签包裹。
    如果答案仅包含段落，则在段落之间添加<p><br></p>。

    Args:
        text (str): 原始FAQ文本

    Returns:
        list: 包含字典的列表，每个字典有'question'和'answer'键
    """
    # 按行分割文本
    lines = text.strip().split('\n')

    # 去除第一行
    if lines:
        lines = lines[1:]

    # 按空行分块
    blocks = []
    current_block = []

    for line in lines:
        if line.strip() == '':  # 遇到空行
            if current_block:  # 如果当前块不为空
                blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line.strip())

    # 添加最后一个块（如果存在）
    if current_block:
        blocks.append(current_block)

    # 解析每个块为问答对
    faq_list = []
    for block in blocks:
        if len(block) >= 2:  # 至少要有问题和答案
            question = block[0]
            answer_lines = block[1:]
            
            # 检查回答中是否包含列表项
            has_list_item = any(re.match(r'^\d+\.\s', line) for line in answer_lines)
            
            answer_html_parts = []

            if has_list_item:
                # 包含列表项的逻辑
                in_ol = False
                for line in answer_lines:
                    is_list_item = re.match(r'^\d+\.\s', line)
                    if is_list_item:
                        if not in_ol:
                            in_ol = True
                            answer_html_parts.append('<ol>')
                        content = re.sub(r'^\d+\.\s', '', line)
                        answer_html_parts.append(f'<li>{content}</li>')
                    else:
                        if in_ol:
                            answer_html_parts.append('</ol>')
                            in_ol = False
                        if line.strip():
                            answer_html_parts.append(f'<p>{line}</p>')
                if in_ol:
                    answer_html_parts.append('</ol>')
            else:
                # 纯段落的逻辑
                p_tags = [f'<p>{line}</p>' for line in answer_lines if line.strip()]
                answer_html_parts.append('<p><br></p>'.join(p_tags))

            answer = ''.join(answer_html_parts)

            faq_list.append({
                'question': question,
                'answer': answer
            })

    return faq_list





def extract_url(text: str) -> list:
    """
    Extracts URLs from text that are in an ordered list format (e.g., "1. https://abc.com").

    参数:
        text (str): 包含URL的文本，可以是字符串或字符串列表
        
    返回:
        list: 提取的URL列表，已清理末尾标点符号
    """
    # If input is a list, join it into a single string
    if isinstance(text, list):
        text = "\n".join(text)
        
    # 修改正则表达式模式，直接匹配URL而不需要数字序号
    pattern = re.compile(r'(https?://[^\s]+)')
    
    # Find all matches in the text
    urls = pattern.findall(text)
    
    # 清理URL末尾可能的标点符号
    urls = [url.rstrip(',.;') for url in urls]
    
    return urls

import csv
from typing import Dict, List, Any

def parse_size_csv(file_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Parses a CSV file with mockup sizes, handling irregular format.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary where keys are mockup names
                                         and values are lists of size data.
    """
    sizes = {}
    with open(file_path, mode='r', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        header = next(reader)  # Skip header
        
        current_mockup_name = ""
        for row in reader:
            if not any(row) or len(row) < 5:  # Skip empty or malformed rows
                continue

            mockup_name = row[0].strip()
            # Check for new mockup group, ignore comment-like entries
            if mockup_name and not mockup_name.startswith('（'):
                current_mockup_name = mockup_name
                if current_mockup_name not in sizes:
                    sizes[current_mockup_name] = []

            # Process size string, removing quotes first
            size_str = row[3].strip().strip('"')
            if not size_str:
                continue

            try:
                size_parts = [int(s.strip()) for s in size_str.split(',')]
                
                width = size_parts[0] if len(size_parts) > 0 else 0
                height = size_parts[1] if len(size_parts) > 1 else 0
                depth = size_parts[2] if len(size_parts) > 2 else 0

                is_default = row[4].strip() == '默认值'

                if current_mockup_name:
                    sizes[current_mockup_name].append({
                        'width': width,
                        'height': height,
                        'depth': depth,
                        'is_default': is_default
                    })
            except ValueError:
                # Ignore rows where size is not a valid number list
                continue

    return {k: v for k, v in sizes.items() if v} # Filter out empty entries


def process_text_with_links(lines_list):
    """
    将包含链接信息的文本行列表转换为带HTML链接的整理文本
    
    没有潜在链接时代码能正常运行，会返回原始文本内容。
    
    Args:
        lines_list: 使用 text.splitlines() 并过滤空行后的列表
    
    Returns:
        str: 处理后的HTML文本
    """
    # 存储链接信息的字典
    links_dict = {}
    
    # 存储正文行
    content_lines = []
    
    # 遍历所有行，分离正文和链接
    for line in lines_list:
        line = line.strip()
        if ':' in line:
            # 检查是否是链接行（包含 tools/ 或 mockups/ 或 https://）
            parts = line.split(':', 1)
            if len(parts) == 2:
                link_text = parts[0].strip()
                url = parts[1].strip()
                
                # 判断是否是链接（包含常见的URL特征）
                if ('tools/' in url or 'mockups/' in url or 
                    url.startswith('http') or url.startswith('/')):
                    # 规范化URL
                    if url.startswith('http'):
                        # 完整URL保持不变
                        clean_url = url
                    elif url.startswith('/'):
                        # 已经是相对路径，保持不变
                        clean_url = url
                    else:
                        # 添加前缀斜杠
                        clean_url = '/' + url if not url.startswith('/') else url
                    
                    # 存储链接信息
                    links_dict[link_text] = clean_url
                    continue
        
        # 不是链接行，添加到正文
        content_lines.append(line)
    
    # 合并正文
    content = ' '.join(content_lines)
    
    # 处理文本中的链接替换
    for link_text, url in links_dict.items():
        # 创建HTML链接
        html_link = f'<a class="pac-ui-editor-a" href={url} target=_self gtm="" rel="noopener noreferrer">{link_text}</a>'
        
        # 在文本中查找并替换链接文本
        # 处理可能的复数形式和上下文
        if link_text in content:
            content = content.replace(link_text, html_link)
        else:
            # 尝试查找相似的文本（比如复数形式）
            # 检查是否有复数形式
            plural_form = link_text + 's'
            if plural_form in content:
                content = content.replace(plural_form, html_link)
            
            # 检查是否在句子中有稍微不同的形式
            words = content.split()
            for i, word in enumerate(words):
                # 移除标点符号进行比较
                clean_word = word.rstrip('.,!?;:')
                if clean_word == link_text or clean_word == plural_form:
                    words[i] = word.replace(clean_word, html_link)
                    break
            
            content = ' '.join(words)
    
    return content

# 示例用法
if __name__ == "__main__":
    # str = '''
    #     Browse more menu mockups now
    #     https://www.pacdora.com/mockup-detail/clipboard-menu-mockup-911447
    #     https://www.pacdora.com/mockup-detail/bifold-menu-card-mockup-911439
    #     https://www.pacdora.com/mockup-detail/menu-mockup-911458
    #     https://www.pacdora.com/mockup-detail/clipboard-mockup-911448
    #     https://www.pacdora.com/mockup-detail/table-tent-mockup-911459
    #     https://www.pacdora.com/mockup-detail/menu-mockup-911455
    #     https://www.pacdora.com/mockup-detail/trifold-brochure-mockup-24200402
    #     https://www.pacdora.com/mockup-detail/a4-flyer-mockup-608040
    #     View all menu mockups
    #     '''
    # result = extract_url(str)
    # print(result)
    
    # Test parse_size_csv
    sizes = parse_size_csv('../size.csv')
    import json
    print(json.dumps(sizes, indent=2))
