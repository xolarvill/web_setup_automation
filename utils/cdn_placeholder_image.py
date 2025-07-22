
def cdn_placeholder_image(cdn_address: str, type: str) -> str:
    '''
    检查cdn链接是否为空，如果空则返回一个1400x1000的纯黑图片作为占位
    '''
    if type == 'a': 
        if cdn_address:
            return cdn_address
        else:
            return "https://cdn.pacdora.com/page-img/46816878-bc73-443c-b7b3-328202fd844a.png"
    elif type == 'b': 
        if cdn_address:
            return cdn_address
        else:
            return "https://cdn.pacdora.com/page-img/0229c1bc-09ab-431c-aebc-22b9b34da372.png"
    elif type == 'c': 
        if cdn_address:
            return cdn_address
        else:
            return "https://cdn.pacdora.com/page-img/91d172ef-0de5-4bd2-a088-c3156b758113.png"
    elif type == 'd': 
        if cdn_address:
            return cdn_address
        else:
            return "https://cdn.pacdora.com/page-img/45d178a0-f6ce-4027-a2a7-e0b82808af5a.png"
    elif type == '1': 
        if cdn_address:
            return cdn_address
        else:
            return "https://cdn.pacdora.com/page-img/d49f2f9a-e538-43c0-90cb-7c3ea47c3e56.png"
    elif type == '2': 
        if cdn_address:
            return cdn_address
        else:
            return "https://cdn.pacdora.com/page-img/1254454b-396c-4b92-8e4d-77a7ecbf3752.png"
    elif type == '3': 
        if cdn_address:
            return cdn_address
        else:
            return "https://cdn.pacdora.com/page-img/8166ae2d-77e4-4189-a128-ca98b768d846.png"
    elif type == 'banner': 
        if cdn_address:
            return cdn_address
        else:
            return "https://cdn.pacdora.com/page-img/193feffa-bcb9-4536-8ca2-8b33ff92fa49.png"
    else:
        if cdn_address:
            return cdn_address
        else:
            return "https://cdn.pacdora.com/web-assets/2e22e2d6-fd1d-4a09-925b-7ba5d403d82b.png"