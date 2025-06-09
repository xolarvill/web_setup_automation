from typing import List

def extract_cutout_nextline(text: str, keywords: List[str]) -> dict:
    """
    从文本中提取以指定关键词开头的行的下一段内容。

    :param text: 输入的多行字符串
    :param keywords: 关键词列表
    :return: dict，key为关键词，value为对应cutout内容
    """
    lines = text.splitlines()
    cutouts = {}
    keyword_set = set(keywords)
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        for keyword in keyword_set:
            if line.startswith(keyword):
                # 提取下一段内容
                cutout_lines = []
                i += 1
                while i < len(lines) and lines[i].strip() != "":
                    cutout_lines.append(lines[i])
                    i += 1
                cutouts[keyword] = "\n".join(cutout_lines)
                break
        i += 1
    return cutouts

def extract_cutout_currentline(text: str, keywords: List[str])-> dict: 
    """
    提取以指定关键词开头的所有行。
    :param text: 输入的多行字符串
    :param keywords: 关键词列表
    :return: dict，key为关键词，value为所有匹配行组成的列表
    """
    lines = text.splitlines()
    keyword_set = set(keywords)
    cutouts = {k: [] for k in keywords}
    for line in lines:
        stripped = line.strip()
        for keyword in keyword_set:
            if stripped.startswith(keyword):
                cutouts[keyword].append(line)
    return cutouts

# 示例用法
if __name__ == "__main__":
    sample_text = """
    meta description
    这是描述内容
    可以有多行

    title
    这是标题

    meta keywords
    关键词1, 关键词2
    """
    keywords = ["meta description", "title", "meta keywords"]
    result = extract_cutout_nextline(sample_text, keywords)
    for k, v in result.items():
        print(f"{k}:\n{v}\n")