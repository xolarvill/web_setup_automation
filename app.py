import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QLineEdit, QComboBox, QPushButton, QFileDialog, QTextEdit, 
                              QFrame, QCheckBox,
                              QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from qt_material import apply_stylesheet  # 导入qt-material库
import os
from datetime import datetime
from PySide6.QtGui import QGuiApplication
from utils.parse import extract_cutout_nextline, extract_cutout_currentline, segment, parse_faq_text, extract_url
from utils.fetch_mockup_details import fetch_mockup_details
from PySide6.QtCore import QTimer
from utils.upload_selenium_class import ImageUploader
import json
from utils.upload_boto import S3Uploader


class LabeledLineEditWithCopy(QWidget):
    """
    带复制按钮的输入框class
    ---
    text()获取内容
    setText()传入内容
    set_dimensions()
    turn_off_text_input()
    """
    def __init__(self, label_text="Label:", placeholder= "Click button on the right to copy", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # 保证无多余外边距
        layout.setSpacing(8) # 控制label和输入框之间的间距

        self.label = QLabel(label_text)
        layout.addWidget(self.label)

        # 输入框和按钮容器
        input_container = QWidget()
        input_container.setFixedWidth(350)
        input_container.setFixedHeight(32)

        self.line_edit = QLineEdit(input_container)
        self.line_edit.setGeometry(0, 0, 290, 32)
        if placeholder is not None:
            self.line_edit.setPlaceholderText(placeholder)

        self.copy_btn = QPushButton("📋", input_container)
        self.copy_btn.setGeometry(295, 2, 50, 28)
        self.copy_btn.setFocusPolicy(Qt.NoFocus)
        self.copy_btn.setStyleSheet("""
            QPushButton {
            background-color: #E8B15C;
            color: white;
            border-radius: 6px;
            font-weight: bold;
            }
            QPushButton:hover {
            background-color: #D5AB56;
            }
        """)
        def on_copy_clicked():
            QGuiApplication.clipboard().setText(self.line_edit.text())
            original_text = self.copy_btn.text()
            original_style = self.copy_btn.styleSheet()
            self.copy_btn.setText("☑️")
            self.copy_btn.setStyleSheet("""
            QPushButton {
            background-color: #8FB236;
            color: #666666;
            border-radius: 6px;
            font-weight: bold;
            }
            """)
            self.copy_btn.setEnabled(False)
            # 恢复按钮状态
            QTimer.singleShot(800, lambda: (
            self.copy_btn.setText(original_text),
            self.copy_btn.setStyleSheet(original_style),
            self.copy_btn.setEnabled(True)
            ))
        self.copy_btn.clicked.connect(on_copy_clicked)

        layout.addWidget(input_container)

    def text(self):
        return self.line_edit.text()

    def setText(self, text):
        self.line_edit.setText(text)
        
    def set_dimensions(self,height: int, width: int):
        self.line_edit.setFixedHeight(height)
        self.line_edit.setFixedWidth(width)
        # 不改变 self.copy_btn 尺寸
        
    def turn_off_text_input(self):
        """禁用文本输入"""
        self.line_edit.setReadOnly(True)
        self.copy_btn.setEnabled(False)


class WSA(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web Setup Automation")
        self.setMinimumSize(1330, 795)  # 增加最小窗口大小
        self.setWindowIcon(QIcon("resources/icon.png"))  # 可选：添加图标文件
        self.segments = []

        # 0. 中心小部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # 1. 左侧面板 - 输入控件
        left_panel = QWidget()
        left_panel.setFixedWidth(490)
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标题
        left_title_label = QLabel("Configuration Panel")
        left_title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; background-color: transparent;")
        left_layout.addWidget(left_title_label)
        
        # 1.1 first group，因为没有命名的必要
        first_group_layout = QVBoxLayout()
        
        # Page Type下拉菜单
        # 单独定义Page Type选项，在一个Hbox里放label + Combobox
        page_type_layout = QHBoxLayout()
        page_label = QLabel("Type:")
        page_label.setMinimumWidth(100)
        self.page_type = QComboBox()
        self.page_type.addItems(["Mockup tool", "Mockup resource", "Mockup content", "Dieline tool", "Dieline resource", "TOOLS", "Landing page"])
        self.page_type.setCurrentIndex(0)
        self.page_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        page_type_layout.addWidget(page_label)
        page_type_layout.addWidget(self.page_type)
        first_group_layout.addLayout(page_type_layout)

        # 将first_group添加到left_layout
        left_layout.addLayout(first_group_layout)
        
        # 分隔线，section选择框
        separator0 = QFrame()
        separator0.setFrameShape(QFrame.HLine)
        separator0.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(separator0)
        
        # 1.2 Notion PRD中对应的自定义选项
        # 1.2.1
        checkbox_layout = QHBoxLayout()
        self.single_image_checkbox = QCheckBox("传图单张")
        self.single_image_checkbox.setChecked(True)
        checkbox_layout.addWidget(self.single_image_checkbox)

        self.scroll_to_mockup_checkbox = QCheckBox("下滑到样机")
        self.scroll_to_mockup_checkbox.setChecked(True)
        checkbox_layout.addWidget(self.scroll_to_mockup_checkbox)
        
        self.color_diy_checkbox = QCheckBox("颜色自定义")
        self.color_diy_checkbox.setChecked(True)
        checkbox_layout.addWidget(self.color_diy_checkbox)
        
        # 1.2.2
        another_checkbox_layout = QHBoxLayout()
        
        self.color_label_diy_checkbox = QCheckBox("颜色标签自定义")
        self.color_label_diy_checkbox.setChecked(False)
        another_checkbox_layout.addWidget(self.color_label_diy_checkbox)
        
        self.cover_label_diy_checkbox = QCheckBox("cover标题自定义")
        self.cover_label_diy_checkbox.setChecked(False)
        another_checkbox_layout.addWidget(self.cover_label_diy_checkbox)
        
        self.another_checkbox = QCheckBox("待实现功能")
        self.another_checkbox.setChecked(False)
        another_checkbox_layout.addWidget(self.another_checkbox)
        
        # 1.2.3
        # 自定义颜色输入选项
        self.color_diy_choice_widget = LabeledLineEditWithCopy("颜色自定义", "Enter color hex codes'")
        self.color_diy_choice_widget.setText("#FFFFFF")  # 默认颜色
        
        # 自定义颜色标签
        self.color_label_diy_choice_widget = LabeledLineEditWithCopy("颜色标签自定义", "Enter color label text'")
        
        # 自定义封面标题标签
        self.cover_label_diy_widget = LabeledLineEditWithCopy("Cover标题标签", "有自定义需求可以加入")
        
        left_layout.addLayout(checkbox_layout)
        left_layout.addLayout(another_checkbox_layout)
        left_layout.addWidget(self.color_diy_choice_widget)
        left_layout.addWidget(self.color_label_diy_choice_widget)
        left_layout.addWidget(self.cover_label_diy_widget)

        # 分隔线，section输出栏
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(separator1)
        
        # 1.3 输出字段
        # 文件路径
        self.file_path_widget = LabeledLineEditWithCopy("文件路径")
        left_layout.addWidget(self.file_path_widget)
        
        # 浏览器title
        self.title_widget = LabeledLineEditWithCopy("浏览器title")
        left_layout.addWidget(self.title_widget)
        
        # 网页描述
        self.description_widget = LabeledLineEditWithCopy("网页描述")
        left_layout.addWidget(self.description_widget)
        
        # 网页关键词
        self.keywords_widget = LabeledLineEditWithCopy("关键词")
        left_layout.addWidget(self.keywords_widget)
        
        # View
        self.view_widget = LabeledLineEditWithCopy("View")
        left_layout.addWidget(self.view_widget)
        
        # Try
        self.try_widget = LabeledLineEditWithCopy("Try")
        left_layout.addWidget(self.try_widget)
        
        # 分隔线
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(separator2)
        
        # 1.4 按钮
        button_layout = QVBoxLayout()
        
        buttons = [
            ("Update", self.update_action),
            ("Generate JSON", self.generate_json_action)
        ]
        for text, callback in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setMinimumHeight(35)
            button_layout.addWidget(btn)
            
        left_layout.addLayout(button_layout)
        
        # 添加弹性空间
        left_layout.addStretch()
        
        # 垂直分隔线
        vertical_separator1 = QFrame()
        vertical_separator1.setFrameShape(QFrame.VLine)
        vertical_separator1.setFrameShadow(QFrame.Sunken)
        
        # 2. 中间面板 - 图片cdn地址
        mid_panel = QWidget()
        mid_panel.setFixedWidth(490)

        mid_layout = QVBoxLayout(mid_panel)
        mid_layout.setSpacing(12)
        mid_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        mid_title_label = QLabel("CDN Panel")
        mid_title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; background-color: transparent;")
        mid_layout.addWidget(mid_title_label)
        
        # 添加空白spacing 解决左右不平齐问题
        #spacer = QWidget()
        #spacer.setFixedHeight(6)
        #mid_layout.addWidget(spacer)
        
        # 2.1 pic path folder in NAS
        self.pics_path_widget = LabeledLineEditWithCopy("NAS path","Enter the path of your pics folder here. OR use the Browse button.")
        mid_layout.addWidget(self.pics_path_widget)
        
        # 分隔线
        separator_mid0 = QFrame()
        separator_mid0.setFrameShape(QFrame.HLine)
        separator_mid0.setFrameShadow(QFrame.Sunken)
        mid_layout.addWidget(separator_mid0)
        

        # 2.2 Cover photos区域
        cover_group_layout = QVBoxLayout()
        cover_group_layout.setSpacing(8)
        cover_group_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cover_cdn_widget = LabeledLineEditWithCopy("Cover", placeholder="Cover封面")
        cover_group_layout.addWidget(self.cover_cdn_widget)
        self.cover_more_cdn_widget = LabeledLineEditWithCopy("Cover more", placeholder="More封面")
        cover_group_layout.addWidget(self.cover_more_cdn_widget)
        mid_layout.addLayout(cover_group_layout)

        # 分隔线
        separator_mid1 = QFrame()
        separator_mid1.setFrameShape(QFrame.HLine)
        separator_mid1.setFrameShadow(QFrame.Sunken)
        mid_layout.addWidget(separator_mid1)

        # 2.3 Steps pics区域
        steps_group_layout = QVBoxLayout()
        steps_group_layout.setSpacing(8)
        steps_group_layout.setContentsMargins(0, 0, 0, 0)
        
        self.step1_cdn_widget = LabeledLineEditWithCopy("Step 1")
        steps_group_layout.addWidget(self.step1_cdn_widget)
        self.step2_cdn_widget = LabeledLineEditWithCopy("Step 2")
        steps_group_layout.addWidget(self.step2_cdn_widget)
        self.step3_cdn_widget = LabeledLineEditWithCopy("Step 3")
        steps_group_layout.addWidget(self.step3_cdn_widget)
        mid_layout.addLayout(steps_group_layout)

        # 分隔线
        separator_mid2 = QFrame()
        separator_mid2.setFrameShape(QFrame.HLine)
        separator_mid2.setFrameShadow(QFrame.Sunken)
        mid_layout.addWidget(separator_mid2)

        # 2.4 Features区域
        features_group_layout = QVBoxLayout()
        features_group_layout.setSpacing(8)
        features_group_layout.setContentsMargins(0, 0, 0, 0)
        
        self.feature1_cdn_widget = LabeledLineEditWithCopy("Feature 1")
        features_group_layout.addWidget(self.feature1_cdn_widget)
        self.feature2_cdn_widget = LabeledLineEditWithCopy("Feature 2")
        features_group_layout.addWidget(self.feature2_cdn_widget)
        self.feature3_cdn_widget = LabeledLineEditWithCopy("Feature 3")
        features_group_layout.addWidget(self.feature3_cdn_widget)
        self.feature4_cdn_widget = LabeledLineEditWithCopy("Feature 4")
        features_group_layout.addWidget(self.feature4_cdn_widget)
        mid_layout.addLayout(features_group_layout)

        # 分隔线
        separator_mid3 = QFrame()
        separator_mid3.setFrameShape(QFrame.HLine)
        separator_mid3.setFrameShadow(QFrame.Sunken)
        mid_layout.addWidget(separator_mid3)
        
        # 分隔线
        separator_mid4 = QFrame()
        separator_mid4.setFrameShape(QFrame.HLine)
        separator_mid4.setFrameShadow(QFrame.Sunken)
        mid_layout.addWidget(separator_mid4)
        
        # 第一行按钮
        mid_buttons_layout1 = QHBoxLayout()
        buttons_row1 = [
            ("Browse Folder", self.browse_folder),
            ("Open Folder", self.open_folder)
        ]
        for text, callback in buttons_row1:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setMinimumHeight(35)
            mid_buttons_layout1.addWidget(btn)
        
        # 添加上传按钮
        mid_buttons_layout2 = QHBoxLayout()
        self.upload_button = QPushButton("Upload")
        self.upload_button.clicked.connect(self.uploader_upload_folder)
        self.upload_button.setMinimumHeight(35)
        mid_buttons_layout2.addWidget(self.upload_button)
        
        mid_layout.addLayout(mid_buttons_layout1)
        mid_layout.addLayout(mid_buttons_layout2)
    
        # 添加弹性空间
        mid_layout.addStretch()
        
        # 3. 右侧面板 - 输出区域
        right_panel = QWidget()
        right_panel.setMinimumWidth(100)
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(8)
        
        # 3.1 输出区域标题和清除按钮
        output_header = QHBoxLayout()
        output_title = QLabel("Program Output")
        output_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; background-color: transparent;")
        output_header.addWidget(output_title)
        
        output_header.addStretch()  # 添加弹性空间
        
        # 3.2 清除按钮放在标题栏右侧
        self.clear_button = QPushButton("Clear Output")
        self.clear_button.setFixedSize(150, 30)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.clear_button.clicked.connect(self.clear_output)
        output_header.addWidget(self.clear_button)
        
        right_layout.addLayout(output_header)
        
        # 3.3 输出框
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setPlaceholderText(
            "Program output will be displayed here...\n\n"
            "• Use BROWSE FOLDER to locate the picture folder\n"
            "• OPEN FOLDER can open the selected folder for inspection\n"
            "• After copying text from Google Docs, click UPDATE to parse\n"
            "• Click GENERATE JSON for final result\n"
            "• Use Clear Output button to reset messages\n"
            "• Use 📋 button to copy the text\n"
            "• If you are on MacOS, make sure you are connected to the NAS server every time you reboot your computer."
        )
        self.output_box.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        
        right_layout.addWidget(self.output_box)
        
        # 4. 将面板添加到主布局
        main_layout.addWidget(left_panel)
        main_layout.addWidget(vertical_separator1)
        main_layout.addWidget(mid_panel)
        main_layout.addWidget(vertical_separator1)
        main_layout.addWidget(right_panel)
        
        # 设置布局比例
        main_layout.setStretch(0, 0)  # 左侧面板固定宽度
        main_layout.setStretch(1, 0)  # 中间面板可拉伸
        main_layout.setStretch(2, 0)  # 右侧面板可拉伸
        
        # 5. 杂项
        self.uploader = ImageUploader()
        self.aws_upload = S3Uploader()
        self.output_json = ""
        
    def clear_output(self):
        """清除输出框内容"""
        self.output_box.clear()

    def add_output_message(self, message, msg_type="info"):
        """Add styled message to output"""
        timestamp = self.current_time()
        
        if msg_type == "info":
            color = "#007AFF"
            icon = "ℹ️"
        elif msg_type == "warning":
            color = "#FF9500"
            icon = "⚠️"
        elif msg_type == "error":
            color = "#FF3B30"
            icon = "❌"
        elif msg_type == "success":
            color = "#34C759"
            icon = "✅"
        else:
            color = "#1D1D1F"
            icon = "•"
        
        formatted_message = f"""
        <div style="margin: 8px 0; padding: 0; border-left: 3px solid {color};">
            <div style="font-weight: 600; color: white; background-color: {color}; padding: 6px 12px; margin-bottom: 4px; border-radius: 4px;">
            {icon} {timestamp}
            </div>
            <div style="color: #1D1D1F; line-height: 1.3; padding: 0 12px;">
            {message}
            </div>
        </div>
        """
        self.output_box.append(formatted_message)
        
        # 自动滚动到底部
        scrollbar = self.output_box.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def browse_folder(self):
        self.add_output_message("Browsing for folder...", "info")
        
        # Set default folder for QFileDialog
        if sys.platform.startswith('darwin'):
            default_folder = "/Volumes/shared/pacdora.com/"
            if not os.path.isdir(default_folder):
                self.add_output_message(f"Cannot reach NAS folder ({default_folder}). Using Desktop instead.", "warning")
                default_folder = os.path.expanduser("~/Desktop")
        else:
            default_folder = "//nas01.tools.baoxiaohe.com/shared/pacdora.com/"
        
        # Check if default folder exists
        if not os.path.isdir(default_folder):
            self.add_output_message(f"Cannot reach default folder ({default_folder}). Using home directory instead.", "warning")
            default_folder = os.path.expanduser("~")
        
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", default_folder)
        if folder:
            self.pics_path_widget.setText(folder)
            self.add_output_message(f"Selected folder: {folder}", "success")
        else:
            self.add_output_message("No folder selected", "warning")
    
    def open_folder(self):
        self.add_output_message("Opening folder...", "info")
        folder_path = self.pics_path_widget.text().strip()
        
        if not folder_path or not os.path.isdir(folder_path):
            self.add_output_message("Please select a valid folder path before opening. Maybe the folder is not created yet. Check the process in notion.", "warning")
            return
        
        try:
            if sys.platform.startswith('darwin'):
                os.system(f'open "{folder_path}"')
            elif os.name == 'nt':
                # Handle UNC paths and convert slashes
                unc_path = folder_path.replace('/', '\\')
                if not unc_path.startswith('\\\\'):
                    if unc_path.startswith('\\'):
                        unc_path = '\\\\' + unc_path.lstrip('\\')
                os.startfile(unc_path)
            elif os.name == 'posix':
                os.system(f'xdg-open "{folder_path}"')
            else:
                self.add_output_message("Unsupported OS for opening folders.", "error")
                return
            
            self.add_output_message(f"Opened folder: {folder_path}", "success")
        except Exception as e:
            self.add_output_message(f"Error opening folder: {e}", "error")

    def update_action(self):
        self.add_output_message("Processing clipboard content...", "info")
        
        clipboard = QGuiApplication.clipboard()
        clipboard_text = clipboard.text()
        cutout_keywords_nextline = ["URL", "Title", "Meta Description", "Breadcrumb"]
        cutout_keywords_currentline = ["View all", "Make a", "Design a", "Create a", "Custom a", "Customize a"]
        
        # 如果剪切板非空
        if clipboard_text:
            preview_start = clipboard_text[:50]
            self.add_output_message(f"Clipboard content captured: {preview_start}...", "info")
            
            # 先解析关键词字段返回到field中
            try:
                dict_parsed1 = extract_cutout_nextline(text=clipboard_text, keywords=cutout_keywords_nextline)
                dict_parse2 = extract_cutout_currentline(text=clipboard_text, keywords=cutout_keywords_currentline)
                
                if dict_parsed1 and dict_parse2:
                    merged = dict_parsed1.copy()
                    merged.update(dict_parse2)
                    # 检查所有关键字段是否为空
                    required_fields = ["URL", "Title", "Meta Description", "Breadcrumb", "View all", "Make a"]
                    empty_fields = [field for field in required_fields if not merged.get(field) or (isinstance(merged.get(field), str) and merged.get(field).strip() == "")]
                    
                    if len(empty_fields) == len(required_fields):
                        self.add_output_message("Parsing failed: All required fields are empty. Please check your input format.", "error")
                    else:
                        self.add_output_message("Article parsed successfully! Keywords detected and extracted.", "success")
                    
                    # 更新界面字段
                    if "URL" in merged:
                        value = merged["URL"]
                        # 判断系统是Windows还是Mac
                        if sys.platform.startswith('darwin'):
                            self.pics_path_widget.setText(f"/Volumes/shared/pacdora.com/{value}" if isinstance(value, str) else ", ".join(map(str, value)))
                        elif os.name == 'nt':
                            self.pics_path_widget.setText(f"//nas01.tools.baoxiaohe.com/shared/pacdora.com/{value}" if isinstance(value, str) else ", ".join(map(str, value)))
                        else:
                            self.add_output_message(f"Detected system: {sys.platform}", "info")
                        self.file_path_widget.setText(value if isinstance(value, str) else ", ".join(map(str, value)))

                    if "Title" in merged:
                        value = merged["Title"]
                        self.title_widget.setText(value if isinstance(value, str) else ", ".join(map(str, value)))
                    if "Meta Description" in merged:
                        value = merged["Meta Description"]
                        self.description_widget.setText(value if isinstance(value, str) else ", ".join(map(str, value)))
                    if "Breadcrumb" in merged:
                        value = merged["Breadcrumb"]
                        self.keywords_widget.setText(value if isinstance(value, str) else ", ".join(map(str, value)))
                    if "View all" in merged:
                        value = merged["View all"]
                        self.view_widget.setText(value if isinstance(value, str) else ", ".join(map(str, value)))
                    if "Make a" in merged:
                        value = merged["Make a"]
                        # 如果"Make a"为空白，尝试用"Design a"或"Create a"中的非空值替代
                        if (not value or (isinstance(value, str) and value.strip() == "")):
                            if "Design a" in merged and merged["Design a"] and (not isinstance(merged["Design a"], str) or merged["Design a"].strip() != ""):
                                value = merged["Design a"]
                            elif "Create a" in merged and merged["Create a"] and (not isinstance(merged["Create a"], str) or merged["Create a"].strip() != ""):
                                value = merged["Create a"]
                            elif "Custom a" in merged and merged["Custom a"] and (not isinstance(merged["Custom a"], str) or merged["Custom a"].strip() != ""):
                                value = merged["Custom a"]
                            elif "Customize a" in merged and merged["Customize a"] and (not isinstance(merged["Customize a"], str) or merged["Customize a"].strip() != ""):
                                value = merged["Customize a"]
                        self.try_widget.setText(value if isinstance(value, str) else ", ".join(map(str, value)))
                else:
                    self.add_output_message("Parsing failed: No keywords detected. Please ensure you've copied the correct article. This could happen when the article is not correctly formatted. Go check it.", "error")
                
                # 补齐文件夹
                folder_path = self.pics_path_widget.text()
                self.ensure_folder_exists(folder_path=folder_path)
                
                # 判断是否存在cdn
                cdn_records_exist = self.detect_cdn_records(folder_path=folder_path)
                if cdn_records_exist:
                    self.pass_cdn_records()
                    self.add_output_message("Detected cdn records, auto fill.","succcess")
                
            except Exception as e:
                self.add_output_message(f"Error parsing content: {e}", "error")
            
            # 解析本文，验证是否正确
            try:
                self.segments = segment(clipboard_text)
                self.add_output_message(f"Text segmented into {len(self.segments)} parts.", "info")
                if len(self.segments) != 8:
                    self.add_output_message("Wrong number of segments: The number of segments is not 8. Please check the input text. Maybe you added the wrong number of #. There should be 7 of them.", "error")
                else:
                    self.add_output_message("Text segmented successfully.", "success")
                    
                    
            except Exception as e:
                self.add_output_message(f"Error segmenting text: {e}", "error")
        
        # 如果剪切板为空      
        else:
            self.add_output_message("Clipboard is empty or does not contain text.", "warning")
        
    def generate_json_action(self):
        self.add_output_message("Generating JSON output...", "info")
        
        # Check if all required fields are filled
        required_fields = [
            (self.pics_path_widget.text().strip(), "Pictures Path"),
        ]
        
        missing_fields = [field_name for field_value, field_name in required_fields if not field_value]
        
        if missing_fields:
            self.add_output_message(f"Missing required fields: {', '.join(missing_fields)}", "warning")
            return
        
        # 获取关键字段
        view_text = self.view_widget.text().split(":")[0].strip()
        view_link_raw = self.view_widget.text().split(":")[1].strip()
        view_link_spicy = f":{view_link_raw}"
        view_link = view_link_spicy
        
        try_text = self.try_widget.text().split(":")[0].strip()
        try_link_raw = self.try_widget.text().split(":")[1].strip() 
        try_link_spicy = f":{try_link_raw}"
        try_link = try_link_spicy
        
        breadcrumb = self.keywords_widget.text()
        breadcrumb_lower = breadcrumb.title()
        
        part2 = self.segments[1]
        part2_text = part2.splitlines()[1]
        
        mockup_list_1_name = ''
        mockup_list_1_number = ''
        mockup_list_1_cdn = ''
        
        mockup_list_2_number = ''
        mockup_list_2_cdn = ''
        
        if self.single_image_checkbox.isChecked():
            multiple_upload = 'true'
        else:
            multiple_upload = 'false'

        if self.scroll_to_mockup_checkbox.isChecked():
            more_link = '#mockup-display' 
        else:
            more_link = ''
            
        if self.color_diy_checkbox.isChecked():
            cover_colors = 'true'
        else:
            cover_colors = 'false'
        
        part3 = self.segments[2].splitlines()
        part3_title = part3[0]
        part3_text = part3[1]
        
        # 样机展示链接
        part4 = self.segments[3].splitlines()
        part4_title = part4[0]
        
        # 检查是否存在 var.json，如果有则读取，否则fetch并写入
        var_json_path = os.path.join(self.pics_path_widget.text(), "var_v.json")
        if os.path.exists(var_json_path):
            self.add_output_message("Found var_v.json file. Reading mockup details.", "info")
            with open(var_json_path, "r", encoding="utf-8") as f:
                var_json_data = json.load(f)
            model_1_name = var_json_data["model_1"]["name"]
            model_1_image_url = var_json_data["model_1"]["image_url"]
            model_1_editor_inner_link = var_json_data["model_1"]["editor_inner_link"]
            model_2_name = var_json_data["model_2"]["name"]
            model_2_image_url = var_json_data["model_2"]["image_url"]
            model_2_editor_inner_link = var_json_data["model_2"]["editor_inner_link"]
            model_3_name = var_json_data["model_3"]["name"]
            model_3_image_url = var_json_data["model_3"]["image_url"]
            model_3_editor_inner_link = var_json_data["model_3"]["editor_inner_link"]
            model_4_name = var_json_data["model_4"]["name"]
            model_4_image_url = var_json_data["model_4"]["image_url"]
            model_4_editor_inner_link = var_json_data["model_4"]["editor_inner_link"]
            model_5_name = var_json_data["model_5"]["name"]
            model_5_image_url = var_json_data["model_5"]["image_url"]
            model_5_editor_inner_link = var_json_data["model_5"]["editor_inner_link"]
            model_6_name = var_json_data["model_6"]["name"]
            model_6_image_url = var_json_data["model_6"]["image_url"]
            model_6_editor_inner_link = var_json_data["model_6"]["editor_inner_link"]
            model_7_name = var_json_data["model_7"]["name"]
            model_7_image_url = var_json_data["model_7"]["image_url"]
            model_7_editor_inner_link = var_json_data["model_7"]["editor_inner_link"]
            model_8_name = var_json_data["model_8"]["name"]
            model_8_image_url = var_json_data["model_8"]["image_url"]
            model_8_editor_inner_link = var_json_data["model_8"]["editor_inner_link"]
        else:
            urls = extract_url(part4)
            model_1_name, model_1_image_url, model_1_editor_inner_link = fetch_mockup_details(urls[0])
            model_2_name, model_2_image_url, model_2_editor_inner_link = fetch_mockup_details(urls[1])
            model_3_name, model_3_image_url, model_3_editor_inner_link = fetch_mockup_details(urls[2])
            model_4_name, model_4_image_url, model_4_editor_inner_link = fetch_mockup_details(urls[3])
            model_5_name, model_5_image_url, model_5_editor_inner_link = fetch_mockup_details(urls[4])
            model_6_name, model_6_image_url, model_6_editor_inner_link = fetch_mockup_details(urls[5])
            model_7_name, model_7_image_url, model_7_editor_inner_link = fetch_mockup_details(urls[6])
            model_8_name, model_8_image_url, model_8_editor_inner_link = fetch_mockup_details(urls[7])
            # 写入 var.json
            var_json_data = {
            "model_1": {
                "name": model_1_name,
                "image_url": model_1_image_url,
                "editor_inner_link": model_1_editor_inner_link
            },
            "model_2": {
                "name": model_2_name,
                "image_url": model_2_image_url,
                "editor_inner_link": model_2_editor_inner_link
            },
            "model_3": {
                "name": model_3_name,
                "image_url": model_3_image_url,
                "editor_inner_link": model_3_editor_inner_link
            },
            "model_4": {
                "name": model_4_name,
                "image_url": model_4_image_url,
                "editor_inner_link": model_4_editor_inner_link
            },
            "model_5": {
                "name": model_5_name,
                "image_url": model_5_image_url,
                "editor_inner_link": model_5_editor_inner_link
            },
            "model_6": {
                "name": model_6_name,
                "image_url": model_6_image_url,
                "editor_inner_link": model_6_editor_inner_link
            },
            "model_7": {
                "name": model_7_name,
                "image_url": model_7_image_url,
                "editor_inner_link": model_7_editor_inner_link
            },
            "model_8": {
                "name": model_8_name,
                "image_url": model_8_image_url,
                "editor_inner_link": model_8_editor_inner_link
            }
            }
            with open(var_json_path, "w", encoding="utf-8") as f:
                json.dump(var_json_data, f, ensure_ascii=False, indent=2)
            self.add_output_message("Fetched mockup details and wrote var_v.json.", "success")
        
        step1_cdn = self.step1_cdn_widget.text()
        step2_cdn = self.step2_cdn_widget.text()
        step3_cdn = self.step3_cdn_widget.text()
        
        part5 = [line for line in self.segments[4].splitlines() if line.strip()]
        part5_title = part5[0]
        part5_step1_a = part5[1]
        part5_step1_b = part5[2]
        
        part5_step2_a = part5[3]
        part5_step2_b = part5[4]
        
        part5_step3_a = part5[5]
        part5_step3_b = part5[6]
        
        
        part6 = self.segments[5].splitlines()
        part6_1_feature_cdn = self.feature1_cdn_widget.text()
        part6_2_feature_cdn = self.feature2_cdn_widget.text()
        part6_3_feature_cdn = self.feature3_cdn_widget.text()
        part6_4_feature_cdn = self.feature4_cdn_widget.text()
        
        part6_title = part6[0]
        
        part6_1_title = part6[1]
        part6_1_a = part6[2]
        part6_1_b = part6[3]
        
        part6_2_title = part6[5]
        part6_2_a = part6[6]
        part6_2_b = part6[7]
        
        part6_3_title = part6[9]
        part6_3_a = part6[10]
        part6_3_b = part6[11]
        
        part6_4_title = part6[13]
        part6_4_a = part6[14]
        part6_4_b = part6[15]
        
        # FAQ环节
        part7 = self.segments[6]
        part7_block = parse_faq_text(part7)
        
        part7_q1 = part7_block[0]['question']
        part7_a1 = part7_block[0]['answer']
        
        part7_q2 = part7_block[1]['question']
        part7_a2 = part7_block[1]['answer']
        
        part7_q3 = part7_block[2]['question']
        part7_a3 = part7_block[2]['answer']
        
        part7_q4 = part7_block[3]['question']
        part7_a4 = part7_block[3]['answer']
        
        part7_q5 = part7_block[4]['question']
        part7_a5 = part7_block[4]['answer']
        
        part8_text = self.segments[7].splitlines()[0]
        
        folder_path = self.pics_path_widget.text()
        self.ensure_folder_exists(folder_path = folder_path)
        
        # 读取模板内容
        with open('temp.json', 'r', encoding='utf-8') as f:
            template_str = f.read()

        # 构建替换字典
        replace_dict = {
            "view_text": view_text,
            "view_link": view_link,
            "make_text": try_text,
            "make_link": try_link,
            "breadcrumb": breadcrumb,
            "breadcrumb_lower": breadcrumb_lower,
            "part2_text": part2_text,
            "mockup_list_1_name": mockup_list_1_name,
            "mockup_list_1_number": mockup_list_1_number,
            "mockup_list_1_cdn": mockup_list_1_cdn,
            "mockup_list_2_number": mockup_list_2_number,
            "mockup_list_2_cdn": mockup_list_2_cdn, 
            "multiple_upload": multiple_upload,
            "cover_colors": cover_colors,
            "more_link": more_link,
            "part3_title": part3_title,
            "part3_text": part3_text,
            "part4_title": part4_title,
            "model_1_image_url": model_1_image_url,
            "model_1_name": model_1_name,
            "model_1_editor_inner_link": model_1_editor_inner_link,
            "model_2_image_url": model_2_image_url,
            "model_2_name": model_2_name,
            "model_2_editor_inner_link": model_2_editor_inner_link,
            "model_3_image_url": model_3_image_url,
            "model_3_name": model_3_name,
            "model_3_editor_inner_link": model_3_editor_inner_link,
            "model_4_image_url": model_4_image_url,
            "model_4_name": model_4_name,
            "model_4_editor_inner_link": model_4_editor_inner_link,
            "model_5_image_url": model_5_image_url,
            "model_5_name": model_5_name,
            "model_5_editor_inner_link": model_5_editor_inner_link,
            "model_6_image_url": model_6_image_url,
            "model_6_name": model_6_name,
            "model_6_editor_inner_link": model_6_editor_inner_link,
            "model_7_image_url": model_7_image_url,
            "model_7_name": model_7_name,
            "model_7_editor_inner_link": model_7_editor_inner_link,
            "model_8_image_url": model_8_image_url,
            "model_8_name": model_8_name,
            "model_8_editor_inner_link": model_8_editor_inner_link,
            "step1_cdn": step1_cdn,
            "step2_cdn": step2_cdn,
            "step3_cdn": step3_cdn,
            "part5_title": part5_title,
            "part5_step1_a": part5_step1_a,
            "part5_step1_b": part5_step1_b,
            "part5_step2_a": part5_step2_a,
            "part5_step2_b": part5_step2_b,
            "part5_step3_a": part5_step3_a,
            "part5_step3_b": part5_step3_b,
            "part6_title": part6_title,
            "part6_1_title": part6_1_title,
            "part6_1_feature_cdn": part6_1_feature_cdn,
            "part6_1_a": part6_1_a,
            "part6_1_b": part6_1_b,
            "part6_2_title": part6_2_title,
            "part6_2_feature_cdn": part6_2_feature_cdn,
            "part6_2_a": part6_2_a,
            "part6_2_b": part6_2_b,
            "part6_3_title": part6_3_title,
            "part6_3_feature_cdn": part6_3_feature_cdn,
            "part6_3_a": part6_3_a,
            "part6_3_b": part6_3_b,
            "part6_4_title": part6_4_title,
            "part6_4_feature_cdn": part6_4_feature_cdn,
            "part6_4_a": part6_4_a,
            "part6_4_b": part6_4_b,
            "part7_q1": part7_q1,
            "part7_a1": part7_a1,
            "part7_q2": part7_q2,
            "part7_a2": part7_a2,
            "part7_q3": part7_q3,
            "part7_a3": part7_a3,
            "part7_q4": part7_q4,
            "part7_a4": part7_a4,
            "part7_q5": part7_q5,
            "part7_a5": part7_a5,
            "part8_text": part8_text,
        }

        # 替换所有{{key}}为对应值
        for key, value in replace_dict.items():
            template_str = template_str.replace(f"{{{{{key}}}}}", str(value))

        # 尝试解析为json
        try:
            json_obj = json.loads(template_str)
            json_string = json.dumps(json_obj, indent=2, ensure_ascii=False)
            self.json_widget.setText(json_string)
            self.output_json = json_string
            QGuiApplication.clipboard().setText(json_string)
            self.add_output_message("JSON generated and copied to clipboard!", "success")
        except Exception as e:
            self.add_output_message(f"Error generating JSON: {e}", "error")
            
        
            

    def current_time(self):
        return datetime.now().strftime("%H:%M:%S")
    
    def uploader_activate(self):
        self.add_output_message("Activating the automator. This could take a while.","info")
        self.add_output_message("If you are using the app for the first time, log in manually.","info")
        _ = self.uploader.activate()
        if _:
            self.add_output_message(f"Something went wrong during activation: {_}","error")
        elif self.uploader.activated_status:
            self.add_output_message("The upload automator is activated.","success")
            
    def ensure_folder_exists(self, folder_path):
        """
        Note for dev: os version was already ensured. 
        """
        folder_path = self.pics_path_widget.text()
        # if no folder exist, add one
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            self.add_output_message(f"No folder detected. Created folder automatically.","info")
        # if yes, pass
        
    def detect_var_records(self,folder_path) -> bool:
        """
        see if a var_v.json are stored in nas pics folder
        """
        # detect if a var_v.json exists in the folder_path folder
        if os.path.exists(f"{folder_path}//var_v.json"):
            self.add_output_message(f"Found cdn.json file. Reading records.","info")
            return True
        # if no, pass
        else: 
            return False
        
    def detect_cdn_records(self,folder_path) -> bool:
        """
        see if cdn adresses are already stored in nas pics folder
        """
        # detect if a cdn.json exists in the folder_path folder
        if os.path.exists(f"{folder_path}//cdn.json"):
            self.add_output_message(f"Found cdn.json file. Reading records.","info")
            return True
        # if no, pass
        else: 
            return False
        
    def pass_cdn_records(self):
        folder_path = self.pics_path_widget.text()
        with open(f"{folder_path}//cdn.json","r") as f:
            cdn_json = json.load(f)
        # 提取json中的每一行内容并赋入widget
        self.cover_cdn_widget.setText(cdn_json["cover_cdn"])
        self.cover_more_cdn_widget.setText(cdn_json["cover_more_cdn"])
        self.step1_cdn_widget.setText(cdn_json["step1_cdn"])
        self.step2_cdn_widget.setText(cdn_json["step2_cdn"])
        self.step3_cdn_widget.setText(cdn_json["step3_cdn"])
        self.feature1_cdn_widget.setText(cdn_json["feature1_cdn"])
        self.feature2_cdn_widget.setText(cdn_json["feature2_cdn"])
        self.feature3_cdn_widget.setText(cdn_json["feature3_cdn"])
        self.feature4_cdn_widget.setText(cdn_json["feature4_cdn"])
        
        self.add_output_message("Passing completed.","success")
           
    def uploader_upload_folder(self):
        folder_path = self.pics_path_widget.text()
        self.ensure_folder_exists(folder_path=folder_path)
        if self.detect_cdn_records(folder_path=folder_path): # already uploaded and recorded
            self.add_output_message("already uploaded","info")
            self.pass_cdn_records()
            self.add_output_message("Passing recorded cdn addresses.","success")
        else: # no records
            self.add_output_message("Uploading images for the first time, this could take a while.","info")
            # 获取文件夹内所有图片
            image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
            
            # 用于存储CDN链接的字典
            cdn_links = {}
            
            total_images = len(image_files)
            current_image = 0
            
            for image in image_files:
                # 上传图片并获取CDN链接
                file_path = os.path.join(folder_path, image)
                cdn_url = self.aws_upload.upload_file(file_path)
                current_image += 1
                self.add_output_message(f"Uploading image {current_image}/{total_images}: {image}", "info")
                
                # 获取文件名（不含扩展名）
                filename = os.path.splitext(image)[0]
                
                # 根据文件名分配CDN链接
                if filename in ['1', '2', '3']:
                    step_num = int(filename)
                    if step_num == 1:
                        self.step1_cdn_widget.setText(cdn_url)
                        cdn_links['step1_cdn'] = cdn_url
                    elif step_num == 2:
                        self.step2_cdn_widget.setText(cdn_url)
                        cdn_links['step2_cdn'] = cdn_url
                    elif step_num == 3:
                        self.step3_cdn_widget.setText(cdn_url)
                        cdn_links['step3_cdn'] = cdn_url
                    
                elif filename in ['a', 'b', 'c', 'd']:
                    feature_num = {'a': 1, 'b': 2, 'c': 3, 'd': 4}[filename]
                    if feature_num == 1:
                        self.feature1_cdn_widget.setText(cdn_url)
                        cdn_links['feature1_cdn'] = cdn_url
                    elif feature_num == 2:
                        self.feature2_cdn_widget.setText(cdn_url)
                        cdn_links['feature2_cdn'] = cdn_url
                    elif feature_num == 3:
                        self.feature3_cdn_widget.setText(cdn_url)
                        cdn_links['feature3_cdn'] = cdn_url
                    elif feature_num == 4:
                        self.feature4_cdn_widget.setText(cdn_url)
                        cdn_links['feature4_cdn'] = cdn_url
            
            # 定义cdn模板
            template = {
                "cover_cdn": "",
                "cover_more_cdn": "",
                "step1_cdn": "",
                "step2_cdn": "",
                "step3_cdn": "",
                "feature1_cdn": "",
                "feature2_cdn": "",
                "feature3_cdn": "",
                "feature4_cdn": ""
            }
            
            # 将上传的cdn链接更新到模板中
            merged_data = template.copy()  # 创建template的副本
            merged_data.update(cdn_links)  # 使用update方法合并两个字典
            
            # 保存更新后的JSON文件
            json_path = os.path.join(folder_path, 'cdn.json')
            with open(json_path, 'w') as f:
                json.dump(merged_data, f, indent=4)
                
            self.add_output_message(f"All cdn addresses recorded at {json_path}", "success")
            

            
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 应用Material主题
    apply_stylesheet(app, theme='light_orange.xml')  # 使用Material主题

    window = WSA()
    window.show()
    sys.exit(app.exec())