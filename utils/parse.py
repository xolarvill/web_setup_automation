from typing import List
import re

def extract_cutout_nextline(text: str, keywords: List[str]) -> dict:
    """
    从文本中提取以指定关键词开头的行的下一行内容（比较时大小写不敏感，提取原文时保留原始大小写）。

    :param text: 输入的多行字符串
    :param keywords: 关键词列表
    :return: dict，key为关键词，value为对应cutout内容（只取下一行）
    """
    lines = text.splitlines()
    cutouts = {}
    # 构建小写关键词集合用于比较
    keyword_map = {k.lower(): k for k in keywords}
    found = set()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        for kw_lower, kw_orig in keyword_map.items():
            if kw_orig not in found and stripped.lower().startswith(kw_lower):
                # 只提取第一次出现的下一行内容，保留原文
                if i + 1 < len(lines):
                    cutouts[kw_orig] = lines[i + 1].rstrip()
                else:
                    cutouts[kw_orig] = ""
                found.add(kw_orig)
                break
        i += 1
    # 保证所有关键词都有返回值
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

def parse_faq_text(text) -> list:
    """
    解析FAQ文本，去除第一行，按空行分块处理问答对
    
    Args:
        text (str): 原始FAQ文本
        
    Returns:
        list: 包含字典的列表，每个字典有'question'和'answer'键
    """
    # 按行分割文本
    lines = text.strip().split('\n')
    
    # 去除第一行
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
            answer = ' '.join(block[1:])  # 将多行答案连接成一个字符串
            
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

# 示例用法
if __name__ == "__main__":
    str = '''
        Browse more menu mockups now
        https://www.pacdora.com/mockup-detail/clipboard-menu-mockup-911447
        https://www.pacdora.com/mockup-detail/bifold-menu-card-mockup-911439
        https://www.pacdora.com/mockup-detail/menu-mockup-911458
        https://www.pacdora.com/mockup-detail/clipboard-mockup-911448
        https://www.pacdora.com/mockup-detail/table-tent-mockup-911459
        https://www.pacdora.com/mockup-detail/menu-mockup-911455
        https://www.pacdora.com/mockup-detail/trifold-brochure-mockup-24200402
        https://www.pacdora.com/mockup-detail/a4-flyer-mockup-608040
        View all menu mockups
        '''
    result = extract_url(str)
    print(result)