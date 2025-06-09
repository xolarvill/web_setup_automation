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

        # View Button输入框
        view_layout = QHBoxLayout()
        view_layout.addWidget(QLabel("VIEW button:"))
        self.view_input = QLineEdit()
        #self.view_input.setText("view_text_placeholder: view_link_placeholder")
        view_layout.addWidget(self.view_input)
        main_layout.addLayout(view_layout)

        # Try Button输入框
        try_layout = QHBoxLayout()
        try_layout.addWidget(QLabel("TRY button:"))
        self.try_input = QLineEdit()
        #self.try_input.setText("try_text_placeholder: try_link_placeholder")
        try_layout.addWidget(self.try_input)
        main_layout.addLayout(try_layout)
        
        # 设置统一的输入框和下拉框宽度
        input_width = 550
        self.pics_path_input.setFixedWidth(input_width)
        self.url_path_input.setFixedWidth(input_width)
        self.page_type.setFixedWidth(input_width)
        self.view_input.setFixedWidth(input_width)
        self.try_input.setFixedWidth(input_width)
        

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
        self.output_box.setPlaceholderText("Program output will be displayed here...\n- Use BROWSE FOLDER to locate the picture folder.\n- OPEN FOLDER can open the selected folder for inspection.\n- After copying the whole text in google docs, return to the app and click UPDATE to automatically parse and retrieve.\n- Click GENERATE JSON for final result.\n- Click the C button to clear messages.")
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
        
    def browse_folder(self):
        self.output_box.append(f"#########\nBrowsing action triggered at {self.current_time()}")
        # Set default folder for QFileDialog
        if sys.platform.startswith('darwin'):
            # Use NAS path or Desktop as default on macOS
            default_folder = "/Volumes/shared/pacdora.com/"
            if not os.path.isdir(default_folder):
                self.output_box.append(f"<b>Warning</b>: Cannot reach the NAS folder ({default_folder}). Using Desktop instead.")
                default_folder = os.path.expanduser("~/Desktop")
        else:
            default_folder = "//nas01.tools.baoxiaohe.com/shared/pacdora.com/"
        # Check if default folder exists, else fallback to home
        if not os.path.isdir(default_folder):
            self.output_box.append(f"<b>Warning</b>: Cannot reach the default folder ({default_folder}). Using home directory instead.")
            default_folder = os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", default_folder)
        if folder:
            self.pics_path_input.setText(folder)
            self.output_box.append(f"Selected folder: {folder}")
    
    def open_folder(self):
        self.output_box.append(f"#########\nOpening action triggered at {self.current_time()}")
        folder_path = self.pics_path_input.text().strip()
        if not folder_path or not os.path.isdir(folder_path):
            self.output_box.append("<b>Warning</b>: Please select a valid folder path before opening.")
            return
        if sys.platform.startswith('darwin'):
            os.system(f'open "{folder_path}"')
        elif os.name == 'nt':
            # Handle UNC paths and convert slashes
            unc_path = folder_path.replace('/', '\\')
            if not unc_path.startswith('\\\\'):
                # If path starts with //, convert to \\
                if unc_path.startswith('\\'):
                    unc_path = '\\\\' + unc_path.lstrip('\\')
            try:
                os.startfile(unc_path)
            except Exception as e:
                self.output_box.append(f"Error opening folder: {e}")
        elif os.name == 'posix':
            os.system(f'xdg-open "{folder_path}"')
        else:
            self.output_box.append("Warning: Unsupported OS for opening folders.")

    def update_action(self):
        self.output_box.append(f"#########\nUpdate action triggered at {self.current_time()}")
        clipboard = QGuiApplication.clipboard()
        clipboard_text = clipboard.text()
        cutout_keywords_nextline = ["URL","Title","Meta description","Breadcrumb"]
        cutout_keywords_currentline = ["View all", "Make a"]
        if clipboard_text:
            self.output_box.append("Clipboard content captured, shown as below:")
            preview_start = clipboard_text[:30]
            self.output_box.append(f"--------------------------\n{preview_start}...\n--------------------------")
            dict_parsed1 = extract_cutout_nextline(text = clipboard_text, keywords = cutout_keywords_nextline)
            dict_parse2 = extract_cutout_currentline(text = clipboard_text, keywords = cutout_keywords_currentline)
            if dict_parsed1 and dict_parse2:
                merged = dict_parsed1.copy()
                merged.update(dict_parse2)
                self.output_box.append("The copied article has been parsed. ")
            else:
                self.output_box.append("<b>Warning</b>: No keywords have been detected. Make sure you have copied the correct article.")
        else:
            self.output_box.append("<b>Warning</b>: Clipboard is empty or does not contain text.")
        
    def generate_json_action(self):
        self.output_box.append(f"#########\nGenerate JSON action triggered at {self.current_time()}")
        criterion = False
        if criterion:
            self.output_box.append("json generated and copied to clipboard")
        else:
            self.output_box.append("<b>Warning</b>: the criterions are not fulfilled. Check again please.")

    def current_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 应用Material主题
    apply_stylesheet(app, theme='light_orange.xml')  # 使用Material主题

    window = WSA()
    window.show()
    sys.exit(app.exec())