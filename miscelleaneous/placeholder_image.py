from PIL import Image

# 创立一个1400x1000的纯黑占位图片

# 设置图像尺寸
width = 1400
height = 1000

# 创建一个新的RGB图像，黑色背景（R=0, G=0, B=0）
black_image = Image.new('RGB', (width, height), (0, 0, 0))

# 保存图像为PNG格式
black_image.save('black_image.png')

print(f"成功创建了{width}x{height}大小的纯黑PNG图像：black_image.png")

# 上传后得到https://cdn.pacdora.com/web-assets/2e22e2d6-fd1d-4a09-925b-7ba5d403d82b.png