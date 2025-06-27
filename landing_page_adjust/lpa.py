#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import argparse
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException


class LandingPageAdjuster:
    """
    自动化调整落地页参数的工具类
    使用Selenium自动化操作网页，完成参数调整和保存
    """
    
    def __init__(self, url: str, headless: bool = False, timeout: int = 30):
        """
        初始化浏览器和设置
        
        Args:
            url: 需要打开的网页URL
            headless: 是否使用无头模式（不显示浏览器界面）
            timeout: 等待元素出现的超时时间（秒）
        """
        self.url = url
        self.timeout = timeout
        
        # 设置Chrome选项
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        
        # 初始化WebDriver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, timeout)
    
    def open_page(self) -> None:
        """
        打开指定的网页
        """
        print(f"正在打开页面: {self.url}")
        self.driver.get(self.url)
        time.sleep(2)  # 等待页面加载
    
    def click_element_by_xpath(self, xpath: str, wait_time: Optional[int] = None) -> bool:
        """
        通过XPath点击元素
        
        Args:
            xpath: 元素的XPath
            wait_time: 可选的等待时间，覆盖默认超时时间
            
        Returns:
            bool: 点击是否成功
        """
        timeout = wait_time if wait_time is not None else self.timeout
        try:
            print(f"尝试点击元素: {xpath}")
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            element.click()
            print("点击成功")
            return True
        except (TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
            print(f"点击元素失败: {e}")
            return False
    
    def input_text_by_xpath(self, xpath: str, text: str) -> bool:
        """
        通过XPath向元素输入文本
        
        Args:
            xpath: 元素的XPath
            text: 要输入的文本
            
        Returns:
            bool: 输入是否成功
        """
        try:
            print(f"尝试向元素 {xpath} 输入文本: {text}")
            element = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            element.clear()  # 清除现有文本
            element.send_keys(text)
            print("文本输入成功")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            print(f"输入文本失败: {e}")
            return False
    
    def wait_for_url_change(self, expected_url: str, timeout: Optional[int] = None) -> bool:
        """
        等待URL变为预期的URL
        
        Args:
            expected_url: 预期的URL
            timeout: 可选的等待时间，覆盖默认超时时间
            
        Returns:
            bool: URL是否变为预期值
        """
        wait_time = timeout if timeout is not None else self.timeout
        try:
            WebDriverWait(self.driver, wait_time).until(
                lambda driver: expected_url in driver.current_url
            )
            print(f"URL已变为: {self.driver.current_url}")
            return True
        except TimeoutException:
            print(f"等待URL变为 {expected_url} 超时，当前URL: {self.driver.current_url}")
            return False
    
    def wait_for_new_window(self, timeout: Optional[int] = None) -> bool:
        """
        等待新窗口打开
        
        Args:
            timeout: 可选的等待时间，覆盖默认超时时间
            
        Returns:
            bool: 是否检测到新窗口
        """
        wait_time = timeout if timeout is not None else self.timeout
        original_window = self.driver.current_window_handle
        try:
            WebDriverWait(self.driver, wait_time).until(
                lambda driver: len(driver.window_handles) > 1
            )
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    break
            print(f"已切换到新窗口，当前URL: {self.driver.current_url}")
            return True
        except TimeoutException:
            print("等待新窗口超时")
            return False
    
    def switch_back_to_main_window(self) -> None:
        """
        切换回主窗口（第一个窗口）
        """
        if len(self.driver.window_handles) > 0:
            self.driver.switch_to.window(self.driver.window_handles[0])
            print(f"已切换回主窗口，当前URL: {self.driver.current_url}")
    
    def adjust_landing_page(self, condition_value: str = ">5000,<10000") -> bool:
        """
        执行落地页调整流程
        
        Args:
            condition_value: 要设置的条件值
            
        Returns:
            bool: 整个流程是否成功完成
        """
        try:
            # 1. 点击编辑值按钮
            edit_button_xpath = '//*[@id="app"]/div[1]/main/div/div/div[2]/div/form/div[11]/div/div[2]/div/div[2]/button'
            if not self.click_element_by_xpath(edit_button_xpath):
                return False
            
            # 2. 等待新页面打开，并确认URL
            if not self.wait_for_new_window():
                return False
            
            expected_layout_url = "https://canary.pacdora.com/layout-ui"
            if not self.wait_for_url_change(expected_layout_url):
                return False
            
            # 3. 点击第二个滚动显隐容器
            container_xpath = '//*[@id="pane-0"]/div[1]/div[3]/div[2]'
            if not self.click_element_by_xpath(container_xpath):
                return False
            
            # 4. 修改条件值
            condition_input_xpath = '//*[@id="el-id-8393-894"]'
            if not self.input_text_by_xpath(condition_input_xpath, condition_value):
                return False
            
            # 5. 保存编辑器
            save_editor_xpath = '//*[@id="app"]/div/div[1]/div/div[2]/button[4]'
            if not self.click_element_by_xpath(save_editor_xpath):
                return False
            
            # 等待返回原页面
            time.sleep(2)
            self.switch_back_to_main_window()
            
            # 6. 保存整个页面
            save_page_xpath = '//*[@id="app"]/div[1]/main/div/div/div[3]/button[1]'
            if not self.click_element_by_xpath(save_page_xpath):
                return False
            
            print("落地页调整完成")
            return True
            
        except Exception as e:
            print(f"调整落地页过程中发生错误: {e}")
            return False
    
    def close(self) -> None:
        """
        关闭浏览器
        """
        if self.driver:
            self.driver.quit()
            print("浏览器已关闭")


def main():
    """
    主函数，处理命令行参数并执行自动化流程
    """
    parser = argparse.ArgumentParser(description='自动调整落地页参数工具')
    parser.add_argument('url', help='需要打开的网页URL')
    parser.add_argument('--condition', default='>5000,<10000', help='要设置的条件值，默认为">5000,<10000"')
    parser.add_argument('--headless', action='store_true', help='使用无头模式（不显示浏览器界面）')
    parser.add_argument('--timeout', type=int, default=30, help='等待元素的超时时间（秒），默认为30秒')
    
    args = parser.parse_args()
    
    adjuster = None
    try:
        # 创建并初始化自动化工具
        adjuster = LandingPageAdjuster(args.url, args.headless, args.timeout)
        
        # 执行自动化流程
        adjuster.open_page()
        success = adjuster.adjust_landing_page(args.condition)
        
        if success:
            print("自动化流程成功完成")
        else:
            print("自动化流程未能完成")
            
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 确保浏览器被关闭
        if adjuster:
            adjuster.close()


if __name__ == "__main__":
    main()

