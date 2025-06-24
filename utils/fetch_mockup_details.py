import requests
import time
from urllib.parse import urlparse

def fetch_mockup_details(model_name_key: str) -> tuple:
    """
    根据模型名称或URL获取模型/刀模图的详细信息。

    参数:
        model_name_key (str): 模型名称键或包含模型ID的URL。

    返回:
        tuple: 包含模型名称、图片URL和编辑链接的元组。
    """

    # 根据 model_name_key 判断是获取刀模图还是普通模型的信息
    # 使用 in 操作符而不是 find != -1 更具可读性
    api_base_url = (
        "https://canary.pacdora.com/api/v2/models/details?nameKey="
        if "-dieline-" in model_name_key
        else "https://canary.pacdora.com/api/v2/models/details?mockupNameKey="
    )

    # 初始化默认值，这些值在获取失败时返回
    # 使用常量可以避免魔法字符串，提高可维护性
    DEFAULT_MODEL_NAME = "CHECK YOUR SPELLING"
    DEFAULT_IMAGE_URL = "//cdn.pacdora.com/ui/topic/f420bfb0-3584-47ae-88cd-bb5591f49e78.png"
    DEFAULT_EDITOR_LINK = "/404"

    model_name = DEFAULT_MODEL_NAME
    image = DEFAULT_IMAGE_URL
    editor_link = DEFAULT_EDITOR_LINK

    # 预设最大重试次数和重试间隔
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 1

    try:
        # 检查 model_name_key 是否为有效的 HTTPS URL
        # strip() 确保处理开头和结尾的空格
        if model_name_key.strip().startswith("https:"):
            parsed_url = urlparse(model_name_key)
            editor_link = parsed_url.path
            # 从 URL 路径中提取模型 ID
            # 增加对 model_id 是否为空的检查
            model_id = editor_link.split("/")[-1]
            if not model_id:
                print(f"URL解析失败：无法从 '{model_name_key}' 中提取模型ID。")
                return model_name, image, editor_link

            request_url = api_base_url + model_id

            # 循环重试机制，增加稳健性
            for attempt in range(MAX_RETRIES):
                try:
                    response = requests.get(request_url, timeout=5)  # 增加请求超时
                    response.raise_for_status()  # 对 4xx/5xx 响应抛出异常

                    data = response.json().get("data", {})
                    if not data:
                        print(f"API响应数据为空或格式不正确：{response.text}")
                        # 如果是最后一次尝试，则直接返回默认值
                        if attempt == MAX_RETRIES - 1:
                            return model_name, image, editor_link
                        else:
                            time.sleep(RETRY_DELAY_SECONDS)
                            continue

                    model_name = data.get("mockupName", "").strip()
                    # 优先从 modeSetting 中获取图片，如果失败则从 image 字段获取
                    # 使用 get 避免 KeyError，同时提供默认空字符串
                    try:
                        image = data["modeSetting"][0]["image"].strip()
                    except (KeyError, IndexError):
                        image = data.get("image", "").strip()
                    break  # 成功获取数据，跳出重试循环
                except requests.exceptions.Timeout:
                    print(f"请求超时：第 {attempt + 1} 次尝试连接 {request_url} 超时。")
                except requests.exceptions.HTTPError as e:
                    print(f"HTTP错误：第 {attempt + 1} 次尝试请求 {request_url} 失败，状态码：{e.response.status_code}。")
                except requests.exceptions.RequestException as e:
                    print(f"请求异常：第 {attempt + 1} 次尝试请求 {request_url} 发生错误：{e}")
                except ValueError as e: # 捕获 JSON 解析错误
                    print(f"JSON解析错误：无法解析响应数据，错误：{e}。响应内容：{response.text}")
                except Exception as e:
                    print(f"内部错误：处理请求 {request_url} 时发生未知错误：{e}")

                # 如果不是最后一次尝试，则等待后重试
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    print(f"已达到最大重试次数，未能成功获取 {model_id} 的详细信息。")
                    return model_name, image, editor_link # 最终返回默认值

    except Exception as e:
        # 捕获 URL 解析或其他初期可能发生的异常
        print(f"发生初始化或URL解析错误：{e}")

    return model_name, image, editor_link

if __name__ == "__main__":
    a,b,c = fetch_mockup_details("https://www.pacdora.com/mockup-detail/clipboard-menu-mockup-911447")
    print(a,b,c)