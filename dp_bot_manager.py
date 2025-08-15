import time
import json
import csv
import pickle
from pathlib import Path
from DrissionPage import Chromium
from abc import ABC, abstractmethod
from typing import Callable, Literal, List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ProcessResult(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIP = "skip"
    MANUAL_REQUIRED = "manual_required"

@dataclass
class OperationConfig:
    """操作配置类"""
    login_url: str
    dashboard_url_contains: str
    operate_url: str
    operate_url_contains: str
    edit_url_contains: str
    timeout: int = 10
    checkpoint_file: str = 'cache/progress.pkl'
    cookie_file: str = 'cache/cookies.pkl'
    xpath_config_file: str = 'miscellaneous/web_ui_xpath.json'

# =========================== 策略接口 ===========================

class LoginStrategy(ABC):
    """登录策略接口"""
    
    @abstractmethod
    def execute_login(self, page, config: OperationConfig) -> bool:
        """执行登录"""
        pass

class NavigationStrategy(ABC):
    """导航策略接口"""
    
    @abstractmethod
    def navigate_to_target(self, page, config: OperationConfig) -> bool:
        """导航到目标页面"""
        pass

class SearchStrategy(ABC):
    """搜索策略接口"""
    
    @abstractmethod
    def search_target(self, page, target: str) -> int:
        """搜索目标，返回结果数量"""
        pass

class EditorStrategy(ABC):
    """编辑器策略接口"""
    
    @abstractmethod
    def open_editor(self, page, target: str) -> bool:
        """打开编辑器"""
        pass

class ProcessStrategy(ABC):
    """处理策略接口"""
    
    @abstractmethod
    def process_target(self, page, target: str, update_action: Callable[[str], str]) -> ProcessResult:
        """处理单个目标"""
        pass

# =========================== 具体策略实现 ===========================

class CookieLoginStrategy(LoginStrategy):
    """基于Cookie的登录策略"""
    
    def execute_login(self, page, config: OperationConfig) -> bool:
        print(f"🚀正在打开登录页面: {config.login_url}")
        page.get(config.login_url)
        
        # 尝试使用cookie登录
        if self._load_cookies(page, config.cookie_file):
            print("🍪正在尝试使用已保存的cookie登录...")
            page.refresh()
            
            if page.wait.url_change(config.dashboard_url_contains, timeout=5):
                print("  ✔️ 使用cookie登录成功")
                return True
        
        print("🚩未找到有效cookie或cookie已过期，请手动登录...")
        if page.wait.url_change(config.dashboard_url_contains, timeout=config.timeout * 50):
            print("  ✔️ 手动登录成功")
            self._save_cookies(page, config.cookie_file)
            return True
        else:
            print("    ❌登录失败或超时")
            return False
    
    def _load_cookies(self, page, cookie_file: str) -> bool:
        if Path(cookie_file).exists():
            try:
                with open(cookie_file, 'rb') as f:
                    cookies = pickle.load(f)
                for cookie in cookies:
                    page.set.cookies(cookie)
                return True
            except Exception as e:
                print(f"    ❌加载cookie失败: {e}")
        return False
    
    def _save_cookies(self, page, cookie_file: str):
        try:
            cookies = page.cookies()
            Path(cookie_file).parent.mkdir(exist_ok=True)
            with open(cookie_file, 'wb') as f:
                pickle.dump(cookies, f)
            print("  ✔️ 已保存cookie供下次使用")
        except Exception as e:
            print(f"    ❌保存cookie失败: {e}")

class StandardNavigationStrategy(NavigationStrategy):
    """标准导航策略"""
    
    def __init__(self, language: str):
        self.language = language
    
    def navigate_to_target(self, page, config: OperationConfig) -> bool:
        print(f"🚩正在跳转到操作页面: {config.operate_url}")
        page.get(config.operate_url)
        
        if page.wait.url_change(config.operate_url_contains, timeout=config.timeout):
            print("  ✔️ 成功跳转到操作页面")
            return self._switch_language(page)
        return False
    
    def _switch_language(self, page) -> bool:
        try:
            language_setting = page.ele(self.language)
            if language_setting:
                print(f"  ✔️ 成功识别到{self.language}")
                return True
            else:
                default_language = page.ele('英语')
                if default_language:
                    default_language.click()
                to_language = page.ele(self.language)
                if to_language:
                    to_language.click()
                    print(f"  ✔️ 成功切换到{self.language}")
                    return True
        except Exception as e:
            print(f"切换语言失败: {e}")
        return False

class FlexibleSearchStrategy(SearchStrategy):
    """灵活的搜索策略"""
    
    def search_target(self, page, target: str) -> int:
        try:
            search_input = self._find_search_input(page)
            tr_elements_before = page.eles("tag:tr")
            
            if search_input:
                if self._input_text_to_search(page, search_input, target):
                    print(f"  ✔️ 成功输入搜索目标: {target}")
                else:
                    return 0
                
                time.sleep(1.5)
                page.actions.key_down('Enter').key_up('Enter')
                
                # 等待搜索结果
                max_wait = 30
                for i in range(max_wait):
                    tr_elements = page.eles("tag:tr")
                    if (len(tr_elements) != len(tr_elements_before) and 
                        len(tr_elements) not in [0, 11]):
                        break
                    time.sleep(1)
                else:
                    tr_elements = page.eles("tag:tr")
                
                result_count = len(tr_elements)
                print(f"🚩搜索结果数量: {result_count-1}")
                return result_count
        except Exception as e:
            print(f"    ❌搜索目标失败: {e}")
        return 0
    
    def _find_search_input(self, page):
        """多种方式定位搜索输入框"""
        strategies = [
            lambda: self._find_by_label(page),
            lambda: page.ele('.v-text-field__slot input'),
            lambda: page.ele('tag:input@type=text'),
            lambda: self._click_by_coordinates(page)
        ]
        
        for strategy in strategies:
            try:
                result = strategy()
                if result:
                    return result
            except Exception:
                continue
        return None
    
    def _find_by_label(self, page):
        label = page.ele('text:专题页路径')
        if label:
            input_id = label.attr('for')
            if input_id:
                return page.ele(f'#{input_id}')
        return None
    
    def _click_by_coordinates(self, page):
        print("⚠️使用坐标点击方法")
        return "coordinate_click"
    
    def _input_text_to_search(self, page, search_input, text):
        try:
            if search_input == "coordinate_click":
                page.key('ctrl+a')
                time.sleep(0.1)
                page.key('Delete')
                time.sleep(0.1)
                page.key(text)
                return True
            else:
                search_input.clear()
                search_input.input(text)
                return True
        except Exception as e:
            print(f"输入文本失败: {e}")
            return False

class StandardEditorStrategy(EditorStrategy):
    """标准编辑器策略"""
    
    def open_editor(self, page, target: str) -> bool:
        try:
            edit_button = page.ele('@class=table-td', -1)
            if not edit_button:
                return False
            
            edit_button.click()
            print("🚩正在打开编辑页")
            
            edit_option = page.ele("@role=option", -3)
            if not edit_option:
                return False
            
            edit_option.click()
            time.sleep(2)
            return True
        except Exception as e:
            print(f"    ❌打开编辑页失败: {e}")
            return False

class JsonProcessStrategy(ProcessStrategy):
    """JSON处理策略"""
    
    def process_target(self, page, target: str, update_action: Callable[[str], str]) -> ProcessResult:
        try:
            import pyperclip
            
            # 等待页面加载
            page.wait.load_start()
            
            # 打开可视化编辑器
            open_editor_button = page.ele('编辑值')
            if not open_editor_button:
                return ProcessResult.FAILED
            
            open_editor_button.click()
            time.sleep(1.5)
            
            # 获取编辑器页面
            browser = page.browser
            editor_tab = browser.latest_tab
            editor_tab.set.activate()
            
            # 点击JSON工具按钮
            json_tool_button = editor_tab.ele("@@type=button@@class^el-button")
            if not json_tool_button:
                return ProcessResult.FAILED
            
            json_tool_button.click(by_js=True)
            time.sleep(1)
            
            # 获取JSON
            get_json_button = editor_tab.ele("获取当前JSON")
            if not get_json_button:
                return ProcessResult.FAILED
            
            get_json_button.click()
            time.sleep(1)
            
            # 处理JSON
            json_str = pyperclip.paste()
            replaced_str = update_action(json_str)
            
            # 输入处理后的JSON
            json_input = editor_tab.ele("@class=app-writer")
            if not json_input:
                return ProcessResult.FAILED
            
            json_input.click()
            json_input.input(replaced_str)
            
            # 保存JSON
            save_json_button = editor_tab.ele("确定")
            if save_json_button:
                save_json_button.click()
                time.sleep(1)
            
            # 保存编辑器
            save_editor_button = editor_tab.ele("@@type=button@@class^el-button", index=8)
            if save_editor_button:
                save_editor_button.click()
                time.sleep(5)
            
            # 最终保存
            edit_page = browser.get_tab(1)
            final_save_button = edit_page.ele('保存')
            if final_save_button:
                final_save_button.click()
                if edit_page.wait.url_change('https://op.pacdora.com/topic/List', timeout=60):
                    return ProcessResult.SUCCESS
            
            return ProcessResult.FAILED
            
        except Exception as e:
            print(f"    ❌处理目标失败: {e}")
            return ProcessResult.FAILED

# =========================== 主框架 ===========================

class ModularBatchBot:
    """模块化批量处理机器人"""
    
    def __init__(self, 
                 config: OperationConfig,
                 login_strategy: LoginStrategy,
                 navigation_strategy: NavigationStrategy,
                 search_strategy: SearchStrategy,
                 editor_strategy: EditorStrategy,
                 process_strategy: ProcessStrategy,
                 update_action: Callable[[str], str],
                 target_list: Optional[List[str]] = None,
                 target_csv_path: Optional[str] = None):
        
        if target_list is None and target_csv_path is None:
            raise ValueError("Either 'target_list' or 'target_csv_path' must be provided")
        if target_list is not None and target_csv_path is not None:
            raise ValueError("Only one of 'target_list' or 'target_csv_path' should be provided")
        
        self.config = config
        self.login_strategy = login_strategy
        self.navigation_strategy = navigation_strategy
        self.search_strategy = search_strategy
        self.editor_strategy = editor_strategy
        self.process_strategy = process_strategy
        self.update_action = update_action
        self.target_list = target_list
        self.target_csv_path = target_csv_path
        
        self.browser = Chromium()
    
    def run(self):
        """主运行流程 - 模板方法"""
        try:
            # 1. 准备目标列表
            all_targets = self._prepare_targets()
            if not all_targets:
                print("    ❌未找到任何目标")
                return
            
            # 2. 加载进度
            completed_targets = self._load_progress()
            remaining_targets = [t for t in all_targets if t not in completed_targets]
            
            print(f"🔄总目标数: {len(all_targets)}, 已完成: {len(completed_targets)}, 剩余: {len(remaining_targets)}")
            
            # 3. 登录
            if not self._execute_login():
                return
            
            # 4. 导航到操作页面
            if not self._execute_navigation():
                return
            
            # 5. 批量处理目标
            self._process_targets(remaining_targets, all_targets, completed_targets)
            
        except Exception as e:
            print(f"    ❌程序运行出错: {e}")
        finally:
            if hasattr(self.browser, 'quit'):
                self.browser.quit()
    
    def _prepare_targets(self) -> List[str]:
        """准备目标列表"""
        if self.target_list:
            return self.target_list
        elif self.target_csv_path:
            return self._read_csv_to_list(self.target_csv_path)
        return []
    
    def _read_csv_to_list(self, csv_path: str) -> List[str]:
        """读取CSV文件"""
        targets = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        targets.append(row[0])
        except Exception as e:
            print(f"    ❌读取CSV文件出错: {e}")
        return targets
    
    def _load_progress(self) -> List[str]:
        """加载进度"""
        if Path(self.config.checkpoint_file).exists():
            try:
                with open(self.config.checkpoint_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"    ❌加载进度失败: {e}")
        return []
    
    def _save_progress(self, completed_targets: List[str]):
        """保存进度"""
        try:
            Path(self.config.checkpoint_file).parent.mkdir(exist_ok=True)
            with open(self.config.checkpoint_file, 'wb') as f:
                pickle.dump(completed_targets, f)
        except Exception as e:
            print(f"    ❌保存进度失败: {e}")
    
    def _execute_login(self) -> bool:
        """执行登录"""
        return self.login_strategy.execute_login(self.browser.latest_tab, self.config)
    
    def _execute_navigation(self) -> bool:
        """执行导航"""
        return self.navigation_strategy.navigate_to_target(self.browser.latest_tab, self.config)
    
    def _process_targets(self, remaining_targets: List[str], all_targets: List[str], completed_targets: List[str]):
        """批量处理目标"""
        for i, target in enumerate(remaining_targets):
            try:
                current_progress = len(all_targets) - len(remaining_targets) + i + 1
                print(f"🚩正在处理: {target} (进度: {current_progress}/{len(all_targets)})")
                
                # 搜索目标
                result_count = self.search_strategy.search_target(self.browser.latest_tab, target)
                
                if result_count == 0:
                    print(f"  ❌{target}未找到搜索结果")
                    continue
                elif result_count >= 3:
                    print(f"  ⚠️{target}有多个搜索结果")
                    manual_confirm = input("❓是否继续处理此目标？(y/n): ")
                    if manual_confirm.lower() != 'y':
                        continue
                elif result_count == 2:
                    print("  ✔️ 定位成功")
                    if not self.editor_strategy.open_editor(self.browser.latest_tab, target):
                        continue
                
                # 处理目标
                result = self.process_strategy.process_target(
                    self.browser.latest_tab, target, self.update_action
                )
                
                if result == ProcessResult.SUCCESS:
                    print(f"✅ {target}已成功更新")
                    completed_targets.append(target)
                    self._save_progress(completed_targets)
                else:
                    print(f"    ❌{target}处理失败")
                
                print('='*50)
                
            except Exception as e:
                print(f"    ❌处理{target}时发生错误: {e}")
                self._save_progress(completed_targets)
                break

# =========================== 工厂方法 ===========================

class BotFactory:
    """机器人工厂"""
    
    @staticmethod
    def create_pacdora_json_bot(language: str, update_action: Callable[[str], str], 
                               target_list: Optional[List[str]] = None,
                               target_csv_path: Optional[str] = None) -> ModularBatchBot:
        """创建Pacdora JSON处理机器人"""
        
        config = OperationConfig(
            login_url="https://op.pacdora.com/login",
            dashboard_url_contains="dashboard",
            operate_url="https://op.pacdora.com/topic/List",
            operate_url_contains="List",
            edit_url_contains="edit"
        )
        
        return ModularBatchBot(
            config=config,
            login_strategy=CookieLoginStrategy(),
            navigation_strategy=StandardNavigationStrategy(language),
            search_strategy=FlexibleSearchStrategy(),
            editor_strategy=StandardEditorStrategy(),
            process_strategy=JsonProcessStrategy(),
            update_action=update_action,
            target_list=target_list,
            target_csv_path=target_csv_path
        )
    
    @staticmethod
    def create_custom_bot(config: OperationConfig,
                         login_strategy: LoginStrategy,
                         navigation_strategy: NavigationStrategy,
                         search_strategy: SearchStrategy,
                         editor_strategy: EditorStrategy,
                         process_strategy: ProcessStrategy,
                         update_action: Callable[[str], str],
                         **kwargs) -> ModularBatchBot:
        """创建自定义机器人"""
        return ModularBatchBot(
            config=config,
            login_strategy=login_strategy,
            navigation_strategy=navigation_strategy,
            search_strategy=search_strategy,
            editor_strategy=editor_strategy,
            process_strategy=process_strategy,
            update_action=update_action,
            **kwargs
        )

# =========================== 使用示例 ===========================

def example_usage():
    """使用示例"""
    
    # 方式1: 使用工厂方法创建现有类型的机器人
    def dummy_update_action(json_str: str) -> str:
        return json_str  # 这里放你的更新逻辑
    
    bot = BotFactory.create_pacdora_json_bot(
        language='英语',
        update_action=dummy_update_action,
        target_csv_path='mockup_faq_content.csv'
    )
    
    # 方式2: 创建全新类型的机器人
    # 只需要实现对应的策略类，然后组合即可
    
    # bot.run()

if __name__ == "__main__":
    example_usage()