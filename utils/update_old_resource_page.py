
# read clipboard
# 从剪切板读取内容
def update_old_resource_page(t: str) -> str:
    place1 = '''"aspectRatio":"1","object-fit":"cover","border":"solid 1px rgba(25, 25, 25, 1)","borderRadius":"16px 16px 16px 16px"'''
    place1_to_be = '''"aspectRatio": "1","object-fit": "cover","border": "solid 1px rgba(25, 25, 25, 1)","borderRadius": "16px 16px 16px 16px","background": "#ffffff"'''
                                                                    
    place2 = '''],"curStatus":"default","status":{"hover":{"<980":{'''
    place2_to_be = '''],"curStatus": "hover","status": {"hover": {"<980": {'''

    result = t.replace(place1,place1_to_be)
    result = result.replace(place2,place2_to_be)

    return result
