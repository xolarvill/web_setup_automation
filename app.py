# 标准库导入
import os
import sys
import json
import re
from datetime import datetime
import random
import webbrowser
from typing import Callable

# 第三方库导入
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QFileDialog, QTextEdit,
    QFrame, QCheckBox, QSizePolicy, QToolButton, QScrollArea, QStyle,
    QDialog, QDialogButtonBox, QFormLayout, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt, QTimer, QSize, QParallelAnimationGroup, QPropertyAnimation, QAbstractAnimation, QPoint, QSequentialAnimationGroup, Signal
from PySide6.QtGui import QClipboard, QIcon, QGuiApplication
from qt_material import apply_stylesheet # type: ignore

# 本地模块导入
# 解析文本
from utils.parse import (
    extract_url, segment, parse_faq_text, extract_structured_fields,
    parse_size_csv, process_text_with_links
)
# 获取样机信息
from utils.fetch_mockup_details import fetch_mockup_details
# 图片上传
from utils.upload_boto import S3Uploader
from utils.upload_selenium_class import ImageUploader
# 无图可用时的占位图
from utils.cdn_placeholder_image import cdn_placeholder_image
# 生成tools页面json
from utils.tools_generator import generate_tools_json
# 解耦的UI组件
from ui.collapsible_tab import CollapsibleBox, HorizontalCollapsibleTabs
from ui.label_input import LabeledLineEditWithCopy
# 打包应用后无法读取文件必须要设立一个读取函数
from utils.resource_manager import get_writable_path, get_resource_path
# 更新JSON文件的具体动作
from utils.update_json_action import update_login_requirment, update_old_resource_page, iterate
# AWS和LLM API管理器
from utils.credentials import SCConfigDialog
# 文本模式分析器
from utils.string_action import StringPatternTransformer
# 批量处理机器人
from dp_bot import BatchJsonTaskBot
from dp_bot_manager import BotFactory, ModularBatchBot, GuiInteractionHandler
import glob

class WSA(QMainWindow):
    # 自定义信号，用于跨线程更新UI
    log_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web Setup Automation")
        self.setMinimumSize(1350, 820)  # 增加最小窗口大小
        self.setWindowIcon(QIcon("resources/icon.png"))  # 可选：添加图标文件
        self.segments = []

        # 连接信号到槽函数
        self.log_signal.connect(self.update_output_box)

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
        # left_layout.addWidget(left_title_label)

        # 1.1 first group，因为没有命名的必要
        first_group_layout = QVBoxLayout()
        
        first_group_button_layout = QHBoxLayout()
        # 预处理按理，按照剪切板中的标题名，确保在NAS中对应的文件夹们存在
        self.prepare_folder_button = QPushButton("Prepare Folders")
        self.prepare_folder_button.clicked.connect(self.prepare_folder)
        self.prepare_folder_button.setMinimumHeight(35)
        first_group_button_layout.addWidget(self.prepare_folder_button)
        
        self.it_is_a_button_for_fun = QPushButton("有点意思")
        self.it_is_a_button_for_fun.setToolTip("彩蛋")
        self.it_is_a_button_for_fun.setMinimumHeight(35)
        self.it_is_a_button_for_fun.clicked.connect(self.on_fun_button_clicked)
        first_group_button_layout.addWidget(self.it_is_a_button_for_fun)
        
        first_group_layout.addLayout(first_group_button_layout)
        
        # Page Type下拉菜单
        # 单独定义Page Type选项，在一个Hbox里放label + Combobox
        page_type_layout = QHBoxLayout()
        page_label = QLabel("Type:")
        page_label.setMinimumWidth(100)
        self.page_type = QComboBox()
        # 添加 Mockup 组
        self.page_type.addItems([
            "Mockup tool",
            "Mockup resource",
            "Mockup universal topic",
            "Mockup landing page"
        ])
        # 插入分隔线
        self.page_type.insertSeparator(self.page_type.count())
        
        # 添加 Dieline 组
        self.page_type.addItems([
            "Dieline tool",
            "Dieline resource",
            "Dieline universal topic",
            "Dieline landing page"
        ])
        # 插入分隔线
        self.page_type.insertSeparator(self.page_type.count())

        # 添加最后的项
        self.page_type.addItems([
            "TOOLS"
        ])
        self.page_type.setCurrentIndex(0)
        self.page_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        page_type_layout.addWidget(page_label)
        page_type_layout.addWidget(self.page_type)
        first_group_layout.addLayout(page_type_layout)

        # Add a container for the TOOLS-specific widgets
        self.tools_options_widget = QWidget()
        tools_options_layout = QVBoxLayout(self.tools_options_widget)
        tools_options_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tools_csv_path_widget = LabeledLineEditWithCopy("Tools CSV Path")
        browse_csv_button = QPushButton("Browse")
        browse_csv_button.clicked.connect(self.browse_tools_csv)
        
        tools_csv_layout = QHBoxLayout()
        tools_csv_layout.addWidget(self.tools_csv_path_widget)
        tools_csv_layout.addWidget(browse_csv_button)
        tools_options_layout.addLayout(tools_csv_layout)
        
        first_group_layout.addWidget(self.tools_options_widget)

        # Connect the page_type signal to a handler
        self.page_type.currentIndexChanged.connect(self.on_page_type_changed)
        # Initial check
        self.on_page_type_changed()

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
        
        self.color_diy_checkbox = QCheckBox("颜色自定义")
        self.color_diy_checkbox.setChecked(True)
        checkbox_layout.addWidget(self.color_diy_checkbox)
        
        self.color_label_diy_checkbox = QCheckBox("颜色标签自定义")
        self.color_label_diy_checkbox.setChecked(False)
        checkbox_layout.addWidget(self.color_label_diy_checkbox)
    
        # 1.3 DOM相关选项
        mockup_list_layout = QVBoxLayout()
        self.mockup_list_1_name_widget = LabeledLineEditWithCopy("Cover name")
        mockup_list_layout.addWidget(self.mockup_list_1_name_widget)
        self.mockup_list_1_number_widget = LabeledLineEditWithCopy("Cover #")
        mockup_list_layout.addWidget(self.mockup_list_1_number_widget)
        self.mockup_list_2_number_widget = LabeledLineEditWithCopy("Cover more #")
        mockup_list_layout.addWidget(self.mockup_list_2_number_widget)
        
        # More按钮跳转
        self.more_button_action_widget = LabeledLineEditWithCopy("More跳转")
        self.more_button_action_widget.setText("#mockup-display") # 默认跳转到样机展示区
        
        # 自定义颜色输入选项
        self.color_diy_choice_widget = LabeledLineEditWithCopy("颜色自定义", "输入HEX颜色代码，例如#FFFFFF")
        self.color_diy_choice_widget.setText("#FFFFFF")  # 默认颜色
        
        # Create a new HorizontalCollapsibleTabs for the DOM options
        dom_options_tabs = HorizontalCollapsibleTabs(parent=self, parent_window=self, tab_height=35)

        # Create the first collapsible box for "其他DOM选项"
        other_dom_options_box = QWidget()
        other_dom_options_layout = QVBoxLayout(other_dom_options_box)
        
        self.color_label_diy_choice_widget = LabeledLineEditWithCopy("颜色标签", "输入颜色标签，例如Label color，注意首字母大写")
        self.mockup_type_widget = LabeledLineEditWithCopy("Mockup类型","例如Mockup, Box, Customize...")
        self.mockup_type_widget.setText("Mockup")
        self.dieline_choose_widget = LabeledLineEditWithCopy("Dieline", """例如["F1","F2"]""") # New widget
        
        other_dom_options_layout.addWidget(self.color_label_diy_choice_widget)
        other_dom_options_layout.addWidget(self.mockup_type_widget)
        other_dom_options_layout.addWidget(self.dieline_choose_widget)
        
        dom_options_tabs.add_tab("其他DOM选项", other_dom_options_box)

        # Create the second collapsible box for "尺寸相关选项"
        size_options_box = QWidget()
        size_options_layout = QVBoxLayout(size_options_box)

        self.mockup_size_widget = LabeledLineEditWithCopy("DOM尺寸","输入DOM尺寸，如[[1,1,1],[2,2,2],[3,3,3]]")
        self.mockup_default_size_widget = LabeledLineEditWithCopy("默认尺寸","选择第几个尺寸作为默认选项，如2")

        mockup_size_type_layout = QHBoxLayout()
        mockup_size_type_label = QLabel("Size类型:")
        mockup_size_type_label.setMinimumWidth(100)
        self.mockup_type_combo = QComboBox()
        self.mockup_type_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        mockup_size_type_layout.addWidget(mockup_size_type_label)
        mockup_size_type_layout.addWidget(self.mockup_type_combo)

        size_options_layout.addWidget(self.mockup_size_widget)
        size_options_layout.addWidget(self.mockup_default_size_widget)
        size_options_layout.addLayout(mockup_size_type_layout)
        
        dom_options_tabs.add_tab("尺寸相关选项", size_options_box)

        left_layout.addLayout(checkbox_layout)
        left_layout.addLayout(mockup_list_layout)
        left_layout.addWidget(self.more_button_action_widget)
        left_layout.addWidget(self.color_diy_choice_widget)
        left_layout.addWidget(dom_options_tabs) # Add the new tabs widget

        


        # 分隔section输出栏
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(separator1)
        
        # 1.4 浏览器页面设置相关字段
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
        
        separatora = QFrame()
        separatora.setFrameShape(QFrame.HLine)
        separatora.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(separatora)
        
        # Create the new HorizontalCollapsibleTabs widget
        advanced_options_tabs = HorizontalCollapsibleTabs(parent=self, parent_window=self, tab_height=35)

        # Create and populate the "Landing Page" tab
        landing_page_content = QWidget()
        landing_page_layout = QVBoxLayout(landing_page_content)
        self.h1_title_widget = LabeledLineEditWithCopy("H1标题")
        landing_page_layout.addWidget(self.h1_title_widget)
        self.h1_text_widget = LabeledLineEditWithCopy("H1文案")
        landing_page_layout.addWidget(self.h1_text_widget)
        self.whole_page_background_color_widget = LabeledLineEditWithCopy("页面配色", placeholder="形如rgba(123,345,789,1)")
        landing_page_layout.addWidget(self.whole_page_background_color_widget)
        advanced_options_tabs.add_tab("落地页管理", landing_page_content)

        # Create and populate the "Discover/Explore" tab
        bot_and_others = QWidget()
        bot_and_others_layout = QVBoxLayout(bot_and_others)
        self.bot_and_others_panel_button = QPushButton("Bot and others")
        self.bot_and_others_panel_button.clicked.connect(self.bot_and_others_panel)
        self.bot_and_others_panel_button.setMinimumHeight(35)
        bot_and_others_layout.addWidget(self.bot_and_others_panel_button)
        advanced_options_tabs.add_tab("Bot and others", bot_and_others)

        left_layout.addWidget(advanced_options_tabs)
        
        # 添加弹性空间
        left_layout.addStretch()
        
        # 垂直分隔线
        vertical_separator1 = QFrame()
        vertical_separator1.setFrameShape(QFrame.VLine)
        vertical_separator1.setFrameShadow(QFrame.Sunken)

        vertical_separator2 = QFrame()
        vertical_separator2.setFrameShape(QFrame.VLine)
        vertical_separator2.setFrameShadow(QFrame.Sunken)
        
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
        
        self.manual_aws_configure_widget = QPushButton('SC CONFIGURE')
        self.manual_aws_configure_widget.setMinimumHeight(35)
        self.manual_aws_configure_widget.clicked.connect(self.manual_secret_configure)
        mid_layout.addWidget(self.manual_aws_configure_widget)
        
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
        
        mid_layout.addLayout(mid_buttons_layout1)
        
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
        # mid_layout.addWidget(separator_mid4)
        
        # 添加其他CDN选项
        
        other_cdn = CollapsibleBox("其他图片CDN链接",parent_window=self,button_height=35)
        other_cdn_layout = QHBoxLayout()
        self.banner_cdn_widget = LabeledLineEditWithCopy("Banner")
        other_cdn_layout.addWidget(self.banner_cdn_widget)
        other_cdn.setContentLayout(other_cdn_layout)
        mid_layout.addWidget(other_cdn)
        
        # 第二行按钮
        mid_buttons_layout2 = QHBoxLayout()
        
        # update按钮
        self.update_button = QPushButton("Update")
        self.update_button.setToolTip("从Google Docs文档中提取信息")
        self.update_button.setMinimumHeight(35)
        self.update_button.clicked.connect(self.update_action)
        mid_buttons_layout2.addWidget(self.update_button)
        
        # 添加上传按钮
        self.upload_button = QPushButton("Upload")
        self.upload_button.setToolTip("将NAS文件夹中的图片上传到AWS Bucket获取CDN链接")
        self.upload_button.clicked.connect(self.uploader_upload_folder)
        self.upload_button.setMinimumHeight(35)
        mid_buttons_layout2.addWidget(self.upload_button)
        
        # 第三行按钮
        mid_buttons_layout3 = QHBoxLayout()
        
        # Generate生成按钮
        self.generate_button = QPushButton("Generate JSON")
        self.generate_button.setToolTip("根据已有信息生成JSON字符串")
        self.generate_button.setMinimumHeight(35)
        self.generate_button.clicked.connect(self.generate_json_action)
        mid_buttons_layout3.addWidget(self.generate_button)
        
        
        self.open_canary_url_button = QPushButton("Canary Inspection")
        self.open_canary_url_button.setToolTip("根据文件路径打开Canary页面测试")
        self.open_canary_url_button.setMinimumHeight(35)
        self.open_canary_url_button.clicked.connect(self.open_canary_url)
        mid_buttons_layout3.addWidget(self.open_canary_url_button)
        
        self.open_canary_url_button = QPushButton("Iterate")
        self.open_canary_url_button.setToolTip("获取未完成图片的配置页面json，批量替换CDN链接")
        self.open_canary_url_button.setMinimumHeight(35)
        self.open_canary_url_button.clicked.connect(self.iterate_json_action)
        mid_buttons_layout3.addWidget(self.open_canary_url_button)
        
        # 添加所有按钮
        mid_layout.addLayout(mid_buttons_layout2)
        mid_layout.addLayout(mid_buttons_layout3)
    
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
        self.clear_button.setToolTip("清除输出框中的内容，将所有组件复原到初始状态")
        self.clear_button.setFixedSize(130, 30)
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

        # Help button
        self.help_button = QPushButton()
        self.help_button.setFixedSize(30, 30)
        help_icon = self.style().standardIcon(QStyle.SP_MessageBoxQuestion)
        self.help_button.setIcon(help_icon)
        self.help_button.setFlat(True)
        self.help_button.setToolTip("如有问题请点击此处查看readme使用手册")
        self.help_button.clicked.connect(self.open_help_url)
        output_header.addWidget(self.help_button)
        
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
        main_layout.addWidget(vertical_separator2)
        main_layout.addWidget(right_panel)
        
        # 设置布局比例
        main_layout.setStretch(0, 0)  # 左侧面板固定宽度
        main_layout.setStretch(2, 0)  # 中间面板固定宽度
        main_layout.setStretch(4, 1)  # 右侧面板可拉伸
        
        # 5. 杂项
        self.uploader = ImageUploader()
        self.aws_upload = S3Uploader()
        self.pattern: StringPatternTransformer = None
        self.output_json = ""
        
        # Load mockup sizes and populate the combo box
        self.mockup_sizes_data = self.load_mockup_sizes()
        self.mockup_type_combo.addItem("-- Select a Type --")  # Add placeholder
        if self.mockup_sizes_data:
            self.mockup_type_combo.addItems(sorted(self.mockup_sizes_data.keys(), key=str.lower))
        self.mockup_type_combo.currentIndexChanged.connect(self.update_mockup_size_info)
        # Initial update to clear fields
        self.update_mockup_size_info()
        
        self.interaction_handler = GuiInteractionHandler()
        
    def on_fun_button_clicked(self):
        """
        一个有趣的按钮，用于与用户互动。
        """
        # 定义一些俏皮话
        fun_phrases = [
            "今天Pacdora上市了吗？",
            "别点了，再点我就要报警了！",
            "恭喜你！你刚刚浪费了宝贵的0.5秒。",
            "我们都在用力地活着，和我的一键配置说去吧。",
            "你知道吗？每一次点击，都有一只看不见的猫咪在空中翻滚。",
            "按钮被点击了，但它决定今天罢工。",
            "404: Fun Not Found.",
            "今天几号了？离发工资还有多久？",
            "你！退出这个程序！立刻！马上！",
            "1453年5月29日：QAQ"
        ]
        
        # 随机选择一条俏皮话并显示
        phrase = random.choice(fun_phrases)
        self.add_output_message(phrase, "info")
        
        # 创建一个抖动动画
        animation = QSequentialAnimationGroup(self)
        
        start_pos = self.it_is_a_button_for_fun.pos()
        
        # 抖动动画序列
        for i in range(4):
            anim_right = QPropertyAnimation(self.it_is_a_button_for_fun, b"pos")
            anim_right.setDuration(50)
            anim_right.setStartValue(start_pos)
            anim_right.setEndValue(start_pos + QPoint(5, 0))
            animation.addAnimation(anim_right)
            
            anim_left = QPropertyAnimation(self.it_is_a_button_for_fun, b"pos")
            anim_left.setDuration(50)
            anim_left.setStartValue(start_pos + QPoint(5, 0))
            anim_left.setEndValue(start_pos)
            animation.addAnimation(anim_left)
            
        animation.start()
        
    def clear_output(self):
        """
        1. 清除输出框内容
        2. 将所有widget都设置为空白
        """
        # 需要清空的widget列表
        to_clear = [
            self.pics_path_widget,
            self.title_widget, 
            self.description_widget,
            self.keywords_widget,
            self.view_widget,
            self.try_widget,
            self.h1_title_widget,
            self.h1_text_widget,
            self.whole_page_background_color_widget,
            self.mockup_list_1_name_widget,
            self.mockup_list_1_number_widget,
            self.mockup_list_2_number_widget,
            self.mockup_type_widget,
            self.mockup_size_widget,
            self.mockup_default_size_widget,
            self.more_button_action_widget,
            self.color_diy_choice_widget,
            self.color_label_diy_choice_widget,
            self.file_path_widget,
            self.cover_cdn_widget,
            self.cover_more_cdn_widget,
            self.step1_cdn_widget,
            self.step2_cdn_widget,
            self.step3_cdn_widget,
            self.feature1_cdn_widget,
            self.feature2_cdn_widget,
            self.feature3_cdn_widget,
            self.feature4_cdn_widget
        ]
        
        # 清空所有widget内容
        for item in to_clear:
            item.setText("")
        
        self.mockup_type_combo.setCurrentIndex(0) # Reset to placeholder
            
        self.more_button_action_widget.setText("#mockup-display")
        self.color_diy_choice_widget.setText("#FFFFFF")
        self.mockup_type_widget.setText("Mockup")
        
        # 清空输出框
        self.output_box.clear()

    def add_output_message(self, message, msg_type="info"):
        """
        通过发射信号来请求在主线程中添加消息。
        这个方法现在是线程安全的。
        """
        self.log_signal.emit(message, msg_type)

    def update_output_box(self, message, msg_type):
        """
        这是一个槽函数，它在主线程中被调用来安全地更新QTextEdit。
        """
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
        
    def bot_and_others_panel(self):
        """
        打开一个新的pop up面板用于精确控制discover和explore，以节省app空间
        """
        # 创建一个新窗口
        self.explore_discover_window = QMainWindow()
        self.explore_discover_window.setWindowTitle("Bot and others")
        self.explore_discover_window.setFixedSize(800, 600)
        
        # 创建中心部件和布局
        central_widget = QWidget()
        self.explore_discover_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        
        # layout1的标题
        layout1_title = QLabel("Miscellaneous")
        layout1_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(layout1_title)
        
        # 创建layout1按钮布局
        layout1 = QHBoxLayout()
        
        # 添加一个按钮用于批量替换旧resource页面
        self.replace_old_resource_button = QPushButton("Replace old resource pages")
        self.replace_old_resource_button.setToolTip("确保点击前已经复制了旧resource页面的json字符串")
        self.replace_old_resource_button.clicked.connect(self.replace_old_resource_to_clipboard)
        layout1.addWidget(self.replace_old_resource_button)
        
        # 添加一个按钮用于增加login requirement
        self.add_login_requirement_button = QPushButton("Add login requirement")
        self.add_login_requirement_button.setToolTip("Add login requirement to the json string")
        self.add_login_requirement_button.clicked.connect(self.add_login_requirement)
        layout1.addWidget(self.add_login_requirement_button)
        
        layout.addLayout(layout1)
        
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 创建第二个布局
        layout2 = QVBoxLayout()
        
        # layout2的标题
        layout2_title = QLabel("Bot and dialog")
        layout2_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(layout2_title)
        
        # 添加BOT和对话框
        ## bot参数
        bot_page_type_group = QHBoxLayout()
        bot_page_type_label = QLabel("Bot page type:")
        bot_page_type_group.addWidget(bot_page_type_label)
        
        self.bot_page_type_widget = QComboBox()
        self.bot_page_type_widget.addItems(["Tools/resource", "Landing"])
        bot_page_type_group.addWidget(self.bot_page_type_widget)
        
        layout2.addLayout(bot_page_type_group)
        
        ## bot语言
        bot_language_group = QHBoxLayout()
        bot_language_label = QLabel("Bot language:")
        bot_language_group.addWidget(bot_language_label)
        
        self.bot_language_widget = QComboBox()
        self.bot_language_widget.addItems(["英语", "西班牙语", "葡萄牙语","法语","印度尼西亚语","日语","中文"])
        bot_language_group.addWidget(self.bot_language_widget)
        
        layout2.addLayout(bot_language_group)
        
        ## 默认任务类型
        default_task_group = QHBoxLayout()
        default_task_label = QLabel("Default task:")
        default_task_group.addWidget(default_task_label)
        
        self.default_task_widget = QComboBox()
        self.default_task_widget.addItems(["批量上传替换图片","批量设为启用","自定义批量"])
        default_task_group.addWidget(self.default_task_widget)
        
        layout2.addLayout(default_task_group)
        
        ## 自定义批量任务
        self.custom_batch_bot = CollapsibleBox("自定义批量BOT")
        
        custom_batch_bot_content_layout = QVBoxLayout()
        ## 添加两个输入框，实现StringPatternTransformer的初始化
        compare_json_panel_title = QLabel("放入你需要的对比文本")
        custom_batch_bot_content_layout.addWidget(compare_json_panel_title)
        
        compare_json_panel_input_layout = QHBoxLayout()
        old_json_input = QTextEdit(placeholderText='请放入改动前的旧文本',undoRedoEnabled=True)
        new_json_input = QTextEdit(placeholderText='请放入改动后的文本')
        compare_json_panel_input_layout.addWidget(old_json_input)
        compare_json_panel_input_layout.addWidget(new_json_input)
        custom_batch_bot_content_layout.addLayout(compare_json_panel_input_layout)
        
        compare_json_button = QPushButton('点击自动分析文本之间的差异并初始化bot')
        compare_json_button.clicked.connect(
            lambda: self.initialize_pattern(
                old_p=old_json_input.toPlainText(),
                new_p=new_json_input.toPlainText()
            )
        )
        custom_batch_bot_content_layout.addWidget(compare_json_button)
        
        self.custom_batch_bot.setContentLayout(custom_batch_bot_content_layout)
        layout2.addWidget(self.custom_batch_bot)
        
        ## 输入想要进行操作的页面的短链接
        self.bot_target_list_widget = QTextEdit(placeholderText='输入想要进行操作的页面的短链接')
        layout2.addWidget(self.bot_target_list_widget)
        
        ## bot操作按钮
        bot_button_layout = QHBoxLayout()
        
        self.clear_cache_button = QPushButton('Clear cache')
        self.clear_cache_button.setToolTip('如果遇到先前任务已读条需要重新进行，请先清楚cache')
        self.clear_cache_button.clicked.connect(self.clear_cache)
        bot_button_layout.addWidget(self.clear_cache_button)
        
        self.activate_bot_button = QPushButton("Activate bot")
        self.activate_bot_button.clicked.connect(self.on_activate_bot_clicked)
        bot_button_layout.addWidget(self.activate_bot_button)
        
        self.continue_bot_button = QPushButton("Continue")
        self.continue_bot_button.setToolTip('如果遇到需要手动介入的情况，请在操作完成后点击此处继续')
        # 将 Continue 按钮连接到交互处理器
        self.continue_bot_button.clicked.connect(
            lambda: self.interaction_handler.continue_action(confirmed=True)
        )
        # 添加continue提示信息
        self.interaction_handler.on_request = lambda msg: self.add_output_message(f"⏸️ 等待确认: {msg}", "warning")
        bot_button_layout.addWidget(self.continue_bot_button)
        
        layout2.addLayout(bot_button_layout)
        
        layout.addLayout(layout2)
        
        # 显示窗口
        self.explore_discover_window.show()
        
    def request_confirmation(self, message: str, on_confirm: Callable[[bool], None]):
        self._on_confirm = on_confirm
        self._is_waiting = True
        # ✅ 发送信号或调用主界面方法更新状态栏/日志
        if hasattr(self, 'on_request'):
            self.on_request(message)  # 可由 WSA 绑定
        
    def initialize_pattern(self, old_p, new_p):
        """
        根据初始文本实例化
        """
        try:
            self.pattern = StringPatternTransformer(string_a=old_p,string_b=new_p)
            self.add_output_message('Successfully analyzed pattern differences.','success')
        except Exception as e:
            self.add_output_message(f"Error happened during string pattern recognization: {e}","error")
        
    def pattern_update(self,input) -> str:
        """
        使用StringPatternTransformer转化文本
        """
        if self.pattern:
            output = self.pattern.transform(input)
        return output
    
    def on_activate_bot_clicked(self):
        """
        激活机器人的主要函数，根据选择的任务类型执行不同的自动化操作
        """
        task_type = self.default_task_widget.currentText()
        language = self.bot_language_widget.currentText()
        target_list_text = self.bot_target_list_widget.toPlainText().strip()
        
        # 验证目标列表
        if not target_list_text:
            self.add_output_message('请输入目标页面的短链接列表', 'error')
            return
        
        # 将文本转换为列表
        target_list = [line.strip() for line in target_list_text.split('\n') if line.strip()]
        
        if not target_list:
            self.add_output_message('目标列表为空，请输入有效的短链接', 'error')
            return
        
        self.add_output_message(f'准备处理 {len(target_list)} 个目标页面', 'info')
        
        if task_type == '批量上传替换图片':
            self.activate_batch_upload_replace_bot(language, target_list)
        elif task_type == '批量设为启用':
            self.activate_batch_set_online_bot(language, target_list)
        elif task_type == '自定义批量':
            self.activate_custom_batch_bot(language, target_list)
        else:
            self.add_output_message(f'未知的任务类型: {task_type}', 'error')
    
    def activate_batch_upload_replace_bot(self, language: str, target_list: list):
        """
        将整个批量上传和替换任务放入后台线程执行，以避免阻塞UI。
        """
        def worker():
            try:
                # 注册日志回调函数
                from dp_bot_manager import set_log_callback
                set_log_callback(lambda msg, level: self.add_output_message(msg, level))
                
                self.add_output_message(f"🚀 开始处理 {len(target_list)} 个目标...", "info")

                # --- 1. 确定基础路径（GUI 层决策）---
                if sys.platform.startswith('darwin'):
                    base_folder = "/Volumes/shared/pacdora.com/"
                    if not os.path.isdir(base_folder):
                        self.add_output_message(f"⚠️ NAS不可达，改用桌面", "warning")
                        base_folder = os.path.expanduser("~/Desktop/")
                else:
                    base_folder = "//nas01.tools.baoxiaohe.com/shared/pacdora.com/"

                # --- 2. 上传所有目标图片 ---
                for i, target in enumerate(target_list):
                    folder_path = os.path.join(base_folder, target)
                    if not os.path.exists(folder_path):
                        self.add_output_message(f"❌ 路径不存在: {folder_path}", "error")
                        continue
                    self.add_output_message(f"🖼️ [{i+1}/{len(target_list)}] 上传: {target}", "info")
                    self.uploader_upload_folder_bot(given_folder_path=folder_path, is_pass_cdn=False)

                self.add_output_message("图片上传完成，启动自动化替换", "success")

                # --- 3. 使用工厂创建专用 Bot ---
                bot = BotFactory.create_upload_replace_bot(
                    language=language,
                    base_folder=base_folder,
                    target_list=target_list,
                    interaction_strategy=self.interaction_handler
                )

                self.add_output_message("🤖 机器人已启动，请查看浏览器", "success")

                # --- 4. 运行机器人 ---
                bot.run()
                self.add_output_message("🎉 所有任务已完成！", "success")

            except Exception as e:
                self.add_output_message(f"❌ 批量上传替换失败: {e}", "error")

        # --- 启动后台线程 ---
        from threading import Thread
        thread = Thread(target=worker, daemon=True)
        thread.start()
        
    def activate_batch_set_online_bot(self, language: str, target_list: list):
        """
        激活批量设为启用机器人
        使用 BotFactory.create_online_sync_bot
        """
        try:
            from dp_bot_manager import set_log_callback
            set_log_callback(lambda msg, level: self.add_output_message(msg, level))
            
            self.add_output_message('启动批量设为启用机器人...', 'info')
            
            # 创建并启动批量设为启用机器人，启用机器人不需要传入update函数
            bot = BotFactory.create_online_sync_bot(
                language=language,
                target_list=target_list,
                interaction_strategy=self.interaction_handler
            )
            
            self.add_output_message('批量设为启用机器人已创建成功，请查看新打开的浏览器窗口', 'success')
            from threading import Thread
            Thread(target=bot.run, daemon=True).start()
            
        except Exception as e:
            self.add_output_message(f'启动批量设为启用机器人时发生错误: {e}', 'error')
    
    def activate_custom_batch_bot(self, language: str, target_list: list):
        """
        激活自定义批量机器人
        通过 StringPatternTransformer 分析差异，逐个打开页面进行操作
        """
        try:
            from dp_bot_manager import set_log_callback
            set_log_callback(lambda msg, level: self.add_output_message(msg, level))
            
            if self.pattern is None:
                self.add_output_message('请先分析文本差异并初始化模式转换器', 'warning')
                return
            
            self.add_output_message('启动自定义批量机器人...', 'info')
            
            # 创建自定义 bot（假设你有对应的构造方式）
            bot = BotFactory.create_pacdora_json_bot(
                language=language,
                update_action=lambda x: self.pattern_update(x),
                target_list=target_list,
                interaction_strategy=self.interaction_handler
            )
            self.add_output_message('自定义机器人已创建成功，请查看新打开的浏览器窗口', 'success')
            from threading import Thread
            Thread(target=bot.run, daemon=True).start()
            
        except Exception as e:
            self.add_output_message(f'启动自定义批量机器人时发生错误: {e}', 'error')
            
    def clear_cache(self):
        cache_dir = os.path.join(os.path.dirname(__file__), "cache")
        if not os.path.isdir(cache_dir):
            self.add_output_message(f"Cache directory not found: {cache_dir}", "warning")
            return

        deleted = 0
        for pkl_file in glob.glob(os.path.join(cache_dir, "*.pkl")):
            if os.path.basename(pkl_file) != "cookies.pkl":
                try:
                    os.remove(pkl_file)
                    deleted += 1
                except Exception as e:
                    self.add_output_message(f"Failed to delete {pkl_file}: {e}", "error")

        self.add_output_message(f"Deleted {deleted} cache .pkl files (except cookies.pkl).", "success")
        
    def add_login_requirement(self):
        try:
            t = QGuiApplication.clipboard().text()
            if t:
                t = update_login_requirment(t)
                QGuiApplication.clipboard().setText(t)
                self.add_output_message("Add login requirement success", "success")
            else:
                self.add_output_message("Clipboard is empty", "warning")
        except Exception as e:
            self.add_output_message(f"Error: {e}", "error")
    
    def replace_old_resource_to_clipboard(self):
        try:
            t = QGuiApplication.clipboard().text()
            if t:
                t = update_old_resource_page(t)
                QGuiApplication.clipboard().setText(t)
                self.add_output_message("Replace success", "success")
            else:
                self.add_output_message("Clipboard is empty", "warning")
        except Exception as e:
            self.add_output_message(f"Error: {e}", "error")
            
    def open_help_url(self):
        """
        Opens the help URL in a web browser.
        """
        webbrowser.open("https://github.com/xolarvill/web_setup_automation")

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
            self.add_output_message("Cannot open a null path. Please select a valid folder path before opening. Maybe the folder is not created yet. Check the process in notion.", "error")
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
        type = self.page_type.currentText()
        if type == "Mockup tool":
            self.update_action_mockup_tool()
            
        elif type == "Mockup resource":
            self.update_action_mockup_tool() # NOTICE: here resource page uses the update action of mockup tool!!!
            
        elif type == "Mockup universal topic":
            self.update_action_mockup_tool() # NOTICE: here universal topic page uses the update action of mockup tool!!!
            
        elif type == "Dieline tool":
            self.update_action_dieline_tool()
            
        elif type == "Dieline renderer":
            self.update_action_dieline_renderer()
            
        elif type == "Mockup landing page":
            self.update_action_mockup_landing_page()
            
        else:
            self.add_output_message("Unavailable page type...","warning")

    def update_action_dieline_renderer(self):
        pass
    
    def update_action_dieline_tool(self):
        pass

    def update_action_mockup_landing_page(self):
        """
        适配landing page的改进更新函数
        """
        self.add_output_message("Processing clipboard content...", "info")
    
        clipboard = QGuiApplication.clipboard()
        clipboard_text = clipboard.text()
        
        # 如果剪切板非空
        if clipboard_text:
            preview_start = clipboard_text[:50]
            self.add_output_message(f"Clipboard content captured: {preview_start}...", "info")
            
            # 首先进行分段验证
            try:
                self.segments = segment(clipboard_text)
                self.add_output_message(f"Text segmented into {len(self.segments)} parts.", "info")
                
                if len(self.segments) != 5:
                    self.add_output_message(f"Wrong number of segments: The number of segments is not 5 for landing page. Please check the input text. Maybe you added the wrong number of #. There should be 4 of them.", "error")
                    # 如果分段错误，仍尝试处理H1标题和文本（从原代码保留的逻辑）
                    if self.segments and len(self.segments) > 0:
                        html = [line for line in self.segments[0].splitlines() if line.strip()]
                        if len(html) >= 2:
                            self.h1_title_widget.setText(html[-2])
                            self.h1_text_widget.setText(html[-1])
                    return
                else:
                    self.add_output_message("Text segmented successfully.", "success")
                    
            except Exception as e:
                self.add_output_message(f"Error segmenting text: {e}", "error")
                return
            
            # 从第一段提取结构化信息
            try:
                first_segment = self.segments[0] if self.segments else ""
                if not first_segment.strip():
                    self.add_output_message("First segment is empty, cannot extract structured fields.", "error")
                    return
                    
                # 使用新的解析函数解析第一段
                parsed_data = extract_structured_fields(first_segment)
                
                # 检查必要字段是否为空
                required_fields = ["URL", "Title", "Meta Description", "Breadcrumb"]
                view_try_fields = ["view_text", "try_text"]
                
                empty_basic_fields = [field for field in required_fields if not parsed_data.get(field, "").strip()]
                empty_view_try = [field for field in view_try_fields if not parsed_data.get(field, "").strip()]
                
                if len(empty_basic_fields) == len(required_fields) and len(empty_view_try) == len(view_try_fields):
                    self.add_output_message("Parsing failed: All required fields are empty in first segment. Please check your input format.", "error")
                    return
                
                self.add_output_message("Structured fields parsed successfully from first segment!", "success")
                
                # 更新界面字段
                # URL字段处理
                if parsed_data.get("URL"):
                    url_value = parsed_data["URL"]
                    # 简化处理mockup名称
                    mockup_list_name = url_value.strip().replace("mockup", "").replace("-", " ")
                    self.mockup_list_1_name_widget.setText(mockup_list_name.strip().capitalize())
                    
                    # 设置路径（根据系统类型）
                    if sys.platform.startswith('darwin'):
                        self.pics_path_widget.setText(f"/Volumes/shared/pacdora.com/{url_value}")
                    elif os.name == 'nt':
                        self.pics_path_widget.setText(f"//nas01.tools.baoxiaohe.com/shared/pacdora.com/{url_value}")
                    else:
                        self.add_output_message(f"Detected system: {sys.platform}", "info")
                    
                    self.file_path_widget.setText(url_value)
                
                # 其他基础字段更新
                if parsed_data.get("Title"):
                    self.title_widget.setText(parsed_data["Title"])
                
                if parsed_data.get("Meta Description"):
                    self.description_widget.setText(parsed_data["Meta Description"])
                
                if parsed_data.get("Breadcrumb"):
                    self.keywords_widget.setText(parsed_data["Breadcrumb"])
                
                # View字段更新
                if parsed_data.get("view"):
                    self.view_widget.setText(parsed_data["view"])
                
                # Try字段更新
                if parsed_data.get("try"):
                    self.try_widget.setText(parsed_data["try"])
                
            except Exception as e:
                self.add_output_message(f"Error parsing structured fields from first segment: {e}", "error")
                return
            
            # 补齐文件夹
            folder_path = self.pics_path_widget.text()
            self.ensure_folder_exists(folder_path=folder_path)
            
            # 判断是否存在cdn
            cdn_records_exist = self.detect_cdn_records(folder_path=folder_path)
            if cdn_records_exist:
                self.pass_cdn_records()
                self.add_output_message("Detected cdn records, auto fill.", "success")
        
        else:
            self.add_output_message("Clipboard is empty or does not contain text.", "warning")



    def update_action_mockup_tool(self):
        """
        改进后的更新函数，使用新的解析逻辑
        """
        self.add_output_message("Processing clipboard content...", "info")
    
        clipboard = QGuiApplication.clipboard()
        clipboard_text = clipboard.text()
        
        # 如果剪切板非空
        if clipboard_text:
            preview_start = clipboard_text[:50]
            self.add_output_message(f"Clipboard content captured: {preview_start}...", "info")
            
            # 首先进行分段验证
            try:
                self.segments = segment(clipboard_text)
                self.add_output_message(f"Text segmented into {len(self.segments)} parts.", "info")
                
                if len(self.segments) != 8:
                    self.add_output_message("Wrong number of segments: The number of segments is not 8. Please check the input text. Maybe you added the wrong number of #. There should be 7 of them.", "error")
                    return
                else:
                    self.add_output_message("Text segmented successfully.", "success")
                    
            except Exception as e:
                self.add_output_message(f"Error segmenting text: {e}", "error")
                return
            
            # 从第一段提取结构化信息
            try:
                first_segment = self.segments[0] if self.segments else ""
                if not first_segment.strip():
                    self.add_output_message("First segment is empty, cannot extract structured fields.", "error")
                    return
                    
                # 使用新的解析函数解析第一段
                parsed_data = extract_structured_fields(first_segment)
                
                # 检查必要字段是否为空
                required_fields = ["URL", "Title", "Meta Description", "Breadcrumb"]
                empty_fields = [field for field in required_fields if not parsed_data.get(field, "").strip()]
                
                if len(empty_fields) == len(required_fields):
                    self.add_output_message("Parsing failed: All required fields are empty in first segment. Please check your input format.", "error")
                    return
                
                self.add_output_message("Structured fields parsed successfully from first segment!", "success")
                
                # 更新界面字段
                # URL字段处理
                if parsed_data.get("URL"):
                    url_value = parsed_data["URL"]
                    # 简化处理mockup名称
                    mockup_list_name = url_value.strip().replace("mockup", "").replace("-", " ")
                    self.mockup_list_1_name_widget.setText(mockup_list_name.capitalize())
                    
                    # 设置路径（根据系统类型）
                    if sys.platform.startswith('darwin'):
                        self.pics_path_widget.setText(f"/Volumes/shared/pacdora.com/{url_value}")
                    elif os.name == 'nt':
                        self.pics_path_widget.setText(f"//nas01.tools.baoxiaohe.com/shared/pacdora.com/{url_value}")
                    else:
                        self.add_output_message(f"Detected system: {sys.platform}", "info")
                    
                    self.file_path_widget.setText(url_value)
                
                # 其他字段更新
                if parsed_data.get("Title"):
                    self.title_widget.setText(parsed_data["Title"])
                
                if parsed_data.get("Meta Description"):
                    self.description_widget.setText(parsed_data["Meta Description"])
                
                if parsed_data.get("Breadcrumb"):
                    self.keywords_widget.setText(parsed_data["Breadcrumb"])
                
                if parsed_data.get("view"):
                    self.view_widget.setText(parsed_data["view"])
                
                if parsed_data.get("try"):
                    self.try_widget.setText(parsed_data["try"])
                
                # 如果有链接需要处理，可以在这里添加
                # 例如：self.view_link = parsed_data.get("view_link", "")
                #      self.try_link = parsed_data.get("try_link", "")
                
            except Exception as e:
                self.add_output_message(f"Error parsing structured fields from first segment: {e}", "error")
                return
            
            # 补齐文件夹
            folder_path = self.pics_path_widget.text()
            self.ensure_folder_exists(folder_path=folder_path)
            
            # 判断是否存在cdn
            cdn_records_exist = self.detect_cdn_records(folder_path=folder_path)
            if cdn_records_exist:
                self.pass_cdn_records()
                self.add_output_message("Detected cdn records, auto fill.", "success")
        
        else:
            self.add_output_message("Clipboard is empty or does not contain text.", "warning")

        
    def generate_json_action(self):
        chosen_type = self.page_type.currentText()
        if chosen_type == 'Mockup tool':
            self.generate_json_action_mockup_tool()
        elif chosen_type == 'Mockup resource':
            self.generate_json_action_mockup_resource()
        elif chosen_type == 'Mockup universal topic':
            self.generate_json_action_mockup_universal_topic()
        
        elif chosen_type == 'Dieline tool':
            self.generate_json_action_dieline_tool()
        elif chosen_type == 'Dieline renderer':
            self.generate_json_action_dieline_rendered()
            
        elif chosen_type == 'Mockup landing page':
            self.generate_json_action_mockup_landing_page()
        elif chosen_type == 'TOOLS':
            self.generate_json_action_tools()
        
    def generate_json_action_dieline_tool(self):
        pass
    
    def generate_json_action_dieline_rendered(self):
        pass
    
    def generate_json_action_mockup_universal_topic(self):
        self.add_output_message("Generating JSON output...", "info")
        
        # 获取关键字段
        view_text = self.view_widget.text().split(":")[0].strip()
        view_link_raw = self.view_widget.text().split(":")[1].strip()
        view_link_spicy = f"{view_link_raw}"
        view_link = view_link_spicy
        #print('test point 1')
        
        try_text = self.try_widget.text().split(":")[0].strip()
        try_link_raw = self.try_widget.text().split(":")[1].strip() 
        try_link_spicy = f"{try_link_raw}"
        try_link = try_link_spicy
        
        breadcrumb = self.keywords_widget.text()
        # 处理面包屑文本,保持AI和3D大写
        breadcrumb_lower = breadcrumb.capitalize().replace("Ai", "AI").replace("ai", "AI").replace("3d", "3D")
        
        banner_cdn = cdn_placeholder_image(self.banner_cdn_widget, type='banner')
        
        part2 = self.segments[1]
        part2_text = part2.splitlines()[1]
        
        part3 = [line for line in self.segments[2].splitlines() if line.strip()]
        part3_title = part3[0]
        part3_text = process_text_with_links(part3[1:])
        
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
            model_1_name, model_1_image_url, model_1_editor_inner_link = fetch_mockup_details(urls[0], self.add_output_message)
            model_2_name, model_2_image_url, model_2_editor_inner_link = fetch_mockup_details(urls[1], self.add_output_message)
            model_3_name, model_3_image_url, model_3_editor_inner_link = fetch_mockup_details(urls[2], self.add_output_message)
            model_4_name, model_4_image_url, model_4_editor_inner_link = fetch_mockup_details(urls[3], self.add_output_message)
            model_5_name, model_5_image_url, model_5_editor_inner_link = fetch_mockup_details(urls[4], self.add_output_message)
            model_6_name, model_6_image_url, model_6_editor_inner_link = fetch_mockup_details(urls[5], self.add_output_message)
            model_7_name, model_7_image_url, model_7_editor_inner_link = fetch_mockup_details(urls[6], self.add_output_message)
            model_8_name, model_8_image_url, model_8_editor_inner_link = fetch_mockup_details(urls[7], self.add_output_message)
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
        
        step1_cdn = cdn_placeholder_image(self.step1_cdn_widget.text(),type='1')
        step2_cdn = cdn_placeholder_image(self.step2_cdn_widget.text(),type='2')
        step3_cdn = cdn_placeholder_image(self.step3_cdn_widget.text(),type='3')
        
        part5 = [line for line in self.segments[4].splitlines() if line.strip()]
        part5_title = part5[0].strip()
        part5_step1_a = part5[1].strip()
        part5_step1_b = part5[2].strip()
        
        part5_step2_a = part5[3].strip()
        part5_step2_b = part5[4].strip()
        
        part5_step3_a = part5[5].strip()
        part5_step3_b = part5[6].strip()
        
        
        part6 = [line for line in self.segments[5].splitlines() if line.strip()]
        
        part6_1_feature_cdn = cdn_placeholder_image(self.feature1_cdn_widget.text(),type='a')
        part6_2_feature_cdn = cdn_placeholder_image(self.feature2_cdn_widget.text(),type='b')
        part6_3_feature_cdn = cdn_placeholder_image(self.feature3_cdn_widget.text(),type='c')
        part6_4_feature_cdn = cdn_placeholder_image(self.feature4_cdn_widget.text(),type='d')
        
        part6_title = part6[0]
        
        part6_1_title = part6[1].strip()
        part6_1_a = part6[2].strip()
        part6_1_b = part6[3].strip()
        part6_1_button = part6[4].strip()
        # 根据给定的文案判断是try还是view，由于try的变种文案太多，所以用view来判断
        if part6_1_button.startswith("View"):
            part6_1_button_text = view_text
            part6_1_button_link = view_link_spicy
            part6_1_button_gtm = 'ga-seo_tools_view_all'
        else:
            part6_1_button_text = try_text
            part6_1_button_link = try_link_spicy
            part6_1_button_gtm = 'ga-seo_tools_try'

        part6_2_title = part6[5].strip()
        part6_2_a = part6[6].strip()
        part6_2_b = part6[7].strip()
        part6_2_button = part6[8].strip()
        if part6_2_button.startswith("View"):
            part6_2_button_text = view_text
            part6_2_button_link = view_link_spicy
            part6_2_button_gtm = 'ga-seo_tools_view_all'
        else:
            part6_2_button_text = try_text
            part6_2_button_link = try_link_spicy
            part6_2_button_gtm = 'ga-seo_tools_try'
        
        part6_3_title = part6[9].strip()
        part6_3_a = part6[10].strip()
        part6_3_b = part6[11].strip()
        part6_3_button = part6[12].strip()
        if part6_3_button.startswith("View"):
            part6_3_button_text = view_text
            part6_3_button_link = view_link_spicy
            part6_3_button_gtm = 'ga-seo_tools_view_all'
        else:
            part6_3_button_text = try_text
            part6_3_button_link = try_link_spicy
            part6_3_button_gtm = 'ga-seo_tools_try'
        
        part6_4_title = part6[13].strip()
        part6_4_a = part6[14].strip()
        part6_4_b = part6[15].strip()
        part6_4_button = part6[16].strip()
        if part6_4_button.startswith("View"):
            part6_4_button_text = view_text
            part6_4_button_link = view_link_spicy
            part6_4_button_gtm = 'ga-seo_tools_view_all'
        else:
            part6_4_button_text = try_text
            part6_4_button_link = try_link_spicy
            part6_4_button_gtm = 'ga-seo_tools_try'
        
        # FAQ环节
        part7 = self.segments[6]
        part7_block = parse_faq_text(part7)
        
        part7_q1 = part7_block[0]['question'].strip()
        part7_a1 = part7_block[0]['answer'].strip()
        
        part7_q2 = part7_block[1]['question'].strip()
        part7_a2 = part7_block[1]['answer'].strip()
        
        part7_q3 = part7_block[2]['question'].strip()
        part7_a3 = part7_block[2]['answer'].strip()
        
        part7_q4 = part7_block[3]['question'].strip()
        part7_a4 = part7_block[3]['answer'].strip()
        
        part7_q5 = part7_block[4]['question'].strip()
        part7_a5_raw = part7_block[4]['answer'].strip()
        part7_a5 = part7_a5_raw.replace(
            "pricing page", 
            '<a class="pac-ui-editor-a" href=/pricing target=_self gtm="" rel="noopener noreferrer">pricing page</a>'
        )
        
        part8_text = self.segments[7].splitlines()[0]
        
        folder_path = self.pics_path_widget.text()
        self.ensure_folder_exists(folder_path = folder_path)
        
        # 读取模板内容
        temp_path = get_resource_path('json_templates/mockup_universal_topic.json')
        with open(temp_path, 'r', encoding='utf-8') as f:
            template_str = f.read()

        # 构建替换字典
        replace_dict = {
            "view_text": view_text,
            "view_link": view_link,
            "try_text": try_text,
            "try_link": try_link,
            "breadcrumb": breadcrumb,
            "breadcrumb_lower": breadcrumb_lower,
            "banner_cdn": banner_cdn,
            "part2_text": part2_text,
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
            "part6_1_button_text" : part6_1_button_text,
            "part6_1_button_link" : part6_1_button_link,
            "part6_1_button_gtm" : part6_1_button_gtm,
            "part6_2_title": part6_2_title,
            "part6_2_feature_cdn": part6_2_feature_cdn,
            "part6_2_a": part6_2_a,
            "part6_2_b": part6_2_b,
            "part6_2_button_text" : part6_2_button_text,
            "part6_2_button_link" : part6_2_button_link,
            "part6_2_button_gtm" : part6_2_button_gtm,
            "part6_3_title": part6_3_title,
            "part6_3_feature_cdn": part6_3_feature_cdn,
            "part6_3_a": part6_3_a,
            "part6_3_b": part6_3_b,
            "part6_3_button_text" : part6_3_button_text,
            "part6_3_button_link" : part6_3_button_link,
            "part6_3_button_gtm" : part6_3_button_gtm,
            "part6_4_title": part6_4_title,
            "part6_4_feature_cdn": part6_4_feature_cdn,
            "part6_4_a": part6_4_a,
            "part6_4_b": part6_4_b,
            "part6_4_button_text" : part6_4_button_text,
            "part6_4_button_link" : part6_4_button_link,
            "part6_4_button_gtm" : part6_4_button_gtm,
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
            if isinstance(value, str):
                # 使用json.dumps正确处理JSON字符串中的特殊字符
                value = json.dumps(value)[1:-1]  # 去掉json.dumps添加的外层引号
            template_str = template_str.replace(f"{{{{{key}}}}}", str(value))

        # 尝试解析为json
        try:
            json_obj = json.loads(template_str)
            json_string = json.dumps(json_obj, indent=2, ensure_ascii=False)
            # self.json_widget.setText(json_string)
            self.output_json = json_string
            QGuiApplication.clipboard().setText(json_string)
            self.add_output_message("JSON generated and copied to clipboard!", "success")
        except Exception as e:
            self.add_output_message(f"Error generating JSON: {e}", "error")
    
    def generate_json_action_mockup_resource(self):
        self.add_output_message("Generating JSON output...", "info")
        
        # 获取关键字段
        view_text = self.view_widget.text().split(":")[0].strip()
        view_link_raw = self.view_widget.text().split(":")[1].strip()
        view_link_spicy = f"{view_link_raw}"
        view_link = view_link_spicy
        
        try_text = self.try_widget.text().split(":")[0].strip()
        try_link_raw = self.try_widget.text().split(":")[1].strip() 
        try_link_spicy = f"{try_link_raw}"
        try_link = try_link_spicy
        
        breadcrumb = self.keywords_widget.text()
        breadcrumb_lower = breadcrumb.capitalize().replace("Ai", "AI").replace("ai", "AI").replace("3d", "3D")
        
        part2 = self.segments[1]
        part2_text = part2.splitlines()[1]
        
        part3 = [line for line in self.segments[2].splitlines() if line.strip()]
        part3_title = part3[0]
        part3_text = process_text_with_links(part3[1:])
        
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
            model_9_name = var_json_data["model_9"]["name"]
            model_9_image_url = var_json_data["model_9"]["image_url"]
            model_9_editor_inner_link = var_json_data["model_9"]["editor_inner_link"]
            model_10_name = var_json_data["model_10"]["name"]
            model_10_image_url = var_json_data["model_10"]["image_url"]
            model_10_editor_inner_link = var_json_data["model_10"]["editor_inner_link"]
            model_11_name = var_json_data["model_11"]["name"]
            model_11_image_url = var_json_data["model_11"]["image_url"]
            model_11_editor_inner_link = var_json_data["model_11"]["editor_inner_link"]
            model_12_name = var_json_data["model_12"]["name"]
            model_12_image_url = var_json_data["model_12"]["image_url"]
            model_12_editor_inner_link = var_json_data["model_12"]["editor_inner_link"]
            model_13_name = var_json_data["model_13"]["name"]
            model_13_image_url = var_json_data["model_13"]["image_url"]
            model_13_editor_inner_link = var_json_data["model_13"]["editor_inner_link"]
            model_14_name = var_json_data["model_14"]["name"]
            model_14_image_url = var_json_data["model_14"]["image_url"]
            model_14_editor_inner_link = var_json_data["model_14"]["editor_inner_link"]
            model_15_name = var_json_data["model_15"]["name"]
            model_15_image_url = var_json_data["model_15"]["image_url"]
            model_15_editor_inner_link = var_json_data["model_15"]["editor_inner_link"]
            model_16_name = var_json_data["model_16"]["name"]
            model_16_image_url = var_json_data["model_16"]["image_url"]
            model_16_editor_inner_link = var_json_data["model_16"]["editor_inner_link"]
            model_17_name = var_json_data["model_17"]["name"]
            model_17_image_url = var_json_data["model_17"]["image_url"]
            model_17_editor_inner_link = var_json_data["model_17"]["editor_inner_link"]
            model_18_name = var_json_data["model_18"]["name"]
            model_18_image_url = var_json_data["model_18"]["image_url"]
            model_18_editor_inner_link = var_json_data["model_18"]["editor_inner_link"]
            model_19_name = var_json_data["model_19"]["name"]
            model_19_image_url = var_json_data["model_19"]["image_url"]
            model_19_editor_inner_link = var_json_data["model_19"]["editor_inner_link"]
            model_20_name = var_json_data["model_20"]["name"]
            model_20_image_url = var_json_data["model_20"]["image_url"]
            model_20_editor_inner_link = var_json_data["model_20"]["editor_inner_link"]
            model_21_name = var_json_data["model_21"]["name"]
            model_21_image_url = var_json_data["model_21"]["image_url"]
            model_21_editor_inner_link = var_json_data["model_21"]["editor_inner_link"]
            model_22_name = var_json_data["model_22"]["name"]
            model_22_image_url = var_json_data["model_22"]["image_url"]
            model_22_editor_inner_link = var_json_data["model_22"]["editor_inner_link"]
            model_23_name = var_json_data["model_23"]["name"]
            model_23_image_url = var_json_data["model_23"]["image_url"]
            model_23_editor_inner_link = var_json_data["model_23"]["editor_inner_link"]
            model_24_name = var_json_data["model_24"]["name"]
            model_24_image_url = var_json_data["model_24"]["image_url"]
            model_24_editor_inner_link = var_json_data["model_24"]["editor_inner_link"]
        else:
            urls = extract_url(part4)
            model_1_name, model_1_image_url, model_1_editor_inner_link = fetch_mockup_details(urls[0], self.add_output_message)
            model_2_name, model_2_image_url, model_2_editor_inner_link = fetch_mockup_details(urls[1], self.add_output_message)
            model_3_name, model_3_image_url, model_3_editor_inner_link = fetch_mockup_details(urls[2], self.add_output_message)
            model_4_name, model_4_image_url, model_4_editor_inner_link = fetch_mockup_details(urls[3], self.add_output_message)
            model_5_name, model_5_image_url, model_5_editor_inner_link = fetch_mockup_details(urls[4], self.add_output_message)
            model_6_name, model_6_image_url, model_6_editor_inner_link = fetch_mockup_details(urls[5], self.add_output_message)
            model_7_name, model_7_image_url, model_7_editor_inner_link = fetch_mockup_details(urls[6], self.add_output_message)
            model_8_name, model_8_image_url, model_8_editor_inner_link = fetch_mockup_details(urls[7], self.add_output_message)
            model_9_name, model_9_image_url, model_9_editor_inner_link = fetch_mockup_details(urls[8], self.add_output_message)
            model_10_name, model_10_image_url, model_10_editor_inner_link = fetch_mockup_details(urls[9], self.add_output_message)
            model_11_name, model_11_image_url, model_11_editor_inner_link = fetch_mockup_details(urls[10], self.add_output_message)
            model_12_name, model_12_image_url, model_12_editor_inner_link = fetch_mockup_details(urls[11], self.add_output_message)
            model_13_name, model_13_image_url, model_13_editor_inner_link = fetch_mockup_details(urls[12], self.add_output_message)
            model_14_name, model_14_image_url, model_14_editor_inner_link = fetch_mockup_details(urls[13], self.add_output_message)
            model_15_name, model_15_image_url, model_15_editor_inner_link = fetch_mockup_details(urls[14], self.add_output_message)
            model_16_name, model_16_image_url, model_16_editor_inner_link = fetch_mockup_details(urls[15], self.add_output_message)
            model_17_name, model_17_image_url, model_17_editor_inner_link = fetch_mockup_details(urls[16], self.add_output_message)
            model_18_name, model_18_image_url, model_18_editor_inner_link = fetch_mockup_details(urls[17], self.add_output_message)
            model_19_name, model_19_image_url, model_19_editor_inner_link = fetch_mockup_details(urls[18], self.add_output_message)
            model_20_name, model_20_image_url, model_20_editor_inner_link = fetch_mockup_details(urls[19], self.add_output_message)
            model_21_name, model_21_image_url, model_21_editor_inner_link = fetch_mockup_details(urls[20], self.add_output_message)
            model_22_name, model_22_image_url, model_22_editor_inner_link = fetch_mockup_details(urls[21], self.add_output_message)
            model_23_name, model_23_image_url, model_23_editor_inner_link = fetch_mockup_details(urls[22], self.add_output_message)
            model_24_name, model_24_image_url, model_24_editor_inner_link = fetch_mockup_details(urls[23], self.add_output_message)
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
            },
            "model_9": {
                "name": model_9_name,
                "image_url": model_9_image_url,
                "editor_inner_link": model_9_editor_inner_link
            },
            "model_10": {
                "name": model_10_name,
                "image_url": model_10_image_url,
                "editor_inner_link": model_10_editor_inner_link
            },
            "model_11": {
                "name": model_11_name,
                "image_url": model_11_image_url,
                "editor_inner_link": model_11_editor_inner_link
            },
            "model_12": {
                "name": model_12_name,
                "image_url": model_12_image_url,
                "editor_inner_link": model_12_editor_inner_link
            },
            "model_13": {
                "name": model_13_name,
                "image_url": model_13_image_url,
                "editor_inner_link": model_13_editor_inner_link
            },
            "model_14": {
                "name": model_14_name,
                "image_url": model_14_image_url,
                "editor_inner_link": model_14_editor_inner_link
            },
            "model_15": {
                "name": model_15_name,
                "image_url": model_15_image_url,
                "editor_inner_link": model_15_editor_inner_link
            },
            "model_16": {
                "name": model_16_name,
                "image_url": model_16_image_url,
                "editor_inner_link": model_16_editor_inner_link
            },
            "model_17": {
                "name": model_17_name,
                "image_url": model_17_image_url,
                "editor_inner_link": model_17_editor_inner_link
            },
            "model_18": {
                "name": model_18_name,
                "image_url": model_18_image_url,
                "editor_inner_link": model_18_editor_inner_link
            },
            "model_19": {
                "name": model_19_name,
                "image_url": model_19_image_url,
                "editor_inner_link": model_19_editor_inner_link
            },
            "model_20": {
                "name": model_20_name,
                "image_url": model_20_image_url,
                "editor_inner_link": model_20_editor_inner_link
            },
            "model_21": {
                "name": model_21_name,
                "image_url": model_21_image_url,
                "editor_inner_link": model_21_editor_inner_link
            },
            "model_22": {
                "name": model_22_name,
                "image_url": model_22_image_url,
                "editor_inner_link": model_22_editor_inner_link
            },
            "model_23": {
                "name": model_23_name,
                "image_url": model_23_image_url,
                "editor_inner_link": model_23_editor_inner_link
            },
            "model_24": {
                "name": model_24_name,
                "image_url": model_24_image_url,
                "editor_inner_link": model_24_editor_inner_link
            }
            }
            with open(var_json_path, "w", encoding="utf-8") as f:
                json.dump(var_json_data, f, ensure_ascii=False, indent=2)
            self.add_output_message("Fetched mockup details and wrote var_v.json.", "success")
        
        step1_cdn = cdn_placeholder_image(self.step1_cdn_widget.text(),type='1')
        step2_cdn = cdn_placeholder_image(self.step2_cdn_widget.text(),type='2')
        step3_cdn = cdn_placeholder_image(self.step3_cdn_widget.text(),type='3')
        
        part5 = [line for line in self.segments[4].splitlines() if line.strip()]
        part5_title = part5[0].strip()
        part5_step1_a = part5[1].strip()
        part5_step1_b = part5[2].strip()
        
        part5_step2_a = part5[3].strip()
        part5_step2_b = part5[4].strip()
        
        part5_step3_a = part5[5].strip()
        part5_step3_b = part5[6].strip()
        
        
        part6 = [line for line in self.segments[5].splitlines() if line.strip()]
        
        part6_1_feature_cdn = cdn_placeholder_image(self.feature1_cdn_widget.text(),type='a')
        part6_2_feature_cdn = cdn_placeholder_image(self.feature2_cdn_widget.text(),type='b')
        part6_3_feature_cdn = cdn_placeholder_image(self.feature3_cdn_widget.text(),type='c')
        part6_4_feature_cdn = cdn_placeholder_image(self.feature4_cdn_widget.text(),type='d')
        
        part6_title = part6[0]
        
        part6_1_title = part6[1].strip()
        part6_1_a = part6[2].strip()
        part6_1_b = part6[3].strip()
        part6_1_button = part6[4].strip()
        # 根据给定的文案判断是try还是view，由于try的变种文案太多，所以用view来判断
        if part6_1_button.startswith("View"):
            part6_1_button_text = view_text
            part6_1_button_link = view_link_spicy
            part6_1_button_gtm = 'ga-seo_tools_view_all'
        else:
            part6_1_button_text = try_text
            part6_1_button_link = try_link_spicy
            part6_1_button_gtm = 'ga-seo_tools_try'

        part6_2_title = part6[5].strip()
        part6_2_a = part6[6].strip()
        part6_2_b = part6[7].strip()
        part6_2_button = part6[8].strip()
        if part6_2_button.startswith("View"):
            part6_2_button_text = view_text
            part6_2_button_link = view_link_spicy
            part6_2_button_gtm = 'ga-seo_tools_view_all'
        else:
            part6_2_button_text = try_text
            part6_2_button_link = try_link_spicy
            part6_2_button_gtm = 'ga-seo_tools_try'
        
        part6_3_title = part6[9].strip()
        part6_3_a = part6[10].strip()
        part6_3_b = part6[11].strip()
        part6_3_button = part6[12].strip()
        if part6_3_button.startswith("View"):
            part6_3_button_text = view_text
            part6_3_button_link = view_link_spicy
            part6_3_button_gtm = 'ga-seo_tools_view_all'
        else:
            part6_3_button_text = try_text
            part6_3_button_link = try_link_spicy
            part6_3_button_gtm = 'ga-seo_tools_try'
        
        part6_4_title = part6[13].strip()
        part6_4_a = part6[14].strip()
        part6_4_b = part6[15].strip()
        part6_4_button = part6[16].strip()
        if part6_4_button.startswith("View"):
            part6_4_button_text = view_text
            part6_4_button_link = view_link_spicy
            part6_4_button_gtm = 'ga-seo_tools_view_all'
        else:
            part6_4_button_text = try_text
            part6_4_button_link = try_link_spicy
            part6_4_button_gtm = 'ga-seo_tools_try'
        
        # FAQ环节
        part7 = self.segments[6]
        part7_block = parse_faq_text(part7)
        
        part7_q1 = part7_block[0]['question'].strip()
        part7_a1 = part7_block[0]['answer'].strip()
        
        part7_q2 = part7_block[1]['question'].strip()
        part7_a2 = part7_block[1]['answer'].strip()
        
        part7_q3 = part7_block[2]['question'].strip()
        part7_a3 = part7_block[2]['answer'].strip()
        
        part7_q4 = part7_block[3]['question'].strip()
        part7_a4 = part7_block[3]['answer'].strip()
        
        part7_q5 = part7_block[4]['question'].strip()
        part7_a5_raw = part7_block[4]['answer'].strip()
        part7_a5 = part7_a5_raw.replace(
            "pricing page", 
            '<a class="pac-ui-editor-a" href=/pricing target=_self gtm="" rel="noopener noreferrer">pricing page</a>'
        )
        
        part8_text = self.segments[7].splitlines()[0]
        
        folder_path = self.pics_path_widget.text()
        self.ensure_folder_exists(folder_path = folder_path)
        
        # 读取模板内容
        temp_path = get_resource_path('json_templates/mockup_resource.json')
        with open(temp_path, 'r', encoding='utf-8') as f:
            template_str = f.read()

        # 构建替换字典
        replace_dict = {
            "view_text": view_text,
            "view_link": view_link,
            "try_text": try_text,
            "try_link": try_link,
            "breadcrumb": breadcrumb,
            "breadcrumb_titlecase": breadcrumb_lower,
            "breadcrumb_lower": breadcrumb_lower,
            "part2_text": part2_text,
            "part4_title": part3_title,
            "part4_text": part3_text,
            #"part5_title": part4_title,
            "mockup1_cdn": model_1_image_url,
            "mockup1_text": model_1_name,
            "mockup1_link": model_1_editor_inner_link,
            "mockup2_cdn": model_2_image_url,
            "mockup2_text": model_2_name,
            "mockup2_link": model_2_editor_inner_link,
            "mockup3_cdn": model_3_image_url,
            "mockup3_text": model_3_name,
            "mockup3_link": model_3_editor_inner_link,
            "mockup4_cdn": model_4_image_url,
            "mockup4_text": model_4_name,
            "mockup4_link": model_4_editor_inner_link,
            "mockup5_cdn": model_5_image_url,
            "mockup5_text": model_5_name,
            "mockup5_link": model_5_editor_inner_link,
            "mockup6_cdn": model_6_image_url,
            "mockup6_text": model_6_name,
            "mockup6_link": model_6_editor_inner_link,
            "mockup7_cdn": model_7_image_url,
            "mockup7_text": model_7_name,
            "mockup7_link": model_7_editor_inner_link,
            "mockup8_cdn": model_8_image_url,
            "mockup8_text": model_8_name,
            "mockup8_link": model_8_editor_inner_link,
            "mockup9_cdn": model_9_image_url,
            "mockup9_text": model_9_name,
            "mockup9_link": model_9_editor_inner_link,
            "mockup10_cdn": model_10_image_url,
            "mockup10_text": model_10_name,
            "mockup10_link": model_10_editor_inner_link,
            "mockup11_cdn": model_11_image_url,
            "mockup11_text": model_11_name,
            "mockup11_link": model_11_editor_inner_link,
            "mockup12_cdn": model_12_image_url,
            "mockup12_text": model_12_name,
            "mockup12_link": model_12_editor_inner_link,
            "mockup13_cdn": model_13_image_url,
            "mockup13_text": model_13_name,
            "mockup13_link": model_13_editor_inner_link,
            "mockup14_cdn": model_14_image_url,
            "mockup14_text": model_14_name,
            "mockup14_link": model_14_editor_inner_link,
            "mockup15_cdn": model_15_image_url,
            "mockup15_text": model_15_name,
            "mockup15_link": model_15_editor_inner_link,
            "mockup16_cdn": model_16_image_url,
            "mockup16_text": model_16_name,
            "mockup16_link": model_16_editor_inner_link,
            "mockup17_cdn": model_17_image_url,
            "mockup17_text": model_17_name,
            "mockup17_link": model_17_editor_inner_link,
            "mockup18_cdn": model_18_image_url,
            "mockup18_text": model_18_name,
            "mockup18_link": model_18_editor_inner_link,
            "mockup19_cdn": model_19_image_url,
            "mockup19_text": model_19_name,
            "mockup19_link": model_19_editor_inner_link,
            "mockup20_cdn": model_20_image_url,
            "mockup20_text": model_20_name,
            "mockup20_link": model_20_editor_inner_link,
            "mockup21_cdn": model_21_image_url,
            "mockup21_text": model_21_name,
            "mockup21_link": model_21_editor_inner_link,
            "mockup22_cdn": model_22_image_url,
            "mockup22_text": model_22_name,
            "mockup22_link": model_22_editor_inner_link,
            "mockup23_cdn": model_23_image_url,
            "mockup23_text": model_23_name,
            "mockup23_link": model_23_editor_inner_link,
            "mockup24_cdn": model_24_image_url,
            "mockup24_text": model_24_name,
            "mockup24_link": model_24_editor_inner_link,
            "step1_cdn": step1_cdn,
            "step2_cdn": step2_cdn,
            "step3_cdn": step3_cdn,
            "step_title": part5_title,  
            "step1_1": part5_step1_a,
            "step1_2": part5_step1_b,
            "step2_1": part5_step2_a,
            "step2_2": part5_step2_b,
            "step3_1": part5_step3_a,
            "step3_2": part5_step3_b,
            "part6_title": part6_title,
            "feature1_1": part6_1_title,
            "feature1_cdn": part6_1_feature_cdn,
            "feature1_2": part6_1_a,
            "feature1_3": part6_1_b,
            "feature1_button_text" : part6_1_button_text,
            "feature1_button_link" : part6_1_button_link,
            "feature1_button_gtm" : part6_1_button_gtm,
            "feature2_1": part6_2_title,
            "feature2_cdn": part6_2_feature_cdn,
            "feature2_2": part6_2_a,
            "feature2_3": part6_2_b,
            "feature2_button_text" : part6_2_button_text,
            "feature2_button_link" : part6_2_button_link,
            "feature2_button_gtm" : part6_2_button_gtm,
            "feature3_1": part6_3_title,
            "feature3_cdn": part6_3_feature_cdn,
            "feature3_2": part6_3_a,
            "feature3_3": part6_3_b,
            "feature3_button_text" : part6_3_button_text,
            "feature3_button_link" : part6_3_button_link,
            "feature3_button_gtm" : part6_3_button_gtm,
            "feature4_1": part6_4_title,
            "feature4_cdn": part6_4_feature_cdn,
            "feature4_2": part6_4_a,
            "feature4_3": part6_4_b,
            "feature4_button_text" : part6_4_button_text,
            "feature4_button_link" : part6_4_button_link,
            "feature4_button_gtm" : part6_4_button_gtm,
            "q1": part7_q1,
            "a1": part7_a1,
            "q2": part7_q2,
            "a2": part7_a2,
            "q3": part7_q3,
            "a3": part7_a3,
            "q4": part7_q4,
            "a4": part7_a4,
            "q5": part7_q5,
            "a5": part7_a5,
            "part8": part8_text
        }

        # 替换所有{{key}}为对应值
        for key, value in replace_dict.items():
            if isinstance(value, str):
                # 使用json.dumps正确处理JSON字符串中的特殊字符
                value = json.dumps(value)[1:-1]  # 去掉json.dumps添加的外层引号
            template_str = template_str.replace(f"{{{{{key}}}}}", str(value))

        # 尝试解析为json
        try:
            json_obj = json.loads(template_str)
            json_string = json.dumps(json_obj, indent=2, ensure_ascii=False)
            # self.json_widget.setText(json_string)
            self.output_json = json_string
            QGuiApplication.clipboard().setText(json_string)
            self.add_output_message("JSON generated and copied to clipboard!", "success")
        except Exception as e:
            self.add_output_message(f"Error generating JSON: {e}", "error")
    
    def generate_json_action_mockup_tool(self):
        self.add_output_message("Generating JSON output...", "info")
        
        # 获取关键字段
        view_text = self.view_widget.text().split(":")[0].strip()
        view_link_raw = self.view_widget.text().split(":")[1].strip()
        view_link_spicy = f"{view_link_raw}"
        view_link = view_link_spicy
        
        try_text = self.try_widget.text().split(":")[0].strip()
        try_link_raw = self.try_widget.text().split(":")[1].strip() 
        try_link_spicy = f"{try_link_raw}"
        try_link = try_link_spicy
        
        breadcrumb = self.keywords_widget.text()
        breadcrumb_lower = breadcrumb.capitalize().replace("Ai", "AI").replace("ai", "AI").replace("3d", "3D")
        
        part2 = self.segments[1]
        part2_text = part2.splitlines()[1]
        
        mockup_list_1_name = self.mockup_list_1_name_widget.text().strip()
        mockup_list_1_number = self.mockup_list_1_number_widget.text()
        mockup_list_1_cdn = self.cover_cdn_widget.text()
        
        mockup_list_2_number = self.mockup_list_2_number_widget.text()
        mockup_list_2_cdn = self.cover_more_cdn_widget.text()
        
        if self.single_image_checkbox.isChecked():
            multiple_upload = 'false'
        else:
            multiple_upload = 'true'

        more_link = self.more_button_action_widget.text()
        
        if self.color_diy_checkbox.isChecked():
            has_cover_color = 'true'
            has_color = 'false'
            cover_colors = self.color_diy_choice_widget.text()
        else:
            has_cover_color = 'false'
            has_color = 'true'
            cover_colors = "1"
           
        mockup_type = self.mockup_type_widget.text()
         
        if mockup_type == 'Box':
            has_size = 'true'
        else:
            has_size = 'false'
            
        mockup_size = self.mockup_size_widget.text()
        if not mockup_size:
            mockup_size = "1"

        mockup_default_size = self.mockup_default_size_widget.text()
        if not mockup_default_size:
            mockup_default_size = "1"
        
        dieline_choose = self.dieline_choose_widget.text()
        if not dieline_choose:
            dieline_choose = "1"
        
        part3 = [line for line in self.segments[2].splitlines() if line.strip()]
        part3_title = part3[0]
        part3_text = process_text_with_links(part3[1:])
        
        
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
            model_1_name, model_1_image_url, model_1_editor_inner_link = fetch_mockup_details(urls[0], self.add_output_message)
            model_2_name, model_2_image_url, model_2_editor_inner_link = fetch_mockup_details(urls[1], self.add_output_message)
            model_3_name, model_3_image_url, model_3_editor_inner_link = fetch_mockup_details(urls[2], self.add_output_message)
            model_4_name, model_4_image_url, model_4_editor_inner_link = fetch_mockup_details(urls[3], self.add_output_message)
            model_5_name, model_5_image_url, model_5_editor_inner_link = fetch_mockup_details(urls[4], self.add_output_message)
            model_6_name, model_6_image_url, model_6_editor_inner_link = fetch_mockup_details(urls[5], self.add_output_message)
            model_7_name, model_7_image_url, model_7_editor_inner_link = fetch_mockup_details(urls[6], self.add_output_message)
            model_8_name, model_8_image_url, model_8_editor_inner_link = fetch_mockup_details(urls[7], self.add_output_message)
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
        
        step1_cdn = cdn_placeholder_image(self.step1_cdn_widget.text(),type='1')
        step2_cdn = cdn_placeholder_image(self.step2_cdn_widget.text(),type='2')
        step3_cdn = cdn_placeholder_image(self.step3_cdn_widget.text(),type='3')
        
        part5 = [line for line in self.segments[4].splitlines() if line.strip()]
        part5_title = part5[0].strip()
        part5_step1_a = part5[1].strip()
        part5_step1_b = part5[2].strip()
        
        part5_step2_a = part5[3].strip()
        part5_step2_b = part5[4].strip()
        
        part5_step3_a = part5[5].strip()
        part5_step3_b = part5[6].strip()
        
        
        part6 = [line for line in self.segments[5].splitlines() if line.strip()]
        
        part6_1_feature_cdn = cdn_placeholder_image(self.feature1_cdn_widget.text(),type='a')
        part6_2_feature_cdn = cdn_placeholder_image(self.feature2_cdn_widget.text(),type='b')
        part6_3_feature_cdn = cdn_placeholder_image(self.feature3_cdn_widget.text(),type='c')
        part6_4_feature_cdn = cdn_placeholder_image(self.feature4_cdn_widget.text(),type='d')
        
        part6_title = part6[0]
        
        part6_1_title = part6[1].strip()
        part6_1_a = part6[2].strip()
        part6_1_b = part6[3].strip()
        part6_1_button = part6[4].strip()
        # 根据给定的文案判断是try还是view，由于try的变种文案太多，所以用view来判断
        if part6_1_button.startswith("View"):
            part6_1_button_text = view_text
            part6_1_button_link = view_link_spicy
            part6_1_button_gtm = 'ga-seo_tools_view_all'
        else:
            part6_1_button_text = try_text
            part6_1_button_link = try_link_spicy
            part6_1_button_gtm = 'ga-seo_tools_try'

        part6_2_title = part6[5].strip()
        part6_2_a = part6[6].strip()
        part6_2_b = part6[7].strip()
        part6_2_button = part6[8].strip()
        if part6_2_button.startswith("View"):
            part6_2_button_text = view_text
            part6_2_button_link = view_link_spicy
            part6_2_button_gtm = 'ga-seo_tools_view_all'
        else:
            part6_2_button_text = try_text
            part6_2_button_link = try_link_spicy
            part6_2_button_gtm = 'ga-seo_tools_try'
        
        part6_3_title = part6[9].strip()
        part6_3_a = part6[10].strip()
        part6_3_b = part6[11].strip()
        part6_3_button = part6[12].strip()
        if part6_3_button.startswith("View"):
            part6_3_button_text = view_text
            part6_3_button_link = view_link_spicy
            part6_3_button_gtm = 'ga-seo_tools_view_all'
        else:
            part6_3_button_text = try_text
            part6_3_button_link = try_link_spicy
            part6_3_button_gtm = 'ga-seo_tools_try'
        
        part6_4_title = part6[13].strip()
        part6_4_a = part6[14].strip()
        part6_4_b = part6[15].strip()
        part6_4_button = part6[16].strip()
        if part6_4_button.startswith("View"):
            part6_4_button_text = view_text
            part6_4_button_link = view_link_spicy
            part6_4_button_gtm = 'ga-seo_tools_view_all'
        else:
            part6_4_button_text = try_text
            part6_4_button_link = try_link_spicy
            part6_4_button_gtm = 'ga-seo_tools_try'
        
        # FAQ环节
        part7 = self.segments[6]
        part7_block = parse_faq_text(part7) # 使用parse_faq_text函数处理过的文本会自动识别有序列表
        
        part7_q1 = part7_block[0]['question'].strip()
        part7_a1 = part7_block[0]['answer'].strip()
        
        part7_q2 = part7_block[1]['question'].strip()
        part7_a2 = part7_block[1]['answer'].strip()
        
        part7_q3 = part7_block[2]['question'].strip()
        part7_a3 = part7_block[2]['answer'].strip()
        
        part7_q4 = part7_block[3]['question'].strip()
        part7_a4 = part7_block[3]['answer'].strip()
        
        part7_q5 = part7_block[4]['question'].strip()
        part7_a5_raw = part7_block[4]['answer'].strip()
        part7_a5 = part7_a5_raw.replace(
            "pricing page", 
            '<a class="pac-ui-editor-a" href=/pricing target=_self gtm="" rel="noopener noreferrer">pricing page</a>'
        )
        
        part8_text = self.segments[7].splitlines()[0]
        
        folder_path = self.pics_path_widget.text()
        self.ensure_folder_exists(folder_path = folder_path)
        
        # 读取模板内容
        temp_path = get_resource_path('json_templates/mockup_tool.json')
        with open(temp_path, 'r', encoding='utf-8') as f:
            template_str = f.read()

        # 构建替换字典
        replace_dict = {
            "view_text": view_text,
            "view_link": view_link,
            "try_text": try_text,
            "try_link": try_link,
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
            "has_cover_color": has_cover_color,
            "mockup_type" : mockup_type,
            "has_size" : has_size,
            "mockup_size" : mockup_size,
            "mockup_default_size" : mockup_default_size,
            "dieline_choose" : dieline_choose,
            "has_color": has_color,
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
            "part6_1_button_text" : part6_1_button_text,
            "part6_1_button_link" : part6_1_button_link,
            "part6_1_button_gtm" : part6_1_button_gtm,
            "part6_2_title": part6_2_title,
            "part6_2_feature_cdn": part6_2_feature_cdn,
            "part6_2_a": part6_2_a,
            "part6_2_b": part6_2_b,
            "part6_2_button_text" : part6_2_button_text,
            "part6_2_button_link" : part6_2_button_link,
            "part6_2_button_gtm" : part6_2_button_gtm,
            "part6_3_title": part6_3_title,
            "part6_3_feature_cdn": part6_3_feature_cdn,
            "part6_3_a": part6_3_a,
            "part6_3_b": part6_3_b,
            "part6_3_button_text" : part6_3_button_text,
            "part6_3_button_link" : part6_3_button_link,
            "part6_3_button_gtm" : part6_3_button_gtm,
            "part6_4_title": part6_4_title,
            "part6_4_feature_cdn": part6_4_feature_cdn,
            "part6_4_a": part6_4_a,
            "part6_4_b": part6_4_b,
            "part6_4_button_text" : part6_4_button_text,
            "part6_4_button_link" : part6_4_button_link,
            "part6_4_button_gtm" : part6_4_button_gtm,
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
            if isinstance(value, str):
                # 使用json.dumps正确处理JSON字符串中的特殊字符
                value = json.dumps(value)[1:-1]  # 去掉json.dumps添加的外层引号
            template_str = template_str.replace(f"{{{{{key}}}}}", str(value))

        # 尝试解析为json
        try:
            json_obj = json.loads(template_str)
            json_string = json.dumps(json_obj, indent=2, ensure_ascii=False)
            # self.json_widget.setText(json_string)
            self.output_json = json_string
            QGuiApplication.clipboard().setText(json_string)
            self.add_output_message("JSON generated and copied to clipboard!", "success")
        except Exception as e:
            self.add_output_message(f"Error generating JSON: {e}", "error")
            
    def generate_json_action_mockup_landing_page(self):
        self.add_output_message("Generating JSON output...", "info")
        
        if self.whole_page_background_color_widget.text() is not None:
                whole_page_background_color = self.whole_page_background_color_widget.text() 
        else:
            whole_page_background_color = 'rgba(255, 255, 255, 1)'
            self.add_output_message('Since no background color is provided, the default value is rgba(255, 255, 255, 1)','warning')
        
        hover_show_up_distance_range = '>5000,<10000'
        
        part1 = [line for line in self.segments[1].splitlines() if line.strip()]
        part1_title = part1[0]
        part1_text = part1[1]
        
        part2 = [line for line in self.segments[2].splitlines() if line.strip()]
        part2_title = part2[0]
        part2_step1_1 = part2[1]
        part2_step1_2 = part2[2]
        
        part2_step2_1 = part2[3]
        part2_step2_2 = part2[4]
        
        part2_step3_1 = part2[5]
        part2_step3_2 = part2[6]
        
        part2_step1_cdn = cdn_placeholder_image(self.step1_cdn_widget.text(),type='1')
        part2_step2_cdn = cdn_placeholder_image(self.step2_cdn_widget.text(),type='2')
        part2_step3_cdn = cdn_placeholder_image(self.step3_cdn_widget.text(),type='3')
        
        
        part3 = [line for line in self.segments[3].splitlines() if line.strip()]
        part3_title = part3[0]
        part3_1_1 = part3[1]
        part3_1_2 = part3[2]
        part3_1_3 = part3[3]
        
        part3_2_1 = part3[4]
        part3_2_2 = part3[5]
        part3_2_3 = part3[6]
        
        part3_3_1 = part3[7]
        part3_3_2 = part3[8]
        part3_3_3 = part3[9]
        
        part3_4_1 = part3[10]
        part3_4_2 = part3[11]
        part3_4_3 = part3[12]
        
        feature_1_cdn = cdn_placeholder_image(self.feature1_cdn_widget.text(),type='a')
        feature_2_cdn = cdn_placeholder_image(self.feature2_cdn_widget.text(),type='b')
        feature_3_cdn = cdn_placeholder_image(self.feature3_cdn_widget.text(),type='c')
        feature_4_cdn = cdn_placeholder_image(self.feature4_cdn_widget.text(),type='d')
        
        part4 = self.segments[4]
        
        faq = parse_faq_text(part4)
        
        q1 = faq[0]['question'].strip()
        a1 = faq[0]['answer'].strip()
        
        q2 = faq[1]['question'].strip()
        a2 = faq[1]['answer'].strip()
        
        q3 = faq[2]['question'].strip()
        a3 = faq[2]['answer'].strip()
        
        q4 = faq[3]['question'].strip()
        a4 = faq[3]['answer'].strip()
        
        q5 = faq[4]['question'].strip()
        a5_raw = faq[4]['answer'].strip()
        a5 = a5_raw.replace(
            "pricing page", 
            '<a class="pac-ui-editor-a" href=/pricing rel="noopener noreferrer" target=_self>pricing page</a>'
        )
        
        folder_path = self.pics_path_widget.text()
        self.ensure_folder_exists(folder_path=folder_path)
        
        # 读取模板内容
        temp_path = get_resource_path('json_templates/mockup_landing.json')
        with open(temp_path,'r') as f:
            template_str = f.read()
        
        # 构建替换字典
        
        replace_dict = {
            "whole_page_background_color": whole_page_background_color,
            "hover_show_up_distance_range": hover_show_up_distance_range,
            "part1_title": part1_title,
            "part1_text": part1_text,
            "part2_title": part2_title,
            "part2_step1_1": part2_step1_1,
            "part2_step1_2": part2_step1_2,
            "part2_step2_1": part2_step2_1,
            "part2_step2_2": part2_step2_2,
            "part2_step3_1": part2_step3_1,
            "part2_step3_2": part2_step3_2,
            "part2_step1_cdn": part2_step1_cdn,
            "part2_step2_cdn": part2_step2_cdn,
            "part2_step3_cdn": part2_step3_cdn,
            "part3_title": part3_title,
            "part3_1_1": part3_1_1,
            "part3_1_2": part3_1_2,
            "part3_1_3": part3_1_3,
            "part3_2_1": part3_2_1,
            "part3_2_2": part3_2_2,
            "part3_2_3": part3_2_3,
            "part3_3_1": part3_3_1,
            "part3_3_2": part3_3_2,
            "part3_3_3": part3_3_3,
            "part3_4_1": part3_4_1,
            "part3_4_2": part3_4_2,
            "part3_4_3": part3_4_3,
            "feature_1_cdn": feature_1_cdn,
            "feature_2_cdn": feature_2_cdn,
            "feature_3_cdn": feature_3_cdn,
            "feature_4_cdn": feature_4_cdn,
            "q1": q1,
            "a1": a1,
            "q2": q2,
            "a2": a2,
            "q3": q3,
            "a3": a3,
            "q4": q4,
            "a4": a4,
            "q5": q5,
            "a5": a5,
        }
        
        # 替换所有{{key}}为对应值
        for key, value in replace_dict.items():
            if isinstance(value, str):
                # 使用json.dumps正确处理JSON字符串中的特殊字符
                value = json.dumps(value)[1:-1]  # 去掉json.dumps添加的外层引号
            template_str = template_str.replace(f"{{{{{key}}}}}", str(value))

        # 尝试解析为json
        try:
            json_obj = json.loads(template_str)
            json_string = json.dumps(json_obj, indent=2, ensure_ascii=False)
            # self.json_widget.setText(json_string)
            self.output_json = json_string
            QGuiApplication.clipboard().setText(json_string)
            self.add_output_message("JSON generated and copied to clipboard!", "success")
        except Exception as e:
            self.add_output_message(f"Error generating JSON: {e}", "error")
    
    def generate_json_action_universal_topic(self):
        self.add_output_message("Generating JSON output...", "info")
        
        # 获取关键字段

    def generate_json_action_tools(self):
        """
        Handles the generation of JSON for the 'TOOLS' page type.
        """
        self.add_output_message("Generating JSON for 'TOOLS' page type...", "info")
        
        csv_path = self.tools_csv_path_widget.text().strip()
        if not csv_path:
            self.add_output_message("Please select a TOOLS.csv file first.", "error")
            return

        # Define paths for the generator
        templates_path = get_resource_path('json_templates')

        # Generate the JSON string
        json_string = generate_tools_json(
            csv_path=csv_path,
            templates_path=templates_path,
            logger=self.add_output_message
        )

        if json_string:
            self.output_json = json_string
            QGuiApplication.clipboard().setText(json_string)
            self.add_output_message("JSON for 'TOOLS' generated and copied to clipboard!", "success")
        else:
            self.add_output_message("Failed to generate JSON for 'TOOLS'. Check logs for details.", "error")

    def iterate_json_action(self):
        self.add_output_message("Starting to replace the cdn placeholders.",'info')
        # 确保cdn组件中都包含了有效链接
        cdn_fields = [
            self.step1_cdn_widget,
            self.step2_cdn_widget,
            self.step3_cdn_widget,
            self.feature1_cdn_widget,
            self.feature2_cdn_widget,
            self.feature3_cdn_widget,
            self.feature4_cdn_widget
        ]
        empty_fields = []
        for widget in cdn_fields:
            if not widget.text():
                empty_fields.append(widget)
        
        if empty_fields:
            self.add_output_message(f'{len(empty_fields)} cdn addresses are not valid.','error')
            return
        else:
            self.add_output_message('All cdn fields are filled. Proceeding...','success')
            
            # 读取剪切板
            json_str = QGuiApplication.clipboard().text()
            
            # 替换
            replaced = iterate(json_str, 
                               self.step1_cdn_widget.text(),
                               self.step2_cdn_widget.text(),
                               self.step3_cdn_widget.text(),
                               self.feature1_cdn_widget.text(),
                               self.feature2_cdn_widget.text(),
                               self.feature3_cdn_widget.text(),
                               self.feature4_cdn_widget.text())
            
            self.add_output_message('Replace done.','success')
            
            # 将替换过的json传入剪切板
            QGuiApplication.clipboard().setText(replaced)
            self.add_output_message('Replace json copied to clipboard.','success')  
            

    def current_time(self):
        return datetime.now().strftime("%H:%M:%S")
    
    def manual_secret_configure(self):
        """
        打开一个对话框,允许用户输入并使用keyring保存凭证。
        """
        dialog = SCConfigDialog(self)
        if dialog.exec():  # Show the dialog and wait for user action
            # 对话框内部已经处理了所有保存逻辑
            self.add_output_message("Configuration saved successfully.", "success")
            QMessageBox.information(self, "Success", "All configurations have been securely saved.")
        else:
            self.add_output_message("Configuration cancelled by user.", "info")
            
    def ensure_folder_exists(self, folder_path):
        try:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                self.add_output_message(f"No {folder_path} folder detected. Created folder automatically.","info")
            else:
                self.add_output_message(f"Folder {folder_path} already exists.","info")
        except OSError as e:
            self.add_output_message(f"Error creating {folder_path} folder: {e}", "error")
            return False
        return True
    
    def check_nas_connection(self) -> bool | None:
        """
        检查是否能连接到NAS服务器
        """
        # 检查/Volumes/shared/pacdora.com路径是否存在且可访问
        if sys.platform.startswith('darwin'):
            # 对于MacOS，路径通常是/Volumes/shared/pacdora.com
            nas_path = "/Volumes/shared/pacdora.com"
            try:
                if os.path.exists(nas_path) and os.access(nas_path, os.R_OK):
                    self.add_output_message("成功连接到NAS服务器", "success")
                    return True
                else:
                    self.add_output_message("无法访问NAS服务器路径", "error") 
                    return False
            except Exception as e:
                self.add_output_message(f"检查NAS连接时发生错误: {str(e)}", "error")
                return False  
        elif os.name == "nt":
            # 对于Windows，路径通常是//nas01.tools.baoxiaohe.com/shared/pacdora.com
            try:
                if os.path.exists(nas_path) and os.access(nas_path, os.R_OK):
                    self.add_output_message("成功连接到NAS服务器", "success")
                    return True
                else:
                    self.add_output_message("无法访问NAS服务器路径", "error") 
                    return False
            except Exception as e:
                self.add_output_message(f"检查NAS连接时发生错误: {str(e)}", "error")
                return False
        else:
            self.add_output_message("unsupported os detected","warning")
    
    def prepare_folder(self):
        """
        如果批量复制了notion中所有标题名表格，此时会有一个n行1列的表格被复制，
        我们需要将这个表格中的所有标题名提取出来，作为文件夹名.
        判断系统，然后在对应的nas路径中创建对应的文件夹
        """
        # 从剪贴板获取数据
        clipboard_text = QGuiApplication.clipboard().text()
        # 假设数据是一个简单的列表，每个项目占一行
        titles = clipboard_text.strip().split('\n')
        self.add_output_message(f"Detected {len(titles)} titles from clipboard.","info")
        
        try:
            self.add_output_message("Checking NAS connection.","info")
            self.check_nas_connection()
        except:
            self.add_output_message("NAS connection check failed.","error")
            return
        
        # 判断系统是Windows还是Mac
        if sys.platform.startswith('darwin'):
            # 对于MacOS，路径通常是/Volumes/shared/pacdora.com
            self.add_output_message("MacOS detected.","info")
            for title in titles:
                folder_path = os.path.join("/Volumes/shared/pacdora.com",title.strip().replace(" ", "-"))
                self.ensure_folder_exists(folder_path)
                self.add_output_message(f"Created folder: {folder_path}", "success")
        elif os.name == 'nt':
            # 对于Windows，路径通常是//nas01.tools.baoxiaohe.com/shared/pacdora.com
            self.add_output_message("Windows detected.","info")
            for title in titles:
                folder_path = os.path.join("//nas01.tools.baoxiaohe.com/shared/pacdora.com",title.strip().replace(" ", "-"))
                self.ensure_folder_exists(folder_path)
                self.add_output_message(f"Created folder: {folder_path}", "success")
        else:
            self.add_output_message(f"Detected unsupported system: {sys.platform}", "info")
            raise Exception("Unknown system. Please check your system.")
        
    def uploader_upload_folder_bot(self, given_folder_path : str = None, is_pass_cdn : bool = True):
        """
        增量上传文件夹中的图片。
        - 读取现有的cdn.json（如果存在）。
        - 只上传本地存在但json中缺少链接的图片。
        - 如果遇到意料之外的图片（命名不符合所有预设的字段），则在cdn.json中另外保存，按照其文件名+cdn链接的格式。
        - 更新并保存cdn.json。
        """
        
        # 可接受指定文件夹路径的上传
        if given_folder_path is not None:
            folder_path = given_folder_path
            
        # 如不存在 创建文件夹
        if not os.path.isdir(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
                self.add_output_message(f"Folder did not exist. Created: {folder_path}", "info")
            except Exception as e:
                self.add_output_message(f"Invalid folder path and failed to create folder: {e}", "error")
                return

        self.add_output_message("Starting incremental image upload...", "info")
        
        json_path = os.path.join(folder_path, 'cdn.json')
        
        # 1. 读取现有CDN记录或创建新模板
        cdn_data = {
            "cover_cdn": "", "cover_more_cdn": "",
            "mockup_list_1_number": "", "mockup_list_2_number": "",
            "step1_cdn": "", "step2_cdn": "", "step3_cdn": "",
            "feature1_cdn": "", "feature2_cdn": "", "feature3_cdn": "", "feature4_cdn": "",
            "banner_cdn": ""
        }
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    cdn_data.update(json.load(f)) # 用文件中的数据更新模板
                self.add_output_message("Loaded existing cdn.json.", "info")
            except json.JSONDecodeError:
                self.add_output_message("Warning: cdn.json is corrupted. Starting with a fresh record.", "warning")

        # 2. 扫描本地图片并仅上传缺失的图片
        try:
            image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
            total_images = len(image_files)
            self.add_output_message(f"Found {total_images} images in the folder.", "info")

            for i, image_name in enumerate(image_files):
                filename, _ = os.path.splitext(image_name)
                key_to_update = None
                
                # 建立文件名到JSON键的映射
                if filename == 'banner':
                    key_to_update = 'banner_cdn'
                elif filename in ['1', '2', '3']:
                    key_to_update = f"step{filename}_cdn"
                elif filename in ['a', 'b', 'c', 'd']:
                    key_to_update = f"feature{ord(filename) - ord('a') + 1}_cdn"
                elif "mockup" or "custom" in filename:
                    parts = filename.replace("_", " ").split()
                    number = parts[-1] if parts[-1].isdigit() else ""
                    if "more" in parts:
                        key_to_update = "cover_more_cdn"
                        if number and not cdn_data.get("mockup_list_2_number"):
                            cdn_data["mockup_list_2_number"] = number
                    else:
                        key_to_update = "cover_cdn"
                        if number and not cdn_data.get("mockup_list_1_number"):
                            cdn_data["mockup_list_1_number"] = number
                
                # 如果是未知图片，使用文件名作为key
                if key_to_update is None:
                    key_to_update = filename

                # 检查是否需要上传
                if not cdn_data.get(key_to_update):
                    self.add_output_message(f"Uploading ({i+1}/{total_images}): {image_name}...", "info")
                    file_path = os.path.join(folder_path, image_name)
                    cdn_url = self.aws_upload.upload_file(file_path)
                    
                    if cdn_url:
                        cdn_data[key_to_update] = cdn_url
                        self.add_output_message(f"Upload successful: {cdn_url}", "success")
                    else:
                        self.add_output_message(f"Upload failed for {image_name}.", "error")
                else:
                    self.add_output_message(f"Skipping ({i+1}/{total_images}): {image_name} (already uploaded).", "info")

            # 3. 回写JSON文件
            with open(json_path, 'w') as f:
                json.dump(cdn_data, f, indent=4)
            
            self.add_output_message(f"CDN records updated successfully at {json_path}", "success")
            
            # 4. 更新UI界面
            if is_pass_cdn:
                self.pass_cdn_records()

        except Exception as e:
            self.add_output_message(f"An error occurred during upload: {e}", "error")
        
    def uploader_upload_folder(self, is_pass_cdn : bool = True):
        """
        增量上传文件夹中的图片。
        - 读取现有的cdn.json（如果存在）。
        - 只上传本地存在但json中缺少链接的图片。
        - 如果遇到意料之外的图片（命名不符合所有预设的字段），则在cdn.json中另外保存，按照其文件名+cdn链接的格式。
        - 更新并保存cdn.json。
        """
        from threading import Thread

        def worker():
            folder_path = self.pics_path_widget.text()
                
            # 如不存在 创建文件夹
            if not os.path.isdir(folder_path):
                try:
                    os.makedirs(folder_path, exist_ok=True)
                    self.add_output_message(f"Folder did not exist. Created: {folder_path}", "info")
                except Exception as e:
                    self.add_output_message(f"Invalid folder path and failed to create folder: {e}", "error")
                    return

            self.add_output_message("Starting incremental image upload...", "info")
            
            json_path = os.path.join(folder_path, 'cdn.json')
            
            # 1. 读取现有CDN记录或创建新模板
            cdn_data = {
                "cover_cdn": "", "cover_more_cdn": "",
                "mockup_list_1_number": "", "mockup_list_2_number": "",
                "step1_cdn": "", "step2_cdn": "", "step3_cdn": "",
                "feature1_cdn": "", "feature2_cdn": "", "feature3_cdn": "", "feature4_cdn": "",
                "banner_cdn": ""
            }
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r') as f:
                        cdn_data.update(json.load(f)) # 用文件中的数据更新模板
                    self.add_output_message("Loaded existing cdn.json.", "info")
                except json.JSONDecodeError:
                    self.add_output_message("Warning: cdn.json is corrupted. Starting with a fresh record.", "warning")

            # 2. 扫描本地图片并仅上传缺失的图片
            try:
                image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                total_images = len(image_files)
                self.add_output_message(f"Found {total_images} images in the folder.", "info")

                for i, image_name in enumerate(image_files):
                    filename, _ = os.path.splitext(image_name)
                    key_to_update = None
                    
                    # 建立文件名到JSON键的映射
                    if filename == 'banner':
                        key_to_update = 'banner_cdn'
                    elif filename in ['1', '2', '3']:
                        key_to_update = f"step{filename}_cdn"
                    elif filename in ['a', 'b', 'c', 'd']:
                        key_to_update = f"feature{ord(filename) - ord('a') + 1}_cdn"
                    elif "mockup" or "custom" in filename:
                        parts = filename.replace("_", " ").split()
                        number = parts[-1] if parts[-1].isdigit() else ""
                        if "more" in parts:
                            key_to_update = "cover_more_cdn"
                            if number and not cdn_data.get("mockup_list_2_number"):
                                cdn_data["mockup_list_2_number"] = number
                        else:
                            key_to_update = "cover_cdn"
                            if number and not cdn_data.get("mockup_list_1_number"):
                                cdn_data["mockup_list_1_number"] = number
                    
                    # 如果是未知图片，使用文件名作为key
                    if key_to_update is None:
                        key_to_update = filename

                    # 检查是否需要上传
                    if not cdn_data.get(key_to_update):
                        self.add_output_message(f"Uploading ({i+1}/{total_images}): {image_name}...", "info")
                        file_path = os.path.join(folder_path, image_name)
                        cdn_url = self.aws_upload.upload_file(file_path)
                        
                        if cdn_url:
                            cdn_data[key_to_update] = cdn_url
                            self.add_output_message(f"Upload successful: {cdn_url}", "success")
                        else:
                            self.add_output_message(f"Upload failed for {image_name}.", "error")
                    else:
                        self.add_output_message(f"Skipping ({i+1}/{total_images}): {image_name} (already uploaded).", "info")

                # 3. 回写JSON文件
                with open(json_path, 'w') as f:
                    json.dump(cdn_data, f, indent=4)
                
                self.add_output_message(f"CDN records updated successfully at {json_path}", "success")
                
                # 4. 更新UI界面
                if is_pass_cdn:
                    self.pass_cdn_records()

            except Exception as e:
                self.add_output_message(f"An error occurred during upload: {e}", "error")
        
        Thread(target=worker, daemon=True).start()
            
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
        json_path = os.path.join(folder_path, 'cdn.json')
        if not os.path.exists(json_path):
            self.add_output_message("cdn.json not found. Cannot populate fields.", "warning")
            return
            
        with open(json_path,"r") as f:
            cdn_json = json.load(f)
        # 提取json中的每一行内容并赋入widget
        try:
            self.mockup_list_1_number_widget.setText(cdn_json.get("mockup_list_1_number", ""))
            self.mockup_list_2_number_widget.setText(cdn_json.get("mockup_list_2_number", ""))
            self.cover_cdn_widget.setText(cdn_json.get("cover_cdn", ""))
            self.cover_more_cdn_widget.setText(cdn_json.get("cover_more_cdn", ""))
            self.step1_cdn_widget.setText(cdn_json.get("step1_cdn", ""))
            self.step2_cdn_widget.setText(cdn_json.get("step2_cdn", ""))
            self.step3_cdn_widget.setText(cdn_json.get("step3_cdn", ""))
            self.feature1_cdn_widget.setText(cdn_json.get("feature1_cdn", ""))
            self.feature2_cdn_widget.setText(cdn_json.get("feature2_cdn", ""))
            self.feature3_cdn_widget.setText(cdn_json.get("feature3_cdn", ""))
            self.feature4_cdn_widget.setText(cdn_json.get("feature4_cdn", ""))
            self.banner_cdn_widget.setText(cdn_json.get("banner_cdn", ""))
            self.add_output_message("UI fields populated from cdn.json.", "success")
        except Exception as e:
            self.add_output_message(f"Passing cdn addresses failed: {str(e)}","error")
            
    def load_mockup_sizes(self):
        """
        Loads mockup sizes from size.csv.
        """
        try:
            csv_path = get_writable_path('size.csv')
            sizes = parse_size_csv(csv_path)
            self.add_output_message("Successfully loaded mockup sizes from size.csv.", "success")
            return sizes
        except Exception as e:
            self.add_output_message(f"Error loading mockup sizes: {e}", "error")
            return None

    def update_mockup_size_info(self):
        """
        Updates the mockup size and default size widgets based on the selected mockup type.
        """
        selected_mockup = self.mockup_type_combo.currentText()
        
        if selected_mockup == "-- Select a Type --":
            self.mockup_size_widget.setText("")
            self.mockup_default_size_widget.setText("")
            return

        if self.mockup_sizes_data and selected_mockup in self.mockup_sizes_data:
            sizes = self.mockup_sizes_data[selected_mockup]
            
            # Format sizes as [[w, h, d], ...]
            formatted_sizes = [[s['width'], s['height'], s['depth']] for s in sizes]
            self.mockup_size_widget.setText(json.dumps(formatted_sizes))
            
            # Find the index of the default size
            default_index = -1
            for i, size in enumerate(sizes):
                if size['is_default']:
                    default_index = i
                    break
            
            if default_index != -1:
                self.mockup_default_size_widget.setText(str(default_index + 1)) # Use 1-based index
            else:
                self.mockup_default_size_widget.setText("") # Clear if no default
            
            self.add_output_message(f"Updated size info for {selected_mockup}", "info")
            
    def open_canary_url(self):
        try:
            target = self.file_path_widget.text()
            type = self.page_type.currentText()
            if type == 'Mockup tool' or 'Universal topic':
                url_type = 'tools/' 
            elif type == 'Mockup resource':
                url_type = 'resource/'
            elif type == 'Mockup landing page':
                url_type = 'mockups/'
            elif type == "Dieline landing page":
                url_type = "dielines/"
            else:
                url_type = ''
            url = f'https://canary.pacdora.com/{url_type}{target}'
            webbrowser.open(url)
            self.add_output_message('Successfully opened the canary website.','success')
        except Exception as e:
            self.add_output_message('Error during opening canary website.','error')

    def on_page_type_changed(self):
        """
        Shows or hides the TOOLS-specific widgets based on the selected page type.
        """
        is_tools_selected = self.page_type.currentText() == "TOOLS"
        self.tools_options_widget.setVisible(is_tools_selected)

    def browse_tools_csv(self):
        """
        Opens a file dialog to select the TOOLS.csv file.
        """
        self.add_output_message("Browsing for TOOLS CSV file...", "info")
        file_path, _ = QFileDialog.getOpenFileName(self, "Select TOOLS CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.tools_csv_path_widget.setText(file_path)
            self.add_output_message(f"Selected TOOLS CSV: {file_path}", "success")
        else:
            self.add_output_message("No file selected.", "warning")

            
def create_main_window() -> QMainWindow:
    """
    创建并返回主应用窗口。
    """
    window = WSA()
    return window

def main():
    """
    主入口函数，用于独立运行app.py进行测试。
    """
    app = QApplication(sys.argv)
    # 应用Material主题
    apply_stylesheet(app, theme='light_orange.xml')
    
    main_window = create_main_window()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
