import re

def update_faq_translatability(json_str: str) -> str:
    """更新FAQ模块中标题的翻译状态"""
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
    
    
def update_old_resource_page(t: str) -> str:
    """
    替换resource页中透明底为纯白底
    """
    place1 = '''"aspectRatio":"1","object-fit":"cover","border":"solid 1px rgba(25, 25, 25, 1)","borderRadius":"16px 16px 16px 16px"'''
    place1_to_be = '''"aspectRatio": "1","object-fit": "cover","border": "solid 1px rgba(25, 25, 25, 1)","borderRadius": "16px 16px 16px 16px","background": "#ffffff"'''
                                                                    
    place2 = '''],"curStatus":"default","status":{"hover":{"<980":{'''
    place2_to_be = '''],"curStatus": "hover","status": {"hover": {"<980": {'''

    result = t.replace(place1,place1_to_be)
    result = result.replace(place2,place2_to_be)

    return result


def update_login_requirment(t: str) -> str:
    """
    为样机页增加登录功能
    """
    target = '"domDataset":[{"'
    to = '"domDataset":[{"key":"need-login","value":"true"},{"'
    result = t.replace(target, to)
    return result
 
    
def iterate(json_str: str) -> str:
    pass