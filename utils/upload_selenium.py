from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time


login_url = "https://op.pacdora.com/login"
upload_url = "https://op.pacdora.com/upload"
timeout = 300
target_url_contains = "dashboard"
file_path = "/Volumes/shared/pacdora.com/330-ml-can-mockup/2.webp"

chrome_options = Options()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)

# 打开登录页面进行手动登录
print(f"正在打开登录页面: {login_url}")
driver.get(login_url)
print("请在浏览器中手动登录...")

# 等待URL包含dashboard，表示登录成功
try:
    WebDriverWait(driver, timeout).until(
        lambda d: target_url_contains in d.current_url
    )
    print("登录成功，检测到dashboard页面")
    
    # 登录成功后跳转到上传页面
    print(f"正在跳转到上传页面: {upload_url}")
    driver.get(upload_url)
except Exception as e:
    print(f"登录失败或超时: {e}")
    print(f"当前URL: {driver.current_url}")
    driver.quit()
    exit(1)

aws_option = driver.find_element(By.XPATH, """//*[@id="app"]/div/main/div/div/div/div/div[1]/div[1]/div/div/div[1]/div/div[3]""")
aws_option.click()



# 定位 <input type="file"> 元素
file_input = driver.find_element(By.XPATH, '//input[starts-with(@accept, "*")]')

# 确保文件路径是绝对路径
abs_file_path = os.path.abspath(file_path)
if not os.path.exists(abs_file_path):
    raise FileNotFoundError(f"File not found: {abs_file_path}")

# 发送文件路径
file_input.send_keys(abs_file_path)


# 等待上传完成并获取 CDN 路径
print("等待文件上传完成...")

# 使用更长的等待时间，确保文件完全上传
try:
    # 首先等待元素出现
    print("等待CDN链接元素出现...")
    cdn_element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div/main/div/div/div/div/div[2]/div[3]/div[2]'))
    )
    
    # 等待元素中出现文本（链接）
    print("等待CDN链接加载...")
    WebDriverWait(driver, 20).until(
        lambda d: cdn_element.text.strip() != ""
    )
    
    # 获取CDN链接
    cdn_url = cdn_element.text.strip()
    print(f"成功获取CDN链接: {cdn_url}")
    
    # 如果需要，也可以尝试获取href属性
    try:
        href_value = cdn_element.get_attribute("href")
        if href_value:
            print(f"链接的href属性: {href_value}")
    except:
        pass
    
    # 如果上面的方法没有获取到链接，尝试其他方法
    if not cdn_url:
        print("尝试其他方法获取CDN链接...")
        # 尝试查找所有可能包含链接的元素
        potential_elements = driver.find_elements(By.XPATH, '//div[contains(@class, "col")]')
        for elem in potential_elements:
            text = elem.text.strip()
            if text and ("http://" in text or "https://" in text):
                cdn_url = text
                print(f"通过备选方法找到CDN链接: {cdn_url}")
                break
                
except Exception as e:
    print(f"获取CDN链接失败: {e}")
    print("正在截图保存当前页面状态...")
    # 保存截图以便调试
    screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload_error.png")
    driver.save_screenshot(screenshot_path)
    print(f"截图已保存至: {screenshot_path}")
    
    # 打印页面源码以便调试
    print("\n页面HTML结构片段:")
    print(driver.page_source[:500] + "...")
    
    cdn_url = None

