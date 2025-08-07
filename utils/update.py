def update_faq_translatability(json_str: str) -> str:
    """更新JSON字符串中的翻译状态"""
    target = '"text":"FAQ","tag":"h2","isNeedTranslate":false,'
    to_target = '"text":"FAQ","tag":"h2","isNeedTranslate":true,'
    return json_str.replace(target, to_target)

def update_chinese_mockup_tool_and_resource(json_str: str) -> str:
    """更新PNG为PNG图片；更新备受信赖公司；更新CTA为统一语句"""
    
def update_chinese_mockup_landing(json_str: str) -> str:
    pass