from typing import List
import re

def extract_cutout_nextline(text: str, keywords: List[str]) -> dict:
    """
    从文本中提取以指定关键词开头的行的下一行内容（比较时大小写不敏感，提取原文时保留原始大小写）。
    此函数会跳过关键词后的空行，直到找到第一个非空行。

    :param text: 输入的多行字符串
    :param keywords: 关键词列表
    :return: dict，key为关键词，value为对应cutout内容
    """
    lines = text.splitlines()
    cutouts = {}
    keyword_map = {k.lower(): k for k in keywords}
    found_keywords = set()

    for i, line in enumerate(lines):
        stripped_line = line.strip()
        for kw_lower, kw_orig in keyword_map.items():
            if kw_orig not in found_keywords and stripped_line.lower().startswith(kw_lower):
                # 找到关键词，现在开始查找下一个非空行
                next_line_index = i + 1
                while next_line_index < len(lines) and not lines[next_line_index].strip():
                    next_line_index += 1  # 跳过空行

                if next_line_index < len(lines):
                    cutouts[kw_orig] = lines[next_line_index].rstrip()
                else:
                    cutouts[kw_orig] = ""  # 如果关键词后没有非空行
                
                found_keywords.add(kw_orig)
                break  # 处理完一个关键词后，跳出内层循环

    # 确保所有关键词都有返回值
    for keyword in keywords:
        if keyword not in cutouts:
            cutouts[keyword] = ""
            
    return cutouts

def extract_cutout_currentline(text: str, keywords: List[str]) -> dict:
    """
    提取以指定关键词开头的所有行（比较时大小写不敏感，提取原文时保留原始大小写）。
    :param text: 输入的多行字符串
    :param keywords: 关键词列表
    :return: dict，key为关键词，value为所有匹配行组成的列表
    """
    lines = text.splitlines()
    # 构建小写关键词集合用于比较
    keyword_map = {k.lower(): k for k in keywords}
    cutouts = {k: [] for k in keywords}
    found = set()
    for line in lines:
        stripped = line.strip()
        for kw_lower, kw_orig in keyword_map.items():
            if kw_orig not in found and stripped.lower().startswith(kw_lower):
                cutouts[kw_orig].append(line.rstrip())
                found.add(kw_orig)
    return cutouts

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
