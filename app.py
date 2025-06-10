import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QLineEdit, QComboBox, QPushButton, QFileDialog, QTextEdit)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from qt_material import apply_stylesheet  # 导入qt-material库
import os
from datetime import datetime
from PySide6.QtGui import QGuiApplication
from parse import extract_cutout_nextline, extract_cutout_currentline
from PySide6.QtCore import QTimer


# ...existing code...

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
        input_container.setFixedWidth(550)
        input_container.setFixedHeight(32)

        self.line_edit = QLineEdit(input_container)
        self.line_edit.setGeometry(0, 0, 490, 32)
        if placeholder is not None:
            self.line_edit.setPlaceholderText(placeholder)

        self.copy_btn = QPushButton("📋", input_container)
        self.copy_btn.setGeometry(495, 2, 50, 28)
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
            self.copy_btn.setText("✔️")
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




class WSA(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web Setup Automation")
        self.setMinimumSize(700, 600)  # 增加窗口大小以适应输出框
        self.setWindowIcon(QIcon("resources/icon.png"))  # 可选：添加图标文件

        # 中心小部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Page Type下拉菜单
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("Type:"))
        self.page_type = QComboBox()
        self.page_type.addItems(["Mockup tool", "Mockup resource", "Mockup content", "Dieline tool", "Dieline resource", "TOOLS","Landing page"])
        self.page_type.setCurrentIndex(0)
        page_layout.addWidget(self.page_type)
        main_layout.addLayout(page_layout)
        
        # Pics Path输入框
        pics_path_layout = QHBoxLayout()
        pics_path_layout.addWidget(QLabel("Pics Path:"))
        self.pics_path_input = QLineEdit()
        self.pics_path_input.setPlaceholderText("Enter the path of your pics folder here. OR use the Browse button.")
        pics_path_layout.addWidget(self.pics_path_input)
        main_layout.addLayout(pics_path_layout)
        
        # URL Path输入框
        url_path_layout = QHBoxLayout()
        url_path_layout.addWidget(QLabel("URL Path:"))
        self.url_path_input = QLineEdit()
        self.url_path_input.setPlaceholderText("This is the short fix in the url link.")
        url_path_layout.addWidget(self.url_path_input)
        main_layout.addLayout(url_path_layout)
        
        # 文件路径
        self.file_path_widget = LabeledLineEditWithCopy("文件路径")
        main_layout.addWidget(self.file_path_widget)
        
        # 浏览器title
        self.title_widget = LabeledLineEditWithCopy("浏览器title")
        main_layout.addWidget(self.title_widget)
        
        # 网页描述
        self.description_widget = LabeledLineEditWithCopy("网页描述")
        main_layout.addWidget(self.description_widget)
        
        # 网页关键词
        self.keywords_widget = LabeledLineEditWithCopy("网页关键词")
        main_layout.addWidget(self.keywords_widget)
        
        # View
        self.view_widget = LabeledLineEditWithCopy("View")
        main_layout.addWidget(self.view_widget)
        
        # Try
        self.try_widget = LabeledLineEditWithCopy("Try")
        main_layout.addWidget(self.try_widget)
        
        # 设置统一的输入框和下拉框宽度
        input_width = 550
        self.pics_path_input.setFixedWidth(input_width)
        self.url_path_input.setFixedWidth(input_width)
        self.page_type.setFixedWidth(input_width)
        

        # 按钮布局（分两行，手动分配按钮）
        button_layout1 = QHBoxLayout()
        button_layout2 = QHBoxLayout()

        # 第一行按钮
        buttons_row1 = [
            ("Browse folder", self.browse_folder),
            ("Open folder", self.open_folder)
        ]
        for text, callback in buttons_row1:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            button_layout1.addWidget(btn)

        # 第二行按钮
        buttons_row2 = [
            ("Update", self.update_action),
            ("Generate JSON", self.generate_json_action)
        ]
        for text, callback in buttons_row2:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            button_layout2.addWidget(btn)

        # 添加按钮布局
        main_layout.addLayout(button_layout1)
        main_layout.addLayout(button_layout2)

        # 运行结果输出框和清除按钮容器 Output container
        output_container = QWidget()
        output_container.setMinimumHeight(120)
        output_container.setMaximumHeight(200)
        output_container.setLayout(None)  # 允许绝对定位

        # 输出框
        self.output_box = QTextEdit(output_container)
        self.output_box.setReadOnly(True)
        self.output_box.setPlaceholderText(
            "Program output will be displayed here...\n\n"
            "• Use BROWSE FOLDER to locate the picture folder\n"
            "• OPEN FOLDER can open the selected folder for inspection\n"
            "• After copying text from Google Docs, click UPDATE to parse\n"
            "• Click GENERATE JSON for final result\n"
            "• Use Clear button to reset messages\n"
            "• Use 📋 button to copy the text"
            )
        self.output_box.setGeometry(0, 0, 650, 180)  # 预设大小

        # 清除按钮
        self.clear_button = QPushButton("C", output_container)
        self.clear_button.setFixedSize(60, 28)
        # 放在output_box右下角
        self.clear_button.setGeometry(self.output_box.width() - 70, self.output_box.height() - 38, 60, 28)
        self.clear_button.clicked.connect(self.output_box.clear)

        # 响应窗口大小变化，动态调整按钮位置
        def resize_event(event):
            self.output_box.setGeometry(0, 0, output_container.width(), output_container.height())
            self.clear_button.setGeometry(
            output_container.width() - 70,
            output_container.height() - 38,
            60, 28
            )
        output_container.resizeEvent = resize_event

        main_layout.addWidget(output_container)

        # 调整布局间距
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
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
        <div style="margin: 8px 0; padding: 12px; border-radius: 8px; border-left: 3px solid {color};">
            <div style="font-weight: 600; color: {color}; margin-bottom: 4px;">
            {icon} {timestamp}
            </div>
            <div style="color: #1D1D1F; line-height: 1.3;">
            {message}
            </div>
        </div>
        """
        self.output_box.append(formatted_message)

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
            self.pics_path_input.setText(folder)
            self.add_output_message(f"Selected folder: {folder}", "success")
        else:
            self.add_output_message("No folder selected", "warning")
    
    def open_folder(self):
        self.add_output_message("Opening folder...", "info")
        folder_path = self.pics_path_input.text().strip()
        
        if not folder_path or not os.path.isdir(folder_path):
            self.add_output_message("Please select a valid folder path before opening.", "warning")
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
        cutout_keywords_nextline = ["URL", "Title", "Meta description", "Breadcrumb"]
        cutout_keywords_currentline = ["View all", "Make a"]
        
        if clipboard_text:
            preview_start = clipboard_text[:50]
            self.add_output_message(f"Clipboard content captured: {preview_start}...", "info")
            
            try:
                dict_parsed1 = extract_cutout_nextline(text=clipboard_text, keywords=cutout_keywords_nextline)
                dict_parse2 = extract_cutout_currentline(text=clipboard_text, keywords=cutout_keywords_currentline)
                
                if dict_parsed1 and dict_parse2:
                    merged = dict_parsed1.copy()
                    merged.update(dict_parse2)
                    self.add_output_message("Article parsed successfully! Keywords detected and extracted.", "success")
                else:
                    self.add_output_message("No keywords detected. Please ensure you've copied the correct article. This could happen when the article is not correctly formatted. Go check it.", "warning")
            except Exception as e:
                self.add_output_message(f"Error parsing content: {e}", "error")
        else:
            self.add_output_message("Clipboard is empty or does not contain text.", "warning")
        
    def generate_json_action(self):
        self.add_output_message("Generating JSON output...", "info")
        
        # Check if all required fields are filled
        required_fields = [
            (self.pics_path_input.text().strip(), "Pictures Path"),
            (self.url_path_input.text().strip(), "URL Path"),
        ]
        
        missing_fields = [field_name for field_value, field_name in required_fields if not field_value]
        
        if missing_fields:
            self.add_output_message(f"Missing required fields: {', '.join(missing_fields)}", "warning")
            return
        
        # Simulate JSON generation (replace with actual logic)
        criterion = True  # Replace with actual validation logic
        
        if criterion:
            self.add_output_message("JSON generated successfully and copied to clipboard!", "success")
            # Here you would implement the actual JSON generation and clipboard copying
        else:
            self.add_output_message("Generation failed. Please check all requirements are met.", "error")

    def current_time(self):
        return datetime.now().strftime("%H:%M:%S")
        
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 应用Material主题
    apply_stylesheet(app, theme='light_orange.xml')  # 使用Material主题

    window = WSA()
    window.show()
    sys.exit(app.exec())