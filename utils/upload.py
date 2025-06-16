from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class ImageUploader:
    def activate(self):
        """
        Initialize the Selenium WebDriver and navigate to the upload page.
        """
        self.driver = webdriver.Chrome()
        self.driver.get("https://op.pacdora.com/upload")
        
        # 选择“只传AWS”选项
        aws_option = self.driver.find_element(By.XPATH, """//input[@id="input-300"] '只传AWS')]""")
        aws_option.click()

    def upload_and_get(self, file_path):
        """
        Upload the image from the given file path and return the CDN link.
        """
        # 上传文件
        file_input = self.driver.find_element(By.XPATH, "//input[@id='input-304']") # '//*[@id="app"]/div[2]/main/div/div/div/div/div[1]/div[2]/div/div[1]'
        file_input.send_keys(file_path)

        # 等待上传完成并获取 CDN 路径
        time.sleep(2)  # 建议使用显式等待替代
        cdn_path_element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='col col-4']")) # '//*[@id="app"]/div[2]/main/div/div/div/div/div[2]/div[3]/div[2]'
        )
        cdn_path = cdn_path_element.get_attribute("href")

        return cdn_path

    def __del__(self):
        """
        Cleanup: Close the browser when the object is destroyed.
        """
        if hasattr(self, 'driver'):
            self.driver.quit()

# Example usage (uncomment to test)
if __name__ == "__main__":
    uploader = ImageUploader()
    uploader.activate()
    cdn_link = uploader.upload_and_get("C:/path/to/your/image.jpg")
    print(f"Uploaded CDN link: {cdn_link}")
    
    
# <div class="v-input theme--light v-text-field v-text-field--is-booted v-file-input"><div class="v-input__prepend-outer"><div class="v-input__icon v-input__icon--prepend"><button type="button" aria-label="prepend icon" class="v-icon notranslate v-icon--link mdi mdi-paperclip theme--light"></button></div></div><div class="v-input__control"><div class="v-input__slot"><div class="v-text-field__slot"><label for="input-304" class="v-label theme--light" style="left: 0px; right: auto; position: absolute;">选择文件</label><div class="v-file-input__text"></div><input accept="*" id="input-304" type="file"></div><div class="v-input__append-inner"><div></div></div></div><div class="v-text-field__details"><div class="v-messages theme--light"><div class="v-messages__wrapper"></div></div></div></div></div>

#//*[@id="app"]/div[2]/main/div/div/div/div/div[1]/div[2]/div

# 附件上传图标
#//*[@id="app"]/div[2]/main/div/div/div/div/div[1]/div[2]/div/div[1]

# 结果框
#//*[@id="app"]/div[2]/main/div/div/div/div/div[2]/div[3]/div[2]