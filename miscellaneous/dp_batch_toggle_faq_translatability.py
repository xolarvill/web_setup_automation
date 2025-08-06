import time
import json
import csv
import pickle
from pathlib import Path
from DrissionPage import Chromium
import pyperclip


class FAQTranslationToggleBot:
    """
    使用DrissionPage批量切换FAQ翻译状态的自动化机器人
    自动化程度：全自动 + 人工监督分岔节点
    """
    
    def __init__(self):
        self.login_url = "https://op.pacdora.com/login"
        self.dashboard_url_contains = "dashboard"
        self.operate_url = "https://op.pacdora.com/topic/List"
        self.operate_url_contains = "List"
        self.edit_url_contains = "edit"
        self.timeout = 10  # 优化超时时间
        self.checkpoint_file = 'faq_progress.pkl'
        self.cookie_file = 'cookies.pkl'
        
        # 加载XPath配置
        with open('miscellaneous/web_ui_xpath.json', 'r', encoding='utf-8') as f:
            self.xpath = json.load(f)
        
        # 初始化浏览器
        self.browser = Chromium()
        
    def update_json(self, json_str: str) -> str:
        """更新JSON字符串中的翻译状态"""
        target = '"text":"FAQ","tag":"h2","isNeedTranslate":false,'
        to_target = '"text":"FAQ","tag":"h2","isNeedTranslate":true,'
        return json_str.replace(target, to_target)
    
    def read_csv_to_list(self, csv_path: str) -> list:
        """读取CSV文件的第一列内容"""
        targets = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:  # 确保行不为空
                        targets.append(row[0])
        except FileNotFoundError:
            print(f"    ❌文件 {csv_path} 不存在")
            return []
        except Exception as e:
            print(f"    ❌读取CSV文件出错: {e}")
            return []
        return targets
    
    def save_progress(self, completed_targets: list):
        """保存进度到断点文件"""
        try:
            with open(self.checkpoint_file, 'wb') as f:
                pickle.dump(completed_targets, f)
            print(f"  ✔️ 进度已保存到 {self.checkpoint_file}")
        except Exception as e:
            print(f"    ❌保存进度失败: {e}")
    
    def _find_search_input(self, page):
        """尝试多种方式定位搜索输入框"""
        # 方法1: 通过label文本定位（推荐）
        try:
            # 查找包含"专题页路径"文本的label
            label = page.ele('text:专题页路径')
            if label:
                # 获取label的for属性值
                input_id = label.attr('for')
                if input_id:
                    # 通过ID定位input
                    search_input = page.ele(f'#{input_id}')
                    if search_input:
                        print("  ✔️ 通过label定位到搜索输入框")
                        return search_input
        except Exception as e:
            print(f"通过label定位失败: {e}")
        
        # 方法2: 直接通过CSS类名定位input
        try:
            search_input = page.ele('.v-text-field__slot input')
            if search_input:
                print("  ✔️ 通过CSS类名定位到搜索输入框")
                return search_input
        except Exception as e:
            print(f"通过CSS类名定位失败: {e}")
            
        # 方法3: 通过input的type属性定位
        try:
            search_input = page.ele('tag:input@type=text')
            if search_input:
                print("  ✔️ 通过input type定位到搜索输入框")
                return search_input
        except Exception as e:
            print(f"通过input type定位失败: {e}")
        
        # 方法4: 坐标点击方法（备用）
        print("⚠️常规定位方法失败，尝试使用坐标点击")
        return self._click_search_input_by_coordinates(page)
    
    def _input_text_to_search(self, page, search_input, text):
        """向搜索框输入文本"""
        try:
            if search_input == "coordinate_click":
                # 如果是坐标点击的情况，直接输入文本
                print(f"📝使用键盘输入: {text}")
                # 先清空可能存在的文本 (Ctrl+A + Delete)
                page.key('ctrl+a')
                time.sleep(0.1)
                page.key('Delete')
                time.sleep(0.1)
                # 输入新文本
                page.key(text)
                return True
            else:
                # 常规方式
                search_input.clear()
                search_input.input(text)
                return True
        except Exception as e:
            print(f"输入文本失败: {e}")
            return False
    
    def load_progress(self) -> list:
        """从断点文件加载进度"""
        if Path(self.checkpoint_file).exists():
            try:
                with open(self.checkpoint_file, 'rb') as f:
                    completed_targets = pickle.load(f)
                print(f"  ✔️ 已从 {self.checkpoint_file} 加载进度，已完成 {len(completed_targets)} 个目标")
                return completed_targets
            except Exception as e:
                print(f"    ❌加载进度文件失败: {e}")
                return []
        else:
            print("⚠️未找到断点文件，将从头开始处理")
            return []
    
    def save_cookies(self, page):
        """保存cookies到文件"""
        try:
            cookies = page.cookies()
            with open(self.cookie_file, 'wb') as f:
                pickle.dump(cookies, f)
            print("  ✔️ 已保存cookie供下次使用")
        except Exception as e:
            print(f"    ❌保存cookie失败: {e}")
    
    def load_cookies(self, page) -> bool:
        """加载cookies进行自动登录"""
        if Path(self.cookie_file).exists():
            try:
                with open(self.cookie_file, 'rb') as f:
                    cookies = pickle.load(f)
                for cookie in cookies:
                    page.set.cookies(cookie)
                return True
            except Exception as e:
                print(f"    ❌加载cookie失败: {e}")
                return False
        return False
    
    def login(self) -> bool:
        """执行登录流程"""
        print(f"🚀正在打开登录页面: {self.login_url}")
        page = self.browser.latest_tab
        page.get(self.login_url)
        
        # 尝试使用cookie登录
        if self.load_cookies(page):
            print("🍪正在尝试使用已保存的cookie登录...")
            page.refresh()
            
            # 检查是否成功登录
            if page.wait.url_change(self.dashboard_url_contains, timeout=5):
                print("  ✔️ 使用cookie登录成功")
                return True
        
        print("🚩未找到有效cookie或cookie已过期，请手动登录...")
        # 等待手动登录完成
        if page.wait.url_change(self.dashboard_url_contains, timeout=self.timeout * 50):
            print("  ✔️ 手动登录成功")
            self.save_cookies(page)
            return True
        else:
            print("    ❌登录失败或超时")
            return False
    
    def navigate_to_operate_page(self) -> bool:
        """跳转到操作页面"""
        print(f"🚩正在跳转到操作页面: {self.operate_url}")
        page = self.browser.latest_tab
        page.get(self.operate_url)
        
        if page.wait.url_change(self.operate_url_contains, timeout=self.timeout):
            print("  ✔️ 成功跳转到操作页面")
            return True
        else:
            print("    ❌跳转到操作页面失败")
            return False
    
    def search_target(self, target: str) -> int:
        """搜索目标并返回tr-elements结果数量"""
        try:
            page = self.browser.latest_tab
            # 清空搜索框并输入目标
            search_input = self._find_search_input(page)
            
            tr_elements_before = page.eles("tag:tr")
            
            if search_input:
                # 使用专门的输入方法
                if self._input_text_to_search(page, search_input, target):
                    print(f"  ✔️ 成功输入搜索目标: {target}")
                else:
                    print(f"    ❌输入搜索目标失败: {target}")
                    return 0
                
                time.sleep(1.5)
                
                page.actions.key_down('Enter').key_up('Enter')
                
                # 等待搜索结果加载：每隔一秒检查tr元素数量是否变化，最多等待30秒
                max_wait = 30
                for i in range(max_wait):
                    tr_elements = page.eles("tag:tr")
                    if len(tr_elements) != len(tr_elements_before) and len(tr_elements) != 0 and len(tr_elements) != 11:
                        break
                    time.sleep(1)
                else:
                    # 超时未检测到变化
                    tr_elements = page.eles("tag:tr")
                
                # 检查搜索结果
                print(f"🚩搜索结果数量: {len(tr_elements)-1}")
                return len(tr_elements)
                
        except Exception as e:
            print(f"    ❌搜索目标失败: {e}")
        return 0
    
    def open_editor(self) -> bool:
        '''当搜索出单个结果后，点击编辑进入编辑页'''
        try:
            page = self.browser.latest_tab
            edit_button = page.ele('@class=table-td',-1)
            if not edit_button:
                print("    ❌未找到编辑按钮")
                return False
            
            edit_button.click()
            print("🚩正在打开编辑页")
            edit_option = page.ele("@role=option",-3)
            if not edit_option:
                print("    ❌未找到编辑选项")
                return False
            
            edit_option.click()
            time.sleep(2)  # 等待页面跳转
            return True
        except Exception as e:
            print(f"    ❌打开编辑页失败: {e}")
            return False
    
    def process_single_target(self, target: str) -> bool:
        """处理单个目标"""
        try:
            # 获取最新的tab页（编辑页）
            page = self.browser.latest_tab
            page.wait.load_start()  # 等待页面开始加载
            
            # 打开可视化编辑器
            open_pop_up_editor_button = page.ele('编辑值')
            if not open_pop_up_editor_button:
                print("    ❌未找到打开可视化编辑器按钮")
                return False
            
            open_pop_up_editor_button.click()
            
            time.sleep(1.5)  # 等待新tab打开
            
            # 获取最新的tab（可视化编辑器页面）
            editor_tab = self.browser.latest_tab
            editor_tab.set.activate()
            print("  ✔️ 成功打开可视化编辑器")
            
            # 点击JSON工具按钮
            json_tool_button = editor_tab.ele("@@type=button@@class^el-button")
            
            if json_tool_button:
                try:
                    json_tool_button.click(by_js=True)
                    time.sleep(1)
                except Exception as e:
                    print(f"点击JSON工具按钮失败: {e}")
                    return False
                
                get_json_button = editor_tab.ele("获取当前JSON")
                if get_json_button:
                    get_json_button.click()
                    print("  ✔️ 成功获取json")
                    
                    # 获取剪贴板内容并替换
                    time.sleep(1)  # 等待复制完成
                    json_str = pyperclip.paste()
                    replaced_str = self.update_json(json_str)
                    print("  ✔️ 成功替换json")
                    
                    # 输入替换后的JSON
                    json_input = editor_tab.ele("@class=app-writer")
                    if json_input:
                        json_input.click()
                        json_input.input(replaced_str)
                        
                        # 保存JSON输入
                        json_input_save_button = editor_tab.ele("确定")
                        if json_input_save_button:
                            json_input_save_button.click()
                            time.sleep(1)
                            
                            # 保存可视化编辑器
                            save_pop_up_editor_button = editor_tab.ele("@@type=button@@class^el-button",index=8)
                            if save_pop_up_editor_button:
                                save_pop_up_editor_button.click()
                                print("  ✔️ 成功保存json")
                                
                                # 等待标签页关闭
                                time.sleep(5)
                                
                                # 切换回编辑页标签页
                                edit_page = self.browser.get_tab(1)
                                    
                                # 最终保存
                                final_save_button = edit_page.ele('保存')
                                if final_save_button:
                                    final_save_button.click()
                                    print("🚩正在保存编辑页...")
                                        
                                    # 等待返回列表页
                                    if edit_page.wait.url_change('https://op.pacdora.com/topic/List',timeout=60):
                                        print("  ✔️ 成功保存编辑页")
                                        return True
            
            return False
            
        except Exception as e:
            print(f"    ❌处理目标失败: {e}")
            return False
    
    def run(self):
        """主运行方法"""
        try:
            # 读取所有目标
            all_targets = self.read_csv_to_list('mockup_faq_content.csv')
            if not all_targets:
                print("    ❌未找到任何目标")
                return
            
            # 加载进度
            completed_targets = self.load_progress()
            remaining_targets = [target for target in all_targets if target not in completed_targets]
            
            print(f"🔄总目标数: {len(all_targets)}, 已完成: {len(completed_targets)}, 剩余: {len(remaining_targets)}")
            
            # 登录
            if not self.login():
                return
            
            # 跳转到操作页面
            if not self.navigate_to_operate_page():
                return
            
            # 处理剩余目标
            for i, target in enumerate(remaining_targets):
                try:
                    current_progress = len(all_targets) - len(remaining_targets) + i + 1
                    print(f"🚩正在处理: {target} (进度: {current_progress}/{len(all_targets)})")
                    
                    # 搜索目标
                    result_count = self.search_target(target)
                    
                    if result_count == 0:
                        print(f"  ❌{target}未找到搜索结果")
                        continue
                    elif result_count >= 3:
                        print(f"  ⚠️{target}有多个搜索结果，请手动处理")
                        manual_confirm = input("❓是否继续处理此目标？(y/n): ")
                        if manual_confirm.lower() != 'y':
                            continue
                        
                    elif result_count == 2:
                        print("  ✔️ 定位成功")
                        if not self.open_editor():
                            continue
                    
                    # 处理目标
                    if self.process_single_target(target):
                        print(f"✅ {target}已成功更新")
                        completed_targets.append(target)
                        self.save_progress(completed_targets)
                    else:
                        print(f"    ❌{target}处理失败")
                    
                    print('='*50)
                        
                except Exception as e:
                    print(f"    ❌处理{target}时发生错误: {e}")
                    print("⚠️程序中断，已保存当前进度")
                    self.save_progress(completed_targets)
                    break
            
            # 完成处理
            if not remaining_targets:
                print("  ✔️ 没有需要处理的目标，所有任务已完成")
            else:
                print("  ✔️ 所有剩余目标已处理完成！")
                print(f"📊总共处理了 {len(completed_targets)}/{len(all_targets)} 个目标")
                
        except Exception as e:
            print(f"    ❌程序运行出错: {e}")
        finally:
            # 关闭浏览器
            if hasattr(self.browser, 'quit'):
                self.browser.quit()


def main():
    """主函数"""
    bot = FAQTranslationToggleBot()
    bot.run()


if __name__ == "__main__":
    main()