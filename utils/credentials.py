import keyring
import json
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QTabWidget, QWidget, QLineEdit, QComboBox, QPushButton, 
                             QLabel, QDialogButtonBox, QMessageBox, QListWidget, 
                             QListWidgetItem, QSplitter, QGroupBox, QCheckBox)
from PySide6.QtCore import Qt

# 使用一个固定的服务名称来存储所有相关的凭证
AWS_SERVICE_NAME = "WSA_AWS_Credentials"
LLM_SERVICE_NAME = "WSA_LLM_APIS"


def save_credentials(access_key: str, secret_key: str, region: str):
    """
    将AWS凭证安全地保存到操作系统的凭证管理器中。
    我们将所有凭证打包成一个JSON字符串进行存储。
    """
    credentials = {
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "region_name": region
    }
    # Keyring希望用户名为字符串，我们用一个固定的key来存储整个JSON包
    keyring.set_password(AWS_SERVICE_NAME, "aws_credentials", json.dumps(credentials))


def load_credentials() -> dict | None:
    """
    从操作系统的凭证管理器中加载AWS凭证。
    返回一个包含凭证的字典，如果找不到则返回None。
    """
    try:
        credentials_json = keyring.get_password(AWS_SERVICE_NAME, "aws_credentials")
        if credentials_json:
            return json.loads(credentials_json)
        return None
    except Exception as e:
        # 在某些环境下（如无头服务器），keyring可能会失败
        print(f"无法从凭证管理器加载凭证: {e}")
        return None


def delete_credentials():
    """
    从操作系统的凭证管理器中删除已存储的AWS凭证。
    """
    try:
        keyring.delete_password(AWS_SERVICE_NAME, "aws_credentials")
    except keyring.errors.PasswordDeleteError:
        # 如果凭证不存在，某些后端会抛出错误，可以安全地忽略
        pass


def save_llm_api(provider: str, api_key: str):
    """
    保存或更新一个LLM提供商的API密钥。
    """
    apis = load_llm_apis()
    apis[provider] = api_key
    keyring.set_password(LLM_SERVICE_NAME, "llm_apis", json.dumps(apis))


def load_llm_apis() -> dict:
    """
    从凭证管理器加载所有LLM API。
    """
    try:
        apis_json = keyring.get_password(LLM_SERVICE_NAME, "llm_apis")
        if apis_json:
            return json.loads(apis_json)
        return {}
    except Exception as e:
        print(f"无法从凭证管理器加载LLM API: {e}")
        return {}


def delete_llm_api(provider: str):
    """
    从凭证管理器中删除一个LLM提供商的API密钥。
    """
    apis = load_llm_apis()
    if provider in apis:
        del apis[provider]
        keyring.set_password(LLM_SERVICE_NAME, "llm_apis", json.dumps(apis))


def load_llm_api_key(provider: str) -> str | None:
    """
    加载指定LLM提供商的API密钥。
    """
    apis = load_llm_apis()
    return apis.get(provider)





class SCConfigDialog(QDialog):
    """
    一个用于配置AWS和LLM API凭证的对话框。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Service Configuration")
        self.setMinimumSize(600, 400)
        self.resize(700, 500)

        main_layout = QVBoxLayout(self)
        
        # Tab widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # AWS Tab
        aws_widget = QWidget()
        self.setup_aws_tab(aws_widget)
        tab_widget.addTab(aws_widget, "AWS Credentials")

        # LLM API Tab
        llm_widget = QWidget()
        self.setup_llm_tab(llm_widget)
        tab_widget.addTab(llm_widget, "LLM APIs")

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        # 存储LLM APIs数据
        self.llm_apis = {}
        self.load_existing_llm_apis()

    def setup_aws_tab(self, parent_widget):
        """
        设置AWS配置标签页的UI。
        """
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # AWS配置组
        aws_group = QGroupBox("AWS Configuration")
        form_layout = QFormLayout(aws_group)

        self.aws_access_key_id_input = QLineEdit()
        self.aws_access_key_id_input.setPlaceholderText("Enter your AWS Access Key ID")
        
        self.aws_secret_access_key_input = QLineEdit()
        self.aws_secret_access_key_input.setEchoMode(QLineEdit.Password)
        self.aws_secret_access_key_input.setPlaceholderText("Enter your AWS Secret Access Key")
        
        # 添加显示/隐藏密码的复选框
        self.show_aws_password = QCheckBox("Show password")
        self.show_aws_password.toggled.connect(self.toggle_aws_password_visibility)
        
        self.aws_region_input = QLineEdit()
        self.aws_region_input.setPlaceholderText("e.g., us-west-2, eu-west-1")

        form_layout.addRow("Access Key ID:", self.aws_access_key_id_input)
        form_layout.addRow("Secret Access Key:", self.aws_secret_access_key_input)
        form_layout.addRow("", self.show_aws_password)
        form_layout.addRow("Default Region:", self.aws_region_input)

        layout.addWidget(aws_group)
        layout.addStretch()
        
        self.load_existing_aws_credentials()

    def setup_llm_tab(self, parent_widget):
        """
        设置LLM API配置标签页的UI - 使用改进的列表界面。
        """
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 使用分割器来创建左右布局
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：API提供商列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 列表标题和按钮
        list_header = QHBoxLayout()
        list_header.addWidget(QLabel("Configured APIs:"))
        list_header.addStretch()
        
        self.add_new_button = QPushButton("Add New")
        self.add_new_button.clicked.connect(self.add_new_api)
        list_header.addWidget(self.add_new_button)
        
        left_layout.addLayout(list_header)
        
        # API列表
        self.api_list_widget = QListWidget()
        self.api_list_widget.itemSelectionChanged.connect(self.on_api_selection_changed)
        left_layout.addWidget(self.api_list_widget)
        
        splitter.addWidget(left_widget)
        
        # 右侧：编辑区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 编辑组
        edit_group = QGroupBox("Edit API Configuration")
        edit_layout = QFormLayout(edit_group)
        
        self.provider_name_input = QLineEdit()
        self.provider_name_input.setPlaceholderText("e.g., OpenAI, Anthropic, Google")
        self.provider_name_input.textChanged.connect(self.on_provider_name_changed)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter API key")
        self.api_key_input.textChanged.connect(self.on_api_key_changed)
        
        # 显示/隐藏API密钥的复选框
        self.show_api_key = QCheckBox("Show API key")
        self.show_api_key.toggled.connect(self.toggle_api_key_visibility)
        
        edit_layout.addRow("Provider Name:", self.provider_name_input)
        edit_layout.addRow("API Key:", self.api_key_input)
        edit_layout.addRow("", self.show_api_key)
        
        right_layout.addWidget(edit_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_api_button = QPushButton("Save Changes")
        self.save_api_button.clicked.connect(self.save_current_api)
        self.save_api_button.setEnabled(False)
        
        self.delete_api_button = QPushButton("Delete API")
        self.delete_api_button.clicked.connect(self.delete_selected_api)
        self.delete_api_button.setEnabled(False)
        
        button_layout.addWidget(self.save_api_button)
        button_layout.addWidget(self.delete_api_button)
        
        right_layout.addLayout(button_layout)
        right_layout.addStretch()
        
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # 初始状态
        self.current_editing_provider = None
        self.clear_edit_fields()

    def toggle_aws_password_visibility(self, checked):
        """切换AWS密码显示/隐藏"""
        if checked:
            self.aws_secret_access_key_input.setEchoMode(QLineEdit.Normal)
        else:
            self.aws_secret_access_key_input.setEchoMode(QLineEdit.Password)

    def toggle_api_key_visibility(self, checked):
        """切换API密钥显示/隐藏"""
        if checked:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)

    def load_existing_aws_credentials(self):
        """加载现有的AWS凭证"""
        creds = load_credentials()
        if creds:
            self.aws_access_key_id_input.setText(creds.get("aws_access_key_id", ""))
            self.aws_secret_access_key_input.setText(creds.get("aws_secret_access_key", ""))
            self.aws_region_input.setText(creds.get("region_name", ""))

    def load_existing_llm_apis(self):
        """加载现有的LLM APIs"""
        self.llm_apis = load_llm_apis()
        self.update_api_list()

    def update_api_list(self):
        """更新API列表显示"""
        self.api_list_widget.clear()
        for provider in sorted(self.llm_apis.keys()):
            item = QListWidgetItem(provider)
            item.setData(Qt.UserRole, provider)
            self.api_list_widget.addItem(item)

    def add_new_api(self):
        """添加新的API配置"""
        self.api_list_widget.clearSelection()
        self.current_editing_provider = None
        self.clear_edit_fields()
        self.provider_name_input.setEnabled(True)
        self.provider_name_input.setFocus()
        self.update_button_states()

    def on_api_selection_changed(self):
        """当选择的API改变时"""
        current_item = self.api_list_widget.currentItem()
        if current_item:
            provider = current_item.data(Qt.UserRole)
            self.current_editing_provider = provider
            self.provider_name_input.setText(provider)
            self.provider_name_input.setEnabled(False)  # 已存在的provider名称不可编辑
            self.api_key_input.setText(self.llm_apis.get(provider, ""))
        else:
            self.current_editing_provider = None
            self.clear_edit_fields()
        
        self.update_button_states()

    def on_provider_name_changed(self):
        """当provider名称改变时"""
        self.update_button_states()

    def on_api_key_changed(self):
        """当API密钥改变时"""
        self.update_button_states()

    def clear_edit_fields(self):
        """清空编辑字段"""
        self.provider_name_input.clear()
        self.provider_name_input.setEnabled(True)
        self.api_key_input.clear()

    def update_button_states(self):
        """更新按钮状态"""
        provider_name = self.provider_name_input.text().strip()
        api_key = self.api_key_input.text().strip()
        
        # 保存按钮：需要provider名称和API密钥都不为空
        self.save_api_button.setEnabled(bool(provider_name and api_key))
        
        # 删除按钮：需要选中已存在的API
        self.delete_api_button.setEnabled(self.current_editing_provider is not None)

    def save_current_api(self):
        """保存当前编辑的API"""
        provider_name = self.provider_name_input.text().strip()
        api_key = self.api_key_input.text().strip()
        
        if not provider_name or not api_key:
            QMessageBox.warning(self, "Warning", "Both provider name and API key are required.")
            return
        
        try:
            # 如果是重命名（新名称与当前编辑的不同），先删除旧的
            if (self.current_editing_provider and 
                provider_name != self.current_editing_provider):
                delete_llm_api(self.current_editing_provider)
            
            # 保存新的或更新的API
            save_llm_api(provider_name, api_key)
            
            # 更新本地数据
            if self.current_editing_provider and provider_name != self.current_editing_provider:
                # 删除旧的
                if self.current_editing_provider in self.llm_apis:
                    del self.llm_apis[self.current_editing_provider]
            
            self.llm_apis[provider_name] = api_key
            self.current_editing_provider = provider_name
            
            # 更新界面
            self.update_api_list()
            
            # 选中刚保存的项
            for i in range(self.api_list_widget.count()):
                item = self.api_list_widget.item(i)
                if item.data(Qt.UserRole) == provider_name:
                    self.api_list_widget.setCurrentItem(item)
                    break
            
            QMessageBox.information(self, "Success", f"API configuration for '{provider_name}' has been saved.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save API configuration: {e}")

    def delete_selected_api(self):
        """删除选中的API"""
        if not self.current_editing_provider:
            return
        
        provider = self.current_editing_provider
        reply = QMessageBox.question(self, 'Confirm Deletion', 
                                   f"Are you sure you want to delete the API key for '{provider}'?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                delete_llm_api(provider)
                if provider in self.llm_apis:
                    del self.llm_apis[provider]
                
                self.update_api_list()
                self.clear_edit_fields()
                self.current_editing_provider = None
                self.update_button_states()
                
                QMessageBox.information(self, "Success", f"API key for '{provider}' has been deleted.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete API configuration: {e}")

    def get_credentials(self):
        """
        获取用户输入的凭证信息。
        注意：这个方法是为了保持与现有代码的兼容性。
        """
        return {
            "access_key": self.aws_access_key_id_input.text().strip(),
            "secret_key": self.aws_secret_access_key_input.text().strip(),
            "region": self.aws_region_input.text().strip()
        }

    def accept(self):
        """
        当用户点击OK时保存所有配置。
        """
        # 保存AWS凭证
        aws_access_key = self.aws_access_key_id_input.text().strip()
        aws_secret_key = self.aws_secret_access_key_input.text().strip()
        aws_region = self.aws_region_input.text().strip()
        
        # 验证AWS凭证
        if aws_access_key or aws_secret_key or aws_region:
            if not (aws_access_key and aws_secret_key and aws_region):
                QMessageBox.warning(self, "Warning", 
                                  "All AWS fields must be filled or all left empty.")
                return
            
            try:
                save_credentials(aws_access_key, aws_secret_key, aws_region)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save AWS credentials: {e}")
                return

        # 如果当前正在编辑API且有未保存的更改，提醒用户
        provider_name = self.provider_name_input.text().strip()
        api_key = self.api_key_input.text().strip()
        
        if provider_name and api_key:
            # 检查是否有未保存的更改
            if (not self.current_editing_provider or 
                provider_name != self.current_editing_provider or
                api_key != self.llm_apis.get(self.current_editing_provider, "")):
                
                reply = QMessageBox.question(self, "Unsaved Changes", 
                                           "You have unsaved changes to the API configuration. "
                                           "Do you want to save them before closing?",
                                           QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                           QMessageBox.Yes)
                
                if reply == QMessageBox.Cancel:
                    return
                elif reply == QMessageBox.Yes:
                    self.save_current_api()
            
        super().accept()