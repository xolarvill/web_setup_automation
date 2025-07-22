from PIL import Image, ImageDraw, ImageFont
import os

def generate_images_with_identifiers(
    identifiers: list[str],
    width: int = 1400,
    height: int = 1000,
    font_size: int = 100,
    # 尝试使用常见的系统字体路径，请根据你的操作系统进行调整
    # Windows 示例: "C:/Windows/Fonts/arial.ttf" 或 "C:/Windows/Fonts/simsun.ttc"
    # macOS 示例: "/Library/Fonts/Arial.ttf" 或 "/System/Library/Fonts/Supplemental/PingFang.ttc"
    # Linux 示例: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    # 这里我们给出一个常用的通用字体名，程序会尝试查找
    default_font_name: str = "arial.ttf"
) -> None:
    """
    为给定的标识符列表生成纯黑图片，并在图片中央添加对应的标识符文本。
    尝试加载通用字体文件以支持字号控制。

    Args:
        identifiers: 包含要添加到图片上的字符串标识符的列表。
        width: 图片的宽度（像素）。
        height: 图片的高度（像素）。
        font_size: 标识符文本的字体大小。
        default_font_name: 一个通用的字体文件名，程序会尝试在常见字体路径中查找。
    """
    font_paths = [
        # Windows paths
        os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Fonts', default_font_name),
        # macOS paths
        os.path.join('/Library/Fonts', default_font_name),
        os.path.join('/System/Library/Fonts', default_font_name),
        os.path.join('/System/Library/Fonts/Supplemental', default_font_name), # For PingFang TC, SC etc.
        # Linux paths (common locations)
        os.path.join('/usr/share/fonts/truetype', default_font_name),
        os.path.join('/usr/share/fonts/truetype/dejavu', default_font_name),
        os.path.join('/usr/share/fonts/opentype', default_font_name),
    ]

    font = None
    for path in font_paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, font_size)
                print(f"成功加载字体文件: {path}")
                break
            except IOError:
                print(f"尝试加载字体 {path} 失败，尝试下一个路径。")
    
    if font is None:
        print(f"警告：无法加载通用字体 '{default_font_name}'。将使用Pillow默认的固定大小字体，字号参数 '{font_size}' 将被忽略。")
        font = ImageFont.load_default()

    for identifier in identifiers:
        # 创建一个新的RGB图像，黑色背景
        black_image = Image.new('RGB', (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(black_image)

        # 获取文本尺寸
        try:
            # Pillow 10.0.0+ 推荐使用 textbbox
            bbox = draw.textbbox((0, 0), identifier, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError: # 兼容旧版本Pillow，使用 textsize
            text_width, text_height = draw.textsize(identifier, font=font)


        # 计算文本在图片中心的位置
        x = (width - text_width) / 2
        y = (height - text_height) / 2

        # 在图片上绘制白色文本
        draw.text((x, y), identifier, fill=(255, 255, 255), font=font)

        # 保存图像为PNG格式，文件名包含标识符
        # 为了避免文件名冲突，如果标识符包含特殊字符，可以进行简单的清理
        safe_identifier = "".join([c if c.isalnum() else "_" for c in identifier])
        file_name = f"black_image_{safe_identifier}.png"
        black_image.save(file_name)
        print(f"成功创建了{width}x{height}大小的纯黑PNG图像：{file_name}，并添加标识符：'{identifier}'")

if __name__ == "__main__":
    # 示例用法
    # 尝试使用你系统中实际存在的字体文件，例如在Windows上可能就是 "arial.ttf"
    # 如果你确定某个字体文件存在，可以直接提供完整路径，例如:
    # my_identifiers = ["Hello", "World", "Python", "Gemini"]
    # generate_images_with_identifiers(my_identifiers, default_font_name="C:/Windows/Fonts/simsun.ttc")

    # 使用默认的尝试查找逻辑
    my_identifiers = ["1", "2", "3", "a", "b", "c", "d", "banner"]
    generate_images_with_identifiers(my_identifiers)

    # print("\n--- 尝试使用一个不存在的字体名，观察回退到默认字体且字号参数被忽略的情况 ---")
    # generate_images_with_identifiers(["Fallback Test"], default_font_name="nonexistent_font.ttf", font_size=200)

# 上传后得到纯黑 https://cdn.pacdora.com/web-assets/2e22e2d6-fd1d-4a09-925b-7ba5d403d82b.png
# "black_image_banner": "https://cdn.pacdora.com/page-img/193feffa-bcb9-4536-8ca2-8b33ff92fa49.png",
# "black_image_d": "https://cdn.pacdora.com/page-img/45d178a0-f6ce-4027-a2a7-e0b82808af5a.png",
# "black_image_c": "https://cdn.pacdora.com/page-img/91d172ef-0de5-4bd2-a088-c3156b758113.png",
# "black_image_b": "https://cdn.pacdora.com/page-img/0229c1bc-09ab-431c-aebc-22b9b34da372.png",
# "black_image_a": "https://cdn.pacdora.com/page-img/46816878-bc73-443c-b7b3-328202fd844a.png",
# "black_image_3": "https://cdn.pacdora.com/page-img/8166ae2d-77e4-4189-a128-ca98b768d846.png",
# "black_image_2": "https://cdn.pacdora.com/page-img/1254454b-396c-4b92-8e4d-77a7ecbf3752.png",
# "black_image_1": "https://cdn.pacdora.com/page-img/d49f2f9a-e538-43c0-90cb-7c3ea47c3e56.png"