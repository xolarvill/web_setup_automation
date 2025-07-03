import requests
import time
from urllib.parse import urlparse
from typing import Callable, Optional

def fetch_mockup_details(model_name_key: str, output_callback: Optional[Callable[[str, str], None]] = None) -> tuple:
    """
    根据模型名称或URL获取模型/刀模图的详细信息。

    参数:
        model_name_key (str): 模型名称键或包含模型ID的URL。
        output_callback (function, optional): 用于输出消息的回调函数。

    返回:
        tuple: 包含模型名称、图片URL和编辑链接的元组。
    """

    def log_message(message, msg_type="info"):
        if output_callback:
            output_callback(message, msg_type)
        else:
            print(message)

    # 根据 model_name_key 判断是获取刀模图还是普通模型的信息
    api_base_url = (
        "https://canary.pacdora.com/api/v2/models/details?nameKey="
        if "-dieline-" in model_name_key
        else "https://canary.pacdora.com/api/v2/models/details?mockupNameKey="
    )

    DEFAULT_MODEL_NAME = "CHECK YOUR SPELLING"
    DEFAULT_IMAGE_URL = "//cdn.pacdora.com/ui/topic/f420bfb0-3584-47ae-88cd-bb5591f49e78.png"
    DEFAULT_EDITOR_LINK = "/404"

    model_name = DEFAULT_MODEL_NAME
    image = DEFAULT_IMAGE_URL
    editor_link = DEFAULT_EDITOR_LINK

    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 1

    try:
        if model_name_key.strip().startswith("https:"):
            parsed_url = urlparse(model_name_key)
            editor_link = parsed_url.path
            model_id = editor_link.split("/")[-1]
            if not model_id:
                log_message(f"URL解析失败：无法从 '{model_name_key}' 中提取模型ID。", "error")
                return model_name, image, editor_link

            request_url = api_base_url + model_id
            log_message(f"Fetching details for: {model_id}", "info")

            for attempt in range(MAX_RETRIES):
                try:
                    response = requests.get(request_url, timeout=5)
                    response.raise_for_status()

                    data = response.json().get("data", {})
                    if not data:
                        log_message(f"API响应数据为空或格式不正确：{response.text}", "warning")
                        if attempt == MAX_RETRIES - 1:
                            return model_name, image, editor_link
                        else:
                            time.sleep(RETRY_DELAY_SECONDS)
                            continue

                    model_name = data.get("mockupName", "").strip()
                    try:
                        image = data["modeSetting"][0]["image"].strip()
                    except (KeyError, IndexError):
                        image = data.get("image", "").strip()
                    
                    log_message(f"Successfully fetched details for: {model_id}", "success")
                    break
                except requests.exceptions.Timeout:
                    log_message(f"请求超时：第 {attempt + 1} 次尝试连接 {request_url} 超时。", "warning")
                except requests.exceptions.HTTPError as e:
                    log_message(f"HTTP错误：第 {attempt + 1} 次尝试请求 {request_url} 失败，状态码：{e.response.status_code}。", "error")
                except requests.exceptions.RequestException as e:
                    log_message(f"请求异常：第 {attempt + 1} 次尝试请求 {request_url} 发生错误：{e}", "error")
                except ValueError as e:
                    log_message(f"JSON解析错误：无法解析响应数据，错误：{e}。响应内容：{response.text}", "error")
                except Exception as e:
                    log_message(f"内部错误：处理请求 {request_url} 时发生未知错误：{e}", "error")

                if attempt < MAX_RETRIES - 1:
                    log_message(f"Retrying in {RETRY_DELAY_SECONDS} second(s)...", "info")
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    log_message(f"已达到最大重试次数，未能成功获取 {model_id} 的详细信息。", "error")
                    return model_name, image, editor_link

    except Exception as e:
        log_message(f"发生初始化或URL解析错误：{e}", "error")

    return model_name, image, editor_link


if __name__ == "__main__":
    a,b,c = fetch_mockup_details("https://www.pacdora.com/mockup-detail/clipboard-menu-mockup-911447")
    print(a,b,c)