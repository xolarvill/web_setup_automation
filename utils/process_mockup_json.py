# this was originally written by Mirtle. I took the core part of it out of the old cask.
import json

def process_json_template(web_json_path: str, children_data_list: list) -> json:
    """
    处理包含{{}}占位符的JSON模板
    
    Args:
        web_json_path: web.json文件路径
        children_data_list: 子容器数据列表，每个元素是一个字典
    """
    
    # 读取web.json模板
    with open(web_json_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # 将children数据转换为JSON字符串（不带最外层的花括号，因为要嵌入到数组中）
    children_json_strings = []
    for child_data in children_data_list:
        child_json = json.dumps(child_data, ensure_ascii=False, separators=(',', ':'))
        children_json_strings.append(child_json)
    
    # 替换占位符
    for i, child_json in enumerate(children_json_strings, 1):
        placeholder = f"{{{{children{i}}}}}"
        template_content = template_content.replace(placeholder, child_json)
    
    # 解析最终的JSON
    final_json = json.loads(template_content)
    
    return final_json

# 使用示例
if __name__ == "__main__":
    # 示例：准备子容器数据
    children_data = [
        {
            "type": "container",
            "name": "container1", 
            "props": {"width": 100, "height": 200}
        },
        {
            "type": "container", 
            "name": "container2",
            "props": {"width": 150, "height": 250}
        },
        {
            "type": "container",
            "name": "container3", 
            "props": {"width": 200, "height": 300}
        }
    ]
    
    # 处理模板
    result = process_json_template('web.json', children_data)
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 保存到新文件
    with open('web_final.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)