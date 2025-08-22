import time
import json
import csv
import pickle
import random
from pathlib import Path
from DrissionPage import Chromium
from abc import ABC, abstractmethod
from typing import Callable, Literal, List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from utils.resource_manager import get_writable_path

# =========================== 日志接口 ===========================

# 定义一个可被外部设置的日志回调函数
_log_callback = None

def log(msg: str, level: str = "info"):
    """统一日志接口：同时输出到终端和 GUI（如果注册了回调）"""
    print(f"[BOT] {msg}")  # 保留终端输出用于调试. 注意：这里必须用 print，不能用 log，否则无限递归！
    
    if _log_callback:
        _log_callback(msg, level)  # 调用 GUI 的 add_output_message

def set_log_callback(callback):
    """
    设置日志回调函数
    :param callback: func(message: str, level: str)
    """
    global _log_callback
    _log_callback = callback
        
        
# =========================== 基础定义 ===========================

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
    timeout: int = 20
    checkpoint_file: str = 'cache/progress.pkl'
    cookie_file: str = 'cache/cookies.pkl'
    xpath_config_file: str = 'miscellaneous/web_ui_xpath.json'

# =========================== 策略接口 ===========================

class LoginStrategy(ABC):
    """登录策略接口"""
    
    @abstractmethod
    def execute_login(self, page, config: OperationConfig) -> bool:
        """执行登录"""
        raise NotImplementedError("必须实现登录方法")

class NavigationStrategy(ABC):
    """导航策略接口"""
    
    @abstractmethod
    def navigate_to_target(self, page, config: OperationConfig) -> bool:
        """导航到目标页面"""
        raise NotImplementedError("必须实现导航方法")

class SearchStrategy(ABC):
    """搜索策略接口"""
    
    @abstractmethod
    def search_target(self, page, target: str) -> int:
        """搜索目标，返回结果数量"""
        raise NotImplementedError("必须实现搜索方法")
    
class InteractionStrategy(ABC):
    """交互策略接口，用于处理需要用户确认的场景"""
    
    @abstractmethod
    def request_confirmation(self, message: str, on_confirm: Callable[[bool], None]):
        """
        请求用户确认
        :param message: 提示信息
        :param on_confirm: 回调函数，传入 True 表示继续，False 表示跳过
        """
        raise NotImplementedError

class EditorStrategy(ABC):
    """编辑器策略接口"""
    
    @abstractmethod
    def open_editor(self, page, target: str) -> bool:
        """打开编辑器"""
        raise NotImplementedError("必须实现编辑方法")

class ProcessStrategy(ABC):
    """处理策略接口"""
    
    @abstractmethod
    def process_target(self, page, target: str, update_action: Callable[[str], str]) -> ProcessResult:
        """处理单个目标"""
        raise NotImplementedError("必须实现处理方法")

# =========================== 具体策略实现 ===========================

class CookieLoginStrategy(LoginStrategy):
    """
    基于Cookie的登录策略
    使用pickle保存信息到cache中
    """
    
    def execute_login(self, page, config: OperationConfig) -> bool:
        from utils.resource_manager import get_writable_path
        log(f"🚀正在打开登录页面: {config.login_url}")
        page.get(config.login_url)

        # 尝试使用cookie登录
        if self._load_cookies(page, config.cookie_file):
            log("🍪正在尝试使用已保存的cookie登录...")
            page.refresh()

            if page.wait.url_change(config.dashboard_url_contains, timeout=5):
                log("  ✔️ 使用cookie登录成功")
                return True

        log("🚩未找到有效cookie或cookie已过期，请手动登录...")
        if page.wait.url_change(config.dashboard_url_contains, timeout=config.timeout * 50):
            log("  ✔️ 手动登录成功")
            self._save_cookies(page, config.cookie_file)
            return True
        else:
            log("    ❌登录失败或超时")
            return False

    def _load_cookies(self, page, cookie_file: str) -> bool:
        abs_cookie_file = get_writable_path(cookie_file)
        path = Path(abs_cookie_file)

        # ✅ 确保父目录存在（即使不读也要准备写）
        path.parent.mkdir(parents=True, exist_ok=True)

        if not path.exists():
            log(f"    🟡 cookie 文件不存在，将进行手动登录: {abs_cookie_file}")
            return False

        try:
            with open(path, 'rb') as f:
                cookies = pickle.load(f)
            log(f"✅ 成功加载 {len(cookies)} 个 cookies")
            for cookie in cookies:
                page.set.cookies(cookie)
            return True
        except EOFError:
            log("    ❌ cookies.pkl 文件为空或损坏，建议删除后重新登录")
            return False
        except Exception as e:
            log(f"    ❌ 加载 cookie 失败: {type(e).__name__}: {e}")
            return False

    def _save_cookies(self, page, cookie_file: str):
        abs_cookie_file = get_writable_path(cookie_file)
        path = Path(abs_cookie_file)
        path.parent.mkdir(parents=True, exist_ok=True)  # ✅ 确保 cache 目录被创建

        try:
            cookies = page.cookies()
            with open(abs_cookie_file, 'wb') as f:
                pickle.dump(cookies, f)
            log(f"  ✔️ 已保存 cookie 到: {abs_cookie_file}")
        except Exception as e:
            log(f"    ❌保存cookie失败: {e}")

class StandardNavigationStrategy(NavigationStrategy):
    """标准导航策略"""
    
    def __init__(self, language: str):
        self.language = language
    
    def navigate_to_target(self, page, config: OperationConfig) -> bool:
        log(f"🚩正在跳转到操作页面: {config.operate_url}")
        page.get(config.operate_url)
        
        if page.wait.url_change(config.operate_url_contains, timeout=config.timeout):
            log("  ✔️ 成功跳转到操作页面")
            return self._switch_language(page)
        return False
    
    def _switch_language(self, page) -> bool:
        try:
            language_setting = page.ele(self.language)
            if language_setting:
                log(f"  ✔️ 成功识别到{self.language}")
                return True
            else:
                default_language = page.ele('英语')
                if default_language:
                    default_language.click()
                to_language = page.ele(self.language)
                if to_language:
                    to_language.click()
                    log(f"  ✔️ 成功切换到{self.language}")
                    return True
        except Exception as e:
            log(f"切换语言失败: {e}")
        return False

class FlexibleSearchStrategy(SearchStrategy):
    """灵活的搜索策略"""
    
    def search_target(self, page, target: str) -> int:
        try:
            search_input = self._find_search_input(page)
            tr_elements_before = page.eles("tag:tr")
            
            if search_input:
                if self._input_text_to_search(page, search_input, target):
                    log(f"  ✔️ 成功输入搜索目标: {target}")
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
                log(f"🚩搜索结果数量: {result_count-1}")
                return result_count
        except Exception as e:
            log(f"    ❌搜索目标失败: {e}")
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
        log("⚠️使用坐标点击方法")
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
            log(f"输入文本失败: {e}")
            return False

class ConsoleInteractionHandler(InteractionStrategy):
    """控制台交互处理器（默认）"""
    
    def request_confirmation(self, message: str, on_confirm: Callable[[bool], None]):
        try:
            choice = input(f"{message} (y/n): ").strip().lower()
            on_confirm(choice in ['y', 'yes', '是'])
        except:
            on_confirm(False)

class GuiInteractionHandler(InteractionStrategy):
    """
    GUI 交互处理器
    与 PySide6 界面通信，通过按钮触发继续
    """
    
    def __init__(self):
        self._on_confirm: Optional[Callable[[bool], None]] = None
        self._is_waiting = False
    
    def is_waiting_for_input(self) -> bool:
        return self._is_waiting

    def request_confirmation(self, message: str, on_confirm: Callable[[bool], None]):
        self._on_confirm = on_confirm
        self._is_waiting = True
        # 通过信号通知 GUI 显示提示（可选）
        log(f"⏸️ GUI 交互请求: {message}")
        # 实际行为由 GUI 按钮触发 continue_action
    
    def continue_action(self, confirmed: bool = True):
        """由 GUI 按钮调用，恢复任务"""
        if not self._is_waiting or not self._on_confirm:
            return
        
        self._on_confirm(confirmed)
        self._on_confirm = None
        self._is_waiting = False

class StandardEditorStrategy(EditorStrategy):
    """标准编辑器策略"""
    
    def open_editor(self, page, target: str) -> bool:
        try:
            edit_button = page.ele('@class=table-td', -1)
            if not edit_button:
                return False
            
            edit_button.click()
            log("🚩正在打开编辑页")
            
            edit_option = page.ele("@role=option", -3)
            if not edit_option:
                return False
            
            edit_option.click()
            time.sleep(2)
            return True
        except Exception as e:
            log(f"    ❌打开编辑页失败: {e}")
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
            log(f"    ❌处理目标失败: {e}")
            return ProcessResult.FAILED

class ReplacePlaceholderJsonStrategy(ProcessStrategy):
    """
    从本地 cdn.json 读取 CDN 链接并替换 JSON 的策略
    与 GUI 解耦，只需传入 base_folder
    """
    def __init__(self, base_folder: str):
        self.base_folder = Path(base_folder)

    def process_target(self, page, target: str, update_action: Callable[[str], str]) -> ProcessResult:
        try:
            import pyperclip
            page.wait.load_start()

            # 打开编辑器
            if not page.ele('编辑值').click(by_js=True):
                return ProcessResult.FAILED
            time.sleep(1.5)

            # 切换到编辑标签页
            editor_tab = page.browser.latest_tab
            editor_tab.set.activate()
            log(f"🚩切换到编辑标签页")

            # 获取 JSON
            editor_tab.ele("@@type=button@@class^el-button").click(by_js=True)
            time.sleep(0.5)
            editor_tab.ele("获取当前JSON").click()
            time.sleep(1)
            log(f"   ✔️ 获取当前JSON成功")

            original_json = pyperclip.paste()
            if not original_json:
                return ProcessResult.FAILED

            # 读取 cdn.json
            json_path = Path(self.base_folder) / target / 'cdn.json'
            if not json_path.exists():
                log(f"❌ 找不到 cdn.json: {json_path}")
                return ProcessResult.FAILED

            with open(json_path, 'r', encoding='utf-8') as f:
                cdn_data = json.load(f)

            # 替换（调用 iterate）
            from utils.update_json_action import iterate
            replaced_json = iterate(
                original_json,
                cdn_data.get("step1_cdn", ""),
                cdn_data.get("step2_cdn", ""),
                cdn_data.get("step3_cdn", ""),
                cdn_data.get("feature1_cdn", ""),
                cdn_data.get("feature2_cdn", ""),
                cdn_data.get("feature3_cdn", ""),
                cdn_data.get("feature4_cdn", "")
            )

            # 输入新 JSON
            input_ele = editor_tab.ele("@class=app-writer")
            input_ele.click()
            input_ele.input(replaced_json)
            log(f"   ✔️ 输入替换后的JSON成功")
            # 保存JSON
            save_json_button = editor_tab.ele("确定")
            if save_json_button:
                save_json_button.click()
                time.sleep(1)
            log(f"   ✔️ 保存JSON成功")

            # 保存编辑器
            save_editor_button = editor_tab.ele("@@type=button@@class^el-button", index=8)
            if save_editor_button:
                save_editor_button.click()
                time.sleep(5)
            log(f"   ✔️ 保存编辑器成功")
            # 回主页面保存
            edit_page = page.browser.get_tab(1)
            
            thumbnail = page.ele('修改字段',-6)
            thumbnail.click()
            
            random_choice = random.choice(
                                          [cdn_data.get("feature1_cdn", ""),
                cdn_data.get("feature2_cdn", ""),
                cdn_data.get("feature3_cdn", ""),
                cdn_data.get("feature4_cdn", "")]
                                          )
            
            thumbnail_input = page.ele('@@required:required@@type=text',-1)
            thumbnail_input.click()
            thumbnail_input.clear()  # 先清空
            thumbnail_input.input(random_choice)  # 输入新内容
            log(f"   ✔️ 输入随机Feature图片作为thumbnail成功")
            confirm = page.ele('确定')
            confirm.click()
            
            edit_page.ele('保存').click()
            if edit_page.wait.url_change('https://op.pacdora.com/topic/List', timeout=60):
                return ProcessResult.SUCCESS

        except Exception as e:
            log(f"❌ 处理失败: {e}")
        return ProcessResult.FAILED

class DummyEditorStrategy(EditorStrategy):
    def open_editor(self, page, target: str = None) -> bool:
        return True
        
class SyncOnlineProcessStrategy(ProcessStrategy):
    """同步启用处理策略"""
    
    def process_target(self, page, target, update_action):
        """处理单个目标 - 设置同步启用"""
        try:
            # 等待页面开始加载
            page.wait.load_start()
            
            # 点击编辑按钮
            edit_button = page.ele('@class=table-td', -1)
            if not edit_button:
                log("    ❌未找到编辑按钮")
                return ProcessResult.FAILED
            
            edit_button.click()
            
            # 悬浮到同步状态
            sync_button = page.ele('同步状态')
            if not sync_button:
                log("    ❌未找到同步状态按钮")
                return ProcessResult.FAILED
                
            sync_button.hover()
            
            # 点击同步启用
            sync_online_button = page.ele('同步启用')
            if not sync_online_button:
                log("    ❌未找到同步启用按钮")
                return ProcessResult.FAILED
                
            sync_online_button.click()
            log(f"   ✔️ 定位到同步启用按钮")

            sync_confirm_button = page.ele('@class=v-btn v-btn--is-elevated v-btn--has-bg theme--light v-size--default primary',2)
            sync_confirm_button.click()
            log(f"   ✔️ 确认同步启用")
            
            # 等待处理完成
            page.wait(8,10)
            
            log(f"  ✔️ {target} 同步状态设置成功")
            return ProcessResult.SUCCESS
            
        except Exception as e:
            log(f"    ❌处理目标失败: {e}")
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
                 interaction_strategy: Optional[InteractionStrategy] = None,
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
        # ✅ 确保 cache 目录存在
        cache_dir = Path(get_writable_path('cache')).parent
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 1. 准备目标列表
            all_targets = self._prepare_targets()
            if not all_targets:
                log("    ❌未找到任何目标")
                return
            
            # 2. 加载进度
            completed_targets = self._load_progress()
            remaining_targets = [t for t in all_targets if t not in completed_targets]
            
            log(f"🔄总目标数: {len(all_targets)}, 已完成: {len(completed_targets)}, 剩余: {len(remaining_targets)}")
            
            # 3. 登录
            if not self._execute_login():
                return
            
            # 4. 导航到操作页面
            if not self._execute_navigation():
                return
            
            # 5. 批量处理目标
            self._process_targets(remaining_targets, all_targets, completed_targets)
            
        except Exception as e:
            log(f"    ❌程序运行出错: {e}")
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
            log(f"    ❌读取CSV文件出错: {e}")
        return targets
    
    def _load_progress(self) -> List[str]:
        """加载进度"""
        if Path(self.config.checkpoint_file).exists():
            try:
                with open(self.config.checkpoint_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                log(f"    ❌加载进度失败: {e}")
        return []
    
    def _save_progress(self, completed_targets: List[str]):
        """保存进度"""
        try:
            Path(self.config.checkpoint_file).parent.mkdir(exist_ok=True)
            with open(self.config.checkpoint_file, 'wb') as f:
                pickle.dump(completed_targets, f)
        except Exception as e:
            log(f"    ❌保存进度失败: {e}")
    
    def _execute_login(self) -> bool:
        """执行登录"""
        return self.login_strategy.execute_login(self.browser.latest_tab, self.config)
    
    def _execute_navigation(self) -> bool:
        """执行导航"""
        return self.navigation_strategy.navigate_to_target(self.browser.latest_tab, self.config)
    
    def _process_targets(self, remaining_targets: List[str], all_targets: List[str], completed_targets: List[str]):
        """批量处理目标"""
        i = 0

        def process_next_target():
            nonlocal i
            if i >= len(remaining_targets):
                log("✅ 所有目标处理完成。")
                return

            target = remaining_targets[i]
            try:
                current_progress = len(all_targets) - len(remaining_targets) + i + 1
                log(f"🚩正在处理: {target} (进度: {current_progress}/{len(all_targets)})")

                # 搜索目标
                result_count = self.search_strategy.search_target(self.browser.latest_tab, target)

                if result_count == 0:
                    log(f"  ❌ {target}未找到搜索结果")
                    i += 1
                    process_next_target()
                elif result_count >= 3:
                    log(f"  ⚠️ {target}有多个搜索结果")

                    # ✅ 使用交互策略
                    self.interaction_strategy.request_confirmation(
                        f"目标 '{target}' 有多个结果，是否继续？",
                        on_confirm=lambda confirmed: handle_confirm(confirmed, target, result_count)
                    )
                elif result_count == 2:
                    log("  ✔️ 定位成功")
                    if self.editor_strategy.open_editor(self.browser.latest_tab, target):
                        finalize_process(target)
                    else:
                        i += 1
                        process_next_target()

            except Exception as e:
                log(f"    ❌处理{target}时发生错误: {e}")
                self._save_progress(completed_targets)
        
        def handle_confirm(confirmed, target, result_count):
            if confirmed and result_count >= 2:
                if self.editor_strategy.open_editor(self.browser.latest_tab, target):
                    finalize_process(target)
                else:
                    i += 1
                    process_next_target()
            else:
                i += 1
                process_next_target()

        def finalize_process(target):
            result = self.process_strategy.process_target(
                self.browser.latest_tab, target, self.update_action
            )
            if result == ProcessResult.SUCCESS:
                log(f"✅ {target}已成功更新")
                completed_targets.append(target)
                self._save_progress(completed_targets)
            else:
                log(f"    ❌{target}处理失败")
            log('='*50)
            nonlocal i
            i += 1
            process_next_target()

        # 开始处理第一个
        process_next_target()

# =========================== 工厂方法 ===========================

class BotFactory:
    """机器人工厂"""
    
    @staticmethod
    def create_pacdora_json_bot(language: str, update_action: Callable[[str], str], 
                               target_list: Optional[List[str]] = None,
                               target_csv_path: Optional[str] = None,
                               interaction_strategy: Optional[InteractionStrategy] = None) -> ModularBatchBot:
        """创建默认的Pacdora JSON处理机器人"""
        
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
            interaction_strategy=interaction_strategy,
            target_list=target_list,
            target_csv_path=target_csv_path
        )
        
    # dp_bot_manager.py

    @staticmethod
    def create_upload_replace_bot(
        language: str,
        base_folder: str,
        target_list: Optional[List[str]] = None,
        target_csv_path: Optional[str] = None,
        interaction_strategy: Optional[InteractionStrategy] = None
    ) -> ModularBatchBot:
        """
        创建「上传图片 + 替换 CDN」专用机器人
        """
        config = OperationConfig(
            login_url="https://op.pacdora.com/login",
            dashboard_url_contains="dashboard",
            operate_url="https://op.pacdora.com/topic/List",
            operate_url_contains="List",
            edit_url_contains="edit",
            checkpoint_file="cache/upload_replace_progress.pkl",
            cookie_file="cache/cookies.pkl"
        )

        return ModularBatchBot(
            config=config,
            login_strategy=CookieLoginStrategy(),
            navigation_strategy=StandardNavigationStrategy(language),
            search_strategy=FlexibleSearchStrategy(),
            editor_strategy=StandardEditorStrategy(),
            process_strategy=ReplacePlaceholderJsonStrategy(base_folder=base_folder),
            update_action=lambda x: x,  # 占位，实际替换在策略内部完成
            interaction_strategy=interaction_strategy,
            target_list=target_list,
            target_csv_path=target_csv_path
        )
        
    @staticmethod
    def create_online_sync_bot(language: str,
                              target_list: Optional[List[str]] = None,
                              target_csv_path: Optional[str] = None,
                              interaction_strategy: Optional[InteractionStrategy] = None) -> ModularBatchBot:
        """创建同步启用机器人"""
        
        config = OperationConfig(
            login_url="https://op.pacdora.com/login",
            dashboard_url_contains="dashboard",
            operate_url="https://op.pacdora.com/topic/List",
            operate_url_contains="List",
            edit_url_contains="edit",
            checkpoint_file='./cache/online_progress.pkl'  # 使用不同的进度文件
        )
        
        return ModularBatchBot(
            config=config,
            login_strategy=CookieLoginStrategy(),
            navigation_strategy=StandardNavigationStrategy(language),
            search_strategy=FlexibleSearchStrategy(),
            editor_strategy=DummyEditorStrategy, # 传入dummy，因为不需要editor策略，直接在process里进行
            process_strategy=SyncOnlineProcessStrategy(),  # 新的同步处理策略
            update_action=lambda x: x,  # 不需要更新函数
            interaction_strategy=interaction_strategy,
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
        """创建自定义的批量化Bot"""
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

    online_bot = BotFactory.create_online_sync_bot(language='英语', target_list= ['triangle-box-mockup'])
    online_bot.run()
    
if __name__ == "__main__":
    example_usage()