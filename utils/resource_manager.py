# utils/resource_manager.py
import sys
import os
import shutil
from pathlib import Path

class ResourceManager:
    """
    处理PyInstaller打包后的资源文件访问。
    
    主要功能:
    1. 区分开发环境和打包环境，提供统一的资源访问接口
    2. 管理只读资源(打包在exe中)和可写资源(存储在用户目录)
    3. 自动将打包资源复制到用户目录以支持写操作
    4. 提供跨平台的用户数据目录支持(Windows/macOS/Linux)
    """
    
    def __init__(self):
        self.is_bundled = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        self.base_path = self._get_base_path()
        self.user_data_path = self._get_user_data_path()
        
    def _get_base_path(self):
        """获取应用基础路径"""
        if self.is_bundled:
            # PyInstaller环境
            return Path(sys._MEIPASS)
        else:
            # 开发环境
            return Path(__file__).parent.parent
    
    def _get_user_data_path(self):
        """获取用户数据存储路径"""
        if sys.platform.startswith('darwin'):
            # macOS: ~/Library/Application Support/AppName
            app_support = Path.home() / 'Library' / 'Application Support' / 'WebSetupAutomation'
        elif sys.platform.startswith('win'):
            # Windows: %APPDATA%/AppName
            app_support = Path(os.environ.get('APPDATA', Path.home())) / 'WebSetupAutomation'
        else:
            # Linux: ~/.local/share/AppName
            app_support = Path.home() / '.local' / 'share' / 'WebSetupAutomation'
        
        app_support.mkdir(parents=True, exist_ok=True)
        return app_support
    
    def get_resource_path(self, resource_name):
        """获取打包内资源的路径（只读）"""
        return self.base_path / resource_name
    
    def get_writable_resource_path(self, resource_name):
        """获取可写资源的路径（复制到用户目录）"""
        user_resource = self.user_data_path / resource_name
        bundled_resource = self.base_path / resource_name
        
        # 如果用户目录中不存在，从打包资源中复制
        if not user_resource.exists() and bundled_resource.exists():
            if bundled_resource.is_file():
                shutil.copy2(bundled_resource, user_resource)
            elif bundled_resource.is_dir():
                shutil.copytree(bundled_resource, user_resource, dirs_exist_ok=True)
        
        return user_resource
    
    def ensure_user_resources(self) -> bool:
        """确保用户目录中有必要的资源文件"""
        critical_resources = ['size.csv', 'json_templates', 'aws_config.json']
        
        for resource in critical_resources:
            try:
                self.get_writable_resource_path(resource)
                print(f"✓ Resource '{resource}' ready at: {self.user_data_path / resource}")
                return True
            except Exception as e:
                print(f"✗ Failed to prepare resource '{resource}': {e}")
                return False
    
    def get_temp_dir(self):
        """获取临时文件目录"""
        temp_dir = self.user_data_path / 'temp'
        temp_dir.mkdir(exist_ok=True)
        return temp_dir
    
    def open_user_data_folder(self):
        """打开用户数据文件夹"""
        import subprocess
        
        if sys.platform.startswith('darwin'):
            subprocess.run(['open', str(self.user_data_path)])
        elif sys.platform.startswith('win'):
            subprocess.run(['explorer', str(self.user_data_path)])
        else:
            subprocess.run(['xdg-open', str(self.user_data_path)])

# 全局实例
resource_manager = ResourceManager()

# 便捷函数
def get_resource_path(resource_name):
    """获取资源路径（只读）"""
    return resource_manager.get_resource_path(resource_name)

def get_writable_path(resource_name):
    """获取可写资源路径"""
    return resource_manager.get_writable_resource_path(resource_name)

def ensure_resources():
    """确保所有必要资源可用"""
    resource_manager.ensure_user_resources()