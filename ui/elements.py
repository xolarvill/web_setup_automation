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
    
    ---
    使用示例：
    ```python
    # ... (in your main window setup)
    tabs = HorizontalCollapsibleTabs()

    # Tab 1
    content1 = QWidget()
    layout1 = QVBoxLayout(content1)
    layout1.addWidget(QLabel("This is the content for Tab 1"))
    tabs.add_tab("Tab 1", content1)

    # Tab 2
    content2 = QWidget()
    layout2 = QVBoxLayout(content2)
    layout2.addWidget(QLabel("This is the content for Tab 2"))
    tabs.add_tab("Tab 2", content2)

    # Add the tabs widget to your main layout
    main_layout.addWidget(tabs)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabs = []
        self.current_index = -1

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs_layout = QHBoxLayout()
        self.tabs_layout.setSpacing(5)
        
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addLayout(self.tabs_layout)
        main_layout.addWidget(self.content_container)

    def add_tab(self, title: str, widget: QWidget):
        """
        添加一个新的标签页和其对应的内容小部件。
        """
        box = CollapsibleBox(title=title)
        box.setContentLayout(widget.layout())
        
        self.tabs_layout.addWidget(box.toggle_button)
        self.content_layout.addWidget(box.content_area)
        
        box.content_area.hide()

        box.expanded.connect(lambda b=box: self._on_box_expanded(b))
        self.tabs.append(box)

    def _on_box_expanded(self, expanded_box):
        """
        当一个面板展开时，收起所有其他面板。
        """
        for i, box in enumerate(self.tabs):
            if box is expanded_box:
                self.current_index = i
                box.content_area.show()
            else:
                box.collapse()
                box.content_area.hide()
        
        # 调整布局
        self.content_layout.activate()


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
    - parent_window: QWidget, 主窗口引用(用于调整窗口大小)
    
    ```python
    # Create a collapsible box with a title
    collapsible_box = CollapsibleBox("My Collapsible Box")

    # Create a layout for the content of the box
    content_layout = QVBoxLayout()
    content_layout.addWidget(QLabel("This is the content of the box."))
    content_layout.addWidget(QPushButton("A button"))

    # Set the content layout for the box
    collapsible_box.setContentLayout(content_layout)

    # Add the collapsible box to your main layout
    main_layout.addWidget(collapsible_box)
    ```
    
    """
    expanded = Signal()

    def __init__(self, title="", parent=None, parent_window=None):
        super(CollapsibleBox, self).__init__(parent)
        self.parent_window = parent_window
        self.content_height = 0

        self.toggle_button = QToolButton(
            text=title, checkable=True, checked=False
        )
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(Qt.RightArrow)
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

        # Add animations for the box itself
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self.content_area, b"maximumHeight")
        )
        # Add animation for the parent window if it exists
        if self.parent_window:
            self.window_animation = QPropertyAnimation(self.parent_window, b"size")
            self.toggle_animation.addAnimation(self.window_animation)
        
        self.toggle_animation.finished.connect(self._on_animation_finished)


    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            Qt.DownArrow if not checked else Qt.RightArrow
        )

        # Set start/end values for window animation right before starting
        if self.parent_window:
            self.window_animation.setDuration(500)
            current_size = self.parent_window.size()
            if not checked:  # Expanding
                self.window_animation.setStartValue(current_size)
                self.window_animation.setEndValue(
                    QSize(current_size.width(), current_size.height() + self.content_height)
                )
            else:  # Collapsing
                # When running BACKWARD, it animates from END to START.
                # We want to go from current_size to current_size - content_height.
                # So, END should be current_size, and START should be current_size - content_height.
                self.window_animation.setStartValue(
                    QSize(current_size.width(), current_size.height() - self.content_height)
                )
                self.window_animation.setEndValue(current_size)

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

        # Configure animations for the box itself
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

