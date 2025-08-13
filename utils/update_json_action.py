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
 
    
def iterate(json_str: str,
            step1: str,
            step2: str,
            step3: str,
            feature1: str,
            feature2: str,
            feature3: str,
            feature4: str
            ) -> str:
    """
    利用JSON中的占位图埋点一次性替换真实图片
    """
    try:
        # 定义需要替换的占位图片和对应的新CDN链接
        replacements = {
            'https://cdn.pacdora.com/page-img/d49f2f9a-e538-43c0-90cb-7c3ea47c3e56.png': step1,
            'https://cdn.pacdora.com/page-img/1254454b-396c-4b92-8e4d-77a7ecbf3752.png': step2,
            'https://cdn.pacdora.com/page-img/8166ae2d-77e4-4189-a128-ca98b768d846.png': step3,
            'https://cdn.pacdora.com/page-img/46816878-bc73-443c-b7b3-328202fd844a.png': feature1,
            'https://cdn.pacdora.com/page-img/0229c1bc-09ab-431c-aebc-22b9b34da372.png': feature2,
            'https://cdn.pacdora.com/page-img/91d172ef-0de5-4bd2-a088-c3156b758113.png': feature3,
            'https://cdn.pacdora.com/page-img/45d178a0-f6ce-4027-a2a7-e0b82808af5a.png': feature4
        }

        # 使用字典推导式一次性完成所有替换
        for old_url, new_url in replacements.items():
            json_str = json_str.replace(old_url, new_url)
            
        return json_str
                
    # 稳健抛出可能的错误
    except Exception as e:
        return e