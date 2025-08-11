import re

def update_faq_translatability(json_str: str) -> str:
    """更新JSON字符串中的翻译状态"""
    target = '"text":"FAQ","tag":"h2","isNeedTranslate":false,'
    to = '"text":"FAQ","tag":"h2","isNeedTranslate":true,'
    return json_str.replace(target, to)

def update_chinese_mockup_tool_and_resource(json_str: str) -> str:
    """2025.8.7 更新PNG为PNG图片；更新备受信赖公司；更新CTA为统一语句"""
    target1 = "PNG"
    to1 = "PNG图片"
    temp1 = json_str.replace(to1,target1)
    temp2 = temp1.replace(target1,to1)
    
    target2 = ""
    to2 = ""
    temp3 = temp2.replace(target2,to2)
    
    target3 = ""
    to3 = ""
    temp4 = temp3.replace(target3,to3)
    return temp4
    
def update_chinese_mockup_landing(json_str: str) -> str:
    """2025.8.7 替换H1和H1p中的内容"""
    target = ""
    to = ""
    return json_str.replace(target,to)