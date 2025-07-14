# 标准库导入
import os
import sys
import json
import re
from datetime import datetime

# 第三方库导入
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QFrame, QSizePolicy, QToolButton, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QSize, QParallelAnimationGroup, QPropertyAnimation, QAbstractAnimation, Signal
from PySide6.QtGui import QGuiApplication


class HorizontalCollapsibleTabs(QWidget):
    """
    水平排列的折叠面板切换器 + 垂直内容区域展示。
    ---
    - 水平排列多个折叠面板的触发器（标签）。
    - 点击一个触发器时，在下方内容区域展开其对应内容。
    - 自动收起其他已展开的面板，保证只有一个面板处于展开状态。
    
    参数:
    - parent: QWidget, 父组件
    - parent_window: QWidget, 主窗口引用(用于调整窗口大小)
    - tab_height: int, 预设的标签页按钮高度，如果为0则自动计算
    ---
    使用示例：
    ```python
    # ... (in your main window setup)
    tabs = HorizontalCollapsibleTabs(tab_height=35)

    # Tab 1
    content1 = QWidget()
    layout1 = QVBoxLayout(content1)
    layout1.addWidget(QLabel("This is the content for Tab 1"))
    tabs.add_tab("Tab 1", content1)

    # Add the tabs widget to your main layout
    main_layout.addWidget(tabs)
    """
    def __init__(self, parent=None, parent_window=None, tab_height=0):
        super().__init__(parent)
        self.parent_window = parent_window
        self.tab_height = tab_height
        self.tabs = []
        self.current_index = -1
        self.content_height = 0
        self.is_expanded = False

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 标签按钮容器
        self.tabs_layout = QHBoxLayout()
        self.tabs_layout.setSpacing(5)
        
        # 内容区域容器 - 使用固定高度控制
        self.content_container = QWidget()
        self.content_container.setFixedHeight(0)  # 初始高度为0
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addLayout(self.tabs_layout)
        main_layout.addWidget(self.content_container)

        # 动画控制
        self.animation_group = QParallelAnimationGroup(self)
        self.content_animation = QPropertyAnimation(self.content_container, b"maximumHeight")
        self.content_animation.setDuration(500)
        self.animation_group.addAnimation(self.content_animation)
        
        # 窗口大小动画
        if self.parent_window:
            self.window_animation = QPropertyAnimation(self.parent_window, b"size")
            self.window_animation.setDuration(500)
            self.animation_group.addAnimation(self.window_animation)

    def add_tab(self, title: str, widget: QWidget):
        """
        添加一个新的标签页和其对应的内容小部件。
        """
        # 创建标签按钮
        button = QToolButton(text=title, checkable=True, checked=False)
        if self.tab_height > 0:
            button.setFixedHeight(self.tab_height)
        
        button.setStyleSheet("QToolButton { border: none; }")
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        button.setArrowType(Qt.RightArrow)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # 连接按钮点击事件
        tab_index = len(self.tabs)
        button.pressed.connect(lambda: self._on_tab_clicked(tab_index))
        
        # 添加到布局
        self.tabs_layout.addWidget(button)
        self.content_layout.addWidget(widget)
        
        # 初始隐藏内容
        widget.hide()
        
        # 存储标签信息
        tab_info = {
            'button': button,
            'widget': widget,
            'content_height': widget.sizeHint().height()
        }
        self.tabs.append(tab_info)

    def _on_tab_clicked(self, tab_index):
        """
        处理标签点击事件
        """
        clicked_tab = self.tabs[tab_index]
        
        if self.current_index == tab_index and self.is_expanded:
            # 点击当前已展开的标签，收起
            self._collapse_all()
        else:
            # 展开新标签
            self._expand_tab(tab_index)

    def _expand_tab(self, tab_index):
        """
        展开指定标签
        """
        # 更新按钮状态
        for i, tab in enumerate(self.tabs):
            if i == tab_index:
                tab['button'].setChecked(True)
                tab['button'].setArrowType(Qt.DownArrow)
                tab['widget'].show()
            else:
                tab['button'].setChecked(False)
                tab['button'].setArrowType(Qt.RightArrow)
                tab['widget'].hide()
        
        self.current_index = tab_index
        self.content_height = self.tabs[tab_index]['content_height']
        
        # 设置动画
        self.content_animation.setStartValue(0 if not self.is_expanded else self.content_container.height())
        self.content_animation.setEndValue(self.content_height)
        
        if self.parent_window:
            current_size = self.parent_window.size()
            height_diff = self.content_height - (self.content_container.height() if self.is_expanded else 0)
            new_height = current_size.height() + height_diff
            self.window_animation.setStartValue(current_size)
            self.window_animation.setEndValue(QSize(current_size.width(), new_height))
        
        self.is_expanded = True
        self.animation_group.start()

    def _collapse_all(self):
        """
        收起所有标签
        """
        # 更新按钮状态
        for tab in self.tabs:
            tab['button'].setChecked(False)
            tab['button'].setArrowType(Qt.RightArrow)
            tab['widget'].hide()
        
        # 设置动画
        self.content_animation.setStartValue(self.content_container.height())
        self.content_animation.setEndValue(0)
        
        if self.parent_window:
            current_size = self.parent_window.size()
            new_height = current_size.height() - self.content_height
            self.window_animation.setStartValue(current_size)
            self.window_animation.setEndValue(QSize(current_size.width(), new_height))
        
        self.current_index = -1
        self.is_expanded = False
        self.animation_group.start()


class CollapsibleBox(QWidget):
    """
    可折叠框组件类
    ---
    功能:
    - 创建一个可以展开/折叠的容器组件
    - 支持动画效果
    - 可以包含任意布局内容
    
    参数:
    - title: str, 折叠框标题
    - parent: QWidget, 父组件
    - parent_window: QWidget, 主窗口引用(保留兼容性，但不再用于窗口大小调整)
    - button_height: int, 预设的按钮高度
    
    ```python
    # Create a collapsible box with a specific button height
    collapsible_box = CollapsibleBox("My Box", button_height=40)
    ```
    
    """
    expanded = Signal()

    def __init__(self, title="", parent=None, parent_window=None, button_height=0):
        super(CollapsibleBox, self).__init__(parent)
        self.parent_window = parent_window
        self.content_height = 0

        self.toggle_button = QToolButton(
            text=title, checkable=True, checked=False
        )
        if button_height > 0:
            self.toggle_button.setFixedHeight(button_height)
            
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QParallelAnimationGroup(self)

        self.content_area = QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        self.content_area.setFrameShape(QFrame.NoFrame)

        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        # Add animations for the box itself only (removed window animation)
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self.content_area, b"maximumHeight")
        )
        
        self.toggle_animation.finished.connect(self._on_animation_finished)


    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            Qt.DownArrow if not checked else Qt.RightArrow
        )

        # Removed window animation logic - content will expand within its container
        self.toggle_animation.setDirection(
            QAbstractAnimation.Forward
            if not checked
            else QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def _on_animation_finished(self):
        if self.toggle_animation.direction() == QAbstractAnimation.Forward:
            self.expanded.emit()

    def collapse(self):
        if self.toggle_button.isChecked():
            self.toggle_button.setChecked(False)
            self.on_pressed()

    def setContentLayout(self, layout):
        # Clean up old layout
        if self.content_area.layout() is not None:
            QWidget().setLayout(self.content_area.layout())
        
        self.content_area.setLayout(layout)
        self.content_height = layout.sizeHint().height()
        
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        
        # Stop any running animation before reconfiguring
        self.toggle_animation.stop()

        # Configure animations for the box itself (now only 3 animations)
        for i in range(3):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + self.content_height)

        # Configure the animation for the content area specifically
        content_animation = self.toggle_animation.animationAt(2)
        content_animation.setStartValue(0)
        content_animation.setEndValue(self.content_height)



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
