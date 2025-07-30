from re import search
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import pyperclip


"""
使用selenium创建bot批量切换faq翻译状态
自动化程度：全自动 + 人工监督分岔节点
"""


login_url = "https://op.pacdora.com/login"
dashboard_url_contains = "dashboard"
operate_url = "https://op.pacdora.com/topic/List"
operate_url_contains = "List"
edit_url_contains = "edit"
timeout = 500
with open('miscellaneous/web_ui_xpath.json', 'r') as f:
    xpath = json.load(f)
list = ["white-t-shirt-mockup"]

chrome_options = Options()
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
    )

# 打开登录页面进行手动登录
print(f"🚩正在打开登录页面: {login_url}")
driver.get(login_url)
print("🚩请在浏览器中手动登录...")

# 等待URL包含dashboard，表示登录成功
try:
    WebDriverWait(driver, timeout).until(lambda d: dashboard_url_contains in d.current_url)
    print("✅登录成功，检测到dashboard页面")
except Exception as e:
    print(f"    ❌登录失败或超时: {e}")
    driver.quit()
    exit(1)

# 跳转到操作页面
print(f"🚩正在跳转到操作页面: {operate_url}")
driver.get(operate_url)

try:
    WebDriverWait(driver, timeout).until(lambda d: operate_url_contains in d.current_url)
except Exception as e:
    print(f"    ❌跳转错误:{e}")
    driver.quit()
    exit(1)

# 循环处理
for target in list:
    try:
        print(f"🚩正在处理: {target}")
        # locate search input and click search button
        search_input = driver.find_element(By.XPATH, xpath["search_input"])
        search_input.send_keys(target)
        search_button = driver.find_element(By.XPATH, xpath["search_button"])
        search_button.click()
        
        # wait for search complete and use css selector to ensure there is only one element
        tbody_element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#app > div > main > div > div > div.tables-basic > div > div:nth-child(2) > div > div.v-data-table.theme--light > div > table > tbody"))
        )
        tr_elements = tbody_element.find_elements(By.TAG_NAME, "tr")
        
        # if there is more than one search result, let user manually interfare and decide, then back to terminal and input. 
        # if there is only one result, proceed
        if len(tr_elements) >= 2:
            print(f"  ⚠️{target}有多个搜索结果，请手动处理")
            manual_confirm = input("❓是否继续？")
        else:
            edit_button = driver.find_element(By.XPATH, xpath["edit_button"])
            edit_button.click()
            open_edit_page_option = driver
            open_edit_page_option.click()
            print("🚩正在打开编辑页")
            
        # now it will automatically jump to the editor page, https://op.pacdora.com/topic/edit?type=update&id=xxx, where the last xxx is specific unique id.
        WebDriverWait(driver, timeout).until(lambda d: edit_url_contains in d.current_url)
        print("✅打开编辑页成功")
        
        open_pop_up_editor_button = driver.find_element(By.XPATH,xpath["open_pop_up_editor_button"])
        open_pop_up_editor_button.click()
        
        # now it automatically open a new tab, and this new tab will jump to https://canary.pacdora.com/layout-ui
        # remember the old edit tab is still there
        WebDriverWait(driver, timeout).until(lambda d: "layout-ui" in d.current_url)
        print("✅成功打开可视化编辑器")
        
        # get json and do replacing
        json_tool_button = driver.find_element(By.XPATH, xpath["json_tool_button"])
        json_tool_button.click()
        get_json_button = json_tool.find_element(By.XPATH, xpath["get_json_button"])
        get_json_button.click()
        print("✅成功获取json")
        
        # now the json will be copied to clipboard
        json_str = pyperclip.paste()
        replaced_str = update(json_str)
        print("✅成功替换json")
        
        json_input = driver.find_element(By.XPATH, xpath["json_input"])
        json_input.send_keys(replaced_str)
        json_input_save_button = driver.find_element(By.XPATH, xpath["json_input_save_button"])
        json_input_save_button.click()
        save_pop_up_editor_button = driver.find_element(By.XPATH, xpath["save_pop_up_editor_button"])
        save_pop_up_editor_button.click()
        print("✅成功保存json")

        # this will automatically close the new tab, which is https://canary.pacdora.com/layout-ui
        WebDriverWait(driver, timeout).until(lambda d: len(d.window_handles) == 1)
        print("✅成功关闭可视化编辑器标签页")
        
        # save and wait for automatic refresh
        save_pop_up_editor_button = driver.find_element(By.XPATH, xpath["save_pop_up_editor_button"])
        save_pop_up_editor_button.click()
        print("✅成功保存编辑页")
        WebDriverWait(driver, timeout).until(lambda d: "List" in d.current_url)
        print(f"😍{target}已成功更新")
    except Exception as e:
        print(f"    ❌更新失败：{e}")
        driver.quit()
        exit(1)
        
def update(json_str):
    target = '"text":"FAQ","tag":"h2","isNeedTranslate":false,'
    to_target = '"text":"FAQ","tag":"h2","isNeedTranslate":true,'
    json_str = json_str.replace(target, to_target)
    return json_str
    
def read_csv_to_list(csv_path: str) -> list:
    # csv文件是一个没有表头的2列n行的结构，读取每行的第一个列中的文本当作表格的内容
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        list = []
        for row in reader:
            list.append(row[0])
        return list