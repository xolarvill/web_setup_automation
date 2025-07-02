
def cdn_placeholder_image(cdn_address: str) -> str:
    '''
    检查cdn链接是否为空，如果空则返回一个1400x1000的纯黑图片作为占位
    '''
    if cdn_address:
        return cdn_address
    else:
        return "https://cdn.pacdora.com/web-assets/2e22e2d6-fd1d-4a09-925b-7ba5d403d82b.png"