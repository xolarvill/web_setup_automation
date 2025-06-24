from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import os
import json
import time
from typing import Optional
import glob

class ImageUploader:
    """
    图片上传工具类
    首次需要手动登陆，保存cookie后以后自动无头登陆
    """
    
    def __init__(self, cookie_path: str = "cookies.json"):
        """
        初始化上传器
        
        Args:
            cookie_path: cookie文件路径，默认为项目根目录下的cookies.json
        """
        self.login_url = "https://op.pacdora.com/login"
        self.upload_url = "https://op.pacdora.com/upload"
        self.timeout = 300
        self.target_url_contains = "dashboard"
        self.driver = None
        self.activated_status = False
        self.cookie_path = cookie_path
        self.cookie_status = None
    
    def activate(self):
        """
        激活浏览器，根据cookie状态决定是手动登录还是无头登录
        
        如果失败，返回Exception
        """
        try:
            if not self.activated_status:
                # 检查是否有cookies.json
                self.cookie_status = os.path.exists(self.cookie_path)
                
                # 根据cookie判断激活方式
                if self.cookie_status:
                    # 有cookie直接无头加载
                    self.activate_headless()
                else:
                    # 无cookie首次登陆并保存cookie
                    self.activate_manually()
                
                # 设置激活状态
                self.activated_status = True
            else:
                print("浏览器已激活，无需重复操作")
        except Exception as e:
            return e
    
    def activate_manually(self) -> None:
        """
        在log in界面手动登陆，保存cookie
        """
        chrome_options = Options()
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
                )

            # 打开登录页面进行手动登录
            self.driver.get(self.login_url)
            print(f"请在浏览器中手动登录，等待时间{self.timeout}秒")

            # 等待URL包含dashboard，表示登录成功
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    lambda d: self.target_url_contains in d.current_url
                )
                print("登录成功，检测到dashboard页面")
                
                # 保存cookies
                cookies = self.driver.get_cookies()
                with open(self.cookie_path, "w") as f:
                    json.dump(cookies, f)
                print(f"Cookie已保存至 {self.cookie_path}")
                
            except TimeoutException:
                print(f"登录超时，当前URL: {self.driver.current_url}")
                raise Exception("登录超时，请检查网络或登录信息")
            except Exception as e:
                print(f"登录过程中出现错误: {e}")
                print(f"当前URL: {self.driver.current_url}")
                raise
        except Exception as e:
            print(f"浏览器启动失败: {e}")
            raise
        finally:
            # 无论成功与否，都关闭浏览器
            if self.driver:
                self.driver.quit()
    
    def activate_headless(self) -> None:
        """
        读取cookie进行无头登陆
        """
        options = Options()
        options.add_argument("--headless=new")
        
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
                )
            
            # 先访问登录页面
            self.driver.get(self.login_url)
            
            # 读取并添加cookie
            try:
                with open(self.cookie_path, "r") as f:
                    cookies = json.load(f)
                    
                # 添加cookie前确保在正确的域名下
                for cookie in cookies:
                    # 移除不兼容的属性
                    if 'sameSite' in cookie:
                        cookie.pop('sameSite', None)
                    self.driver.add_cookie(cookie)
                
                # 刷新页面，应用cookie
                self.driver.refresh()
                
                # 等待页面加载完成
                WebDriverWait(self.driver, 10).until(
                    lambda d: self.target_url_contains in d.current_url
                )
                print("无头模式登录成功")
                
                # 验证是否成功登录
                try:
                    # 尝试查找上传页面的AWS选项元素，验证登录状态
                    self.driver.get(self.upload_url)
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, 
                            "//*[@id='app']/div/main/div/div/div/div/div[1]/div[1]/div/div/div[1]/div/div[3]"))
                    )
                    print("成功加载上传页面")
                except (NoSuchElementException, TimeoutException) as e:
                    print(f"无法找到上传页面元素，可能登录失败: {e}")
                    raise Exception("无头模式登录失败，请尝试手动登录")
                    
            except FileNotFoundError:
                print(f"Cookie文件不存在: {self.cookie_path}")
                raise
            except json.JSONDecodeError:
                print(f"Cookie文件格式错误: {self.cookie_path}")
                raise
            except Exception as e:
                print(f"加载Cookie过程中出错: {e}")
                raise
        except Exception as e:
            print(f"无头浏览器启动失败: {e}")
            if self.driver:
                self.driver.quit()
            self.driver = None
            raise
        
    
    def upload_and_get(self, file_path: str) -> str:
        """
        给定单个文件的绝对文件路径，上传获取cdn，并且刷新界面
        
        Args:
            file_path: 要上传的文件路径
            
        Returns:
            str: CDN链接
            
        Raises:
            FileNotFoundError: 文件不存在
            Exception: 上传失败或获取CDN链接失败
        """
        # 确保已激活
        if not self.activated_status or not self.driver:
            self.activate()
            
        # 确保在上传页面
        if self.upload_url not in self.driver.current_url:
            self.driver.get(self.upload_url)
            time.sleep(1)  # 等待页面加载
            
        try:
            # 选择AWS选项
            aws_option = self.driver.find_element(By.XPATH, "//*[@id='app']/div/main/div/div/div/div/div[1]/div[1]/div/div/div[1]/div/div[3]")
            aws_option.click()

            # 定位 <input type="file"> 元素
            file_input = self.driver.find_element(By.XPATH, '//input[starts-with(@accept, "*")]')

            # 确保文件路径是绝对路径
            abs_file_path = os.path.abspath(file_path)
            if not os.path.exists(abs_file_path):
                raise FileNotFoundError(f"文件不存在: {abs_file_path}")

            # 发送文件路径
            file_input.send_keys(abs_file_path)

            # 等待上传完成并获取 CDN 路径
            print(f"正在上传文件: {os.path.basename(abs_file_path)}...")

            # 使用更长的等待时间，确保文件完全上传
            try:
                # 首先等待元素出现
                print("等待CDN链接元素出现...")
                cdn_element = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div/main/div/div/div/div/div[2]/div[3]/div[2]'))
                )
                
                # 等待元素中出现文本（链接）
                print("等待CDN链接加载...")
                WebDriverWait(self.driver, 20).until(
                    lambda d: cdn_element.text.strip() != ""
                )
                
                # 获取CDN链接并刷新
                cdn_url = cdn_element.text.strip()
                print(f"成功获取CDN链接: {cdn_url}")
                self.driver.refresh()
                return cdn_url

            except TimeoutException as e:
                print(f"等待CDN链接超时: {e}")
                self._save_screenshot("cdn_timeout")
                raise Exception("获取CDN链接超时，请检查网络或上传状态")
            except Exception as e:
                print(f"获取CDN链接失败: {e}")
                self._save_screenshot("cdn_error")
                raise
        except NoSuchElementException as e:
            print(f"找不到页面元素: {e}")
            self._save_screenshot("element_not_found")
            raise
        except Exception as e:
            print(f"上传过程中出现错误: {e}")
            self._save_screenshot("upload_error")
            raise
        
    def upload_folder(self, folder_path: str) -> list:
        """
        给定一个文件夹，上传其中所有图片，将获取得到的cdn链接返回一个list。

        上传完一个图片后，出现cdn链接，此时获取并保存，然后直接发送新的文件路径到file_input中，获得新的cdn链接
        """

        # 支持的图片扩展名
        exts = ('*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.webp', '*.svg')
        files = []
        for ext in exts:
            files.extend(glob.glob(os.path.join(folder_path, ext)))
        files.sort()

        if not files:
            print(f"文件夹中没有图片: {folder_path}")
            return

        cdn_links = []
        failed_files = []

        for file_path in files:
            try:
                cdn_url = self.upload_and_get(file_path)
                cdn_links.append(f"{cdn_url}")
            except Exception as e:
                print(f"上传失败: {file_path}，错误: {e}")
                failed_files.append(file_path)
        
        return cdn_links
            
    def _save_screenshot(self, error_type: str) -> None:
        """
        保存当前页面截图
        
        Args:
            error_type: 错误类型，用于命名截图文件
        """
        if not self.driver:
            return
            
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"error_{error_type}_{timestamp}.png"
            screenshot_path = os.path.join(os.getcwd(), filename)
            self.driver.save_screenshot(screenshot_path)
            print(f"已保存截图: {screenshot_path}")
        except Exception as e:
            print(f"保存截图失败: {e}")
            
    def close(self) -> None:
        """
        关闭浏览器
        """
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.activated_status = False
            print("浏览器已关闭")
    
    def __enter__(self):
        self.activate()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def __del__(self) -> None:
        """
        析构函数，确保浏览器被关闭
        """
        self.close()
    
if __name__ == "__main__":
    # 创建上传器实例
    uploader = ImageUploader()

    # 激活浏览器（首次使用需手动登录）
    uploader.activate()
    print(uploader.activated_status)
    uploader.close()