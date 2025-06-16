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
from utils.parse import extract_cutout_nextline, extract_cutout_currentline, segment
from PySide6.QtCore import QTimer

class LabeledLineEditWithCopy(QWidget):
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
        
        # JSON
        self.json_widget = LabeledLineEditWithCopy("JSON", "Click button on the right to copy")
        left_layout.addWidget(self.json_widget)
        
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
        
        self.cover1_cdn_widget = LabeledLineEditWithCopy("Cover", placeholder="Cover封面")
        cover_group_layout.addWidget(self.cover1_cdn_widget)
        self.cover2_cdn_widget = LabeledLineEditWithCopy("Cover more", placeholder="More封面")
        cover_group_layout.addWidget(self.cover2_cdn_widget)
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
        
        # 添加Notion地址
        self.notion_url_widget = LabeledLineEditWithCopy("Notion URL")
        mid_layout.addWidget(self.notion_url_widget)
        
        # 添加Slack表格地址
        self.slack_url_widget = LabeledLineEditWithCopy("Slack URL")
        mid_layout.addWidget(self.slack_url_widget)
        
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
        
        # 添加Activate按钮
        mid_buttons_layout2 = QHBoxLayout()
        
        self.activate_button = QPushButton("Activate")
        self.activate_button.setMinimumHeight(35)
        mid_buttons_layout2.addWidget(self.activate_button)

        # 添加Upload按钮
        self.upload_button = QPushButton("Upload")
        self.upload_button.setMinimumHeight(35)
        mid_buttons_layout2.addWidget(self.upload_button)
        
        mid_layout.addLayout(mid_buttons_layout1)
        mid_layout.addLayout(mid_buttons_layout2)
        
        # 添加退出按钮
        self.quit_button = QPushButton("Quit")
        self.quit_button.setMinimumHeight(35)
        mid_layout.addWidget(self.quit_button)

        # 添加弹性空间
        mid_layout.addStretch()
        
        # 3. 右侧面板 - 输出区域
        right_panel = QWidget()
        right_panel.setMinimumWidth(100)
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(8)
        
        # 输出区域标题和清除按钮
        output_header = QHBoxLayout()
        output_title = QLabel("Program Output")
        output_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; background-color: transparent;")
        output_header.addWidget(output_title)
        
        output_header.addStretch()  # 添加弹性空间
        
        # 清除按钮放在标题栏右侧
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
        
        # 输出框
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
        
        # 将面板添加到主布局
        main_layout.addWidget(left_panel)
        main_layout.addWidget(vertical_separator1)
        main_layout.addWidget(mid_panel)
        main_layout.addWidget(vertical_separator1)
        main_layout.addWidget(right_panel)
        
        # 设置布局比例
        main_layout.setStretch(0, 0)  # 左侧面板固定宽度
        main_layout.setStretch(1, 0)  # 中间面板可拉伸
        main_layout.setStretch(2, 0)  # 右侧面板可拉伸
        
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
        cutout_keywords_currentline = ["View all", "Make a", "Design a", "Create a"]
        
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
                        self.try_widget.setText(value if isinstance(value, str) else ", ".join(map(str, value)))
                else:
                    self.add_output_message("Parsing failed: No keywords detected. Please ensure you've copied the correct article. This could happen when the article is not correctly formatted. Go check it.", "error")
            except Exception as e:
                self.add_output_message(f"Error parsing content: {e}", "error")
            
            # 再解析本文，验证是否正确，最终返回json
            try:
                segments = segment(clipboard_text)
                self.add_output_message(f"Text segmented into {len(segments)} parts.", "info")
                if len(segments) != 8:
                    self.add_output_message("Wrong number of segments: The number of segments is not 8. Please check the input text. Maybe you added the wrong number of #. There should be 7 of them.", "error")
                else:
                    self.add_output_message("Text segmented successfully.", "success")
                    json = 'json'
                    self.add_output_message(f"Generating JSON", "info")
                    json_string = json.dumps(json, indent=2, ensure_ascii=False)
                    QGuiApplication.clipboard().setText(json_string)
                    self.add_output_message("JSON copied to clipboard!", "success")
                    
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
        
        # 生成JSON数据
        json_data = {
            "type": self.page_type.currentText(),
            "pics_path": self.pics_path_widget.text().strip(),
            "file_path": self.file_path_widget.text(),
            "title": self.title_widget.text(),
            "description": self.description_widget.text(),
            "keywords": self.keywords_widget.text(),
            "view": self.view_widget.text(),
            "try": self.try_widget.text()
        }
        
        try:
            import json
            json_string = json.dumps(json_data, indent=2, ensure_ascii=False)
            self.json_widget.setText(json_string)
            self.add_output_message(f"Generated JSON", "info")
        except Exception as e:
            self.add_output_message(f"Generation failed: {e}", "error")

    def current_time(self):
        return datetime.now().strftime("%H:%M:%S")
        
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 应用Material主题
    apply_stylesheet(app, theme='light_orange.xml')  # 使用Material主题

    window = WSA()
    window.show()
    sys.exit(app.exec())