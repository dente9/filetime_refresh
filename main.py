# -*- coding: utf-8 -*-
import sys
import os
import datetime
import pytz
from PySide6.QtWidgets import (
    QApplication, QWidget, QFileDialog, QMessageBox, QVBoxLayout, 
    QPushButton, QLabel, QSizePolicy, QLayout
)
from PySide6.QtCore import Qt, Signal, QCoreApplication
from PySide6.QtGui import QFont
from refresh_time import adjust_directory_times, modifyFileTime, set_directory_times_uniformly  # 导入新函数

# 导入生成的 UI 类
from ui_main import Ui_Form

class DragDropButton(QPushButton):
    """支持拖放的自定义按钮组件"""
    pathChanged = Signal(str, list)  # 信号：传递路径和文件列表
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 设置按钮样式
        self.setStyleSheet("""
            QPushButton {
                border: 2px dashed #aaa;
                border-radius: 15px;
                padding: 25px;
                font-size: 16px;
                background-color: #f8f8f8;
                min-height: 80px;
                min-width: 250px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # 设置字体
        font = QFont()
        font.setBold(True)
        self.setFont(font)

    def dragEnterEvent(self, event):
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """处理拖放事件"""
        urls = event.mimeData().urls()
        file_paths = []
        folder_path = ""
        
        for url in urls:
            if url.isLocalFile():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    file_paths.append(path)
                elif os.path.isdir(path):
                    folder_path = path
        
        # 发出信号
        self.pathChanged.emit(folder_path, file_paths)
        event.acceptProposedAction()

class FolderTimeAdjuster(QWidget):
    def __init__(self):
        super().__init__()

        # 初始化 UI
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # 设置窗口标题
        self.setWindowTitle("文件夹/文件时间调整工具")
        
        # 设置窗口最小大小
        self.setMinimumSize(400, 450)

        # 替换普通按钮为支持拖放的按钮
        self.drop_button = DragDropButton("拖放文件夹或文件，或点击选择", self)
        
        # 获取主布局
        layout = self.ui.verticalLayout_2
        
        # 替换原按钮
        index = layout.indexOf(self.ui.pushButton_path)
        if index != -1:
            # 保存布局参数
            stretch = layout.stretch(index)
            
            # 移除原按钮
            layout.takeAt(index)
            self.ui.pushButton_path.deleteLater()
            
            # 添加新按钮
            layout.insertWidget(index, self.drop_button, stretch=stretch)
        
        # 连接信号槽
        self.drop_button.clicked.connect(self.select_path)
        self.drop_button.pathChanged.connect(self.handle_dropped_path)
        
        # 设置执行按钮
        self.ui.pushButton_enter.clicked.connect(self.adjust_times)
        self.ui.pushButton_enter.setEnabled(False)
        
        # 设置时间编辑器
        self.ui.dateTimeEdit_timeinput.setDateTime(datetime.datetime.now())
        self.ui.dateTimeEdit_timeinput.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        
        # 初始化变量
        self.selected_folder = ""
        self.selected_files = []
        self.time_changed = False  # 跟踪时间是否被修改过
        
        # 设置复选框默认状态
        self.ui.checkBox_file_select_change.setChecked(False)  # 默认文件夹模式
        self.ui.checkBox_modelchange.setChecked(False)         # 默认时间差模式
        
        # 连接复选框状态变化信号
        self.ui.checkBox_file_select_change.stateChanged.connect(self.toggle_file_folder_mode)
        self.ui.checkBox_modelchange.stateChanged.connect(self.toggle_time_mode)
        
        # 连接时间编辑器变化信号
        self.ui.dateTimeEdit_timeinput.dateTimeChanged.connect(self.mark_time_changed)
        
        # 更新按钮文本
        self.update_button_text()

    def toggle_file_folder_mode(self, state):
        """切换文件夹/文件模式"""
        # state == Qt.Checked 表示文件模式
        # state == Qt.Unchecked 表示文件夹模式
        self.clear_selection()
        self.update_button_text()

    def toggle_time_mode(self, state):
        """切换时间差/整体修改模式"""
        # state == Qt.Checked 表示整体修改模式
        # state == Qt.Unchecked 表示时间差模式
        # 不需要立即操作，在执行时处理
        pass

    def mark_time_changed(self):
        """标记时间已被用户修改"""
        self.time_changed = True

    def update_button_text(self):
        """根据当前模式更新按钮文本"""
        if self.ui.checkBox_file_select_change.isChecked():
            # 文件模式
            self.drop_button.setText("拖放文件，或点击选择文件")
        else:
            # 文件夹模式
            self.drop_button.setText("拖放文件夹，或点击选择文件夹")

    def clear_selection(self):
        """清除当前选择"""
        self.selected_folder = ""
        self.selected_files = []
        self.update_button_text()
        self.ui.pushButton_enter.setEnabled(False)

    def handle_dropped_path(self, folder_path, file_paths):
        """处理拖放的文件/文件夹路径"""
        if self.ui.checkBox_file_select_change.isChecked():
            # 文件模式
            if file_paths:
                self.set_file_paths(file_paths)
            elif folder_path:
                # 如果拖放的是文件夹但当前是文件模式，提示错误
                QMessageBox.warning(self, "错误", "当前为文件模式，请拖放文件！")
        else:
            # 文件夹模式
            if folder_path:
                self.set_folder_path(folder_path)
            elif file_paths:
                # 如果拖放的是文件但当前是文件夹模式，使用文件所在目录
                folder_path = os.path.dirname(file_paths[0])
                if os.path.isdir(folder_path):
                    self.set_folder_path(folder_path)

    def set_folder_path(self, folder_path):
        """设置选择的文件夹路径"""
        if not os.path.isdir(folder_path):
            QMessageBox.warning(self, "错误", "选择的路径不是有效的文件夹！")
            return

        self.selected_folder = folder_path
        self.selected_files = []  # 清空文件列表
        
        # 更新按钮文本
        display_name = os.path.basename(folder_path)
        if len(folder_path) > 30:
            display_path = "..." + folder_path[-27:]
        else:
            display_path = folder_path
            
        self.drop_button.setText(display_name)
        self.drop_button.setToolTip(folder_path)
        
        # 更新执行按钮文本
        self.ui.pushButton_enter.setText(f"执行时间调整: {display_name}")
        self.ui.pushButton_enter.setEnabled(True)

    def set_file_paths(self, file_paths):
        """设置选择的文件路径"""
        valid_files = [path for path in file_paths if os.path.isfile(path)]
        if not valid_files:
            QMessageBox.warning(self, "错误", "没有选择有效的文件！")
            return
            
        self.selected_files = valid_files
        self.selected_folder = ""  # 清空文件夹路径
        
        # 更新按钮文本
        if len(valid_files) == 1:
            file_name = os.path.basename(valid_files[0])
            if len(file_name) > 30:
                display_text = f"..." + file_name[-27:]
            else:
                display_text = file_name
        else:
            display_text = f"{len(valid_files)}个文件"
            
        self.drop_button.setText(display_text)
        self.drop_button.setToolTip("\n".join(valid_files))
        
        # 更新执行按钮文本
        self.ui.pushButton_enter.setText(f"执行时间调整: {display_text}")
        self.ui.pushButton_enter.setEnabled(True)

    def select_path(self):
        """打开文件/文件夹选择对话框"""
        if self.ui.checkBox_file_select_change.isChecked():
            # 文件模式
            file_paths, _ = QFileDialog.getOpenFileNames(
                self,
                "选择文件",
                os.path.expanduser("~"),
                "All Files (*.*)"
            )
            if file_paths:
                self.set_file_paths(file_paths)
        else:
            # 文件夹模式
            folder_path = QFileDialog.getExistingDirectory(
                self, 
                "选择文件夹", 
                os.path.expanduser("~"),
                options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )
            if folder_path:
                self.set_folder_path(folder_path)

    def adjust_times(self):
        """执行时间调整操作"""
        # 获取用户选择的时间（如果用户修改过时间）
        if self.time_changed:
            custom_time = self.ui.dateTimeEdit_timeinput.dateTime().toPython()
        else:
            # 使用当前系统时间
            custom_time = datetime.datetime.now()
        
        # 添加时区信息
        local_tz = datetime.datetime.now().astimezone().tzinfo
        custom_time = custom_time.replace(tzinfo=local_tz)
        
        try:
            # 显示等待消息
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.drop_button.setText("处理中，请稍候...")
            self.ui.pushButton_enter.setEnabled(False)
            QCoreApplication.processEvents()

            success_count = 0
            total_count = 0
            
            if not self.ui.checkBox_file_select_change.isChecked():
                # 文件夹模式
                if self.ui.checkBox_modelchange.isChecked():
                    # 整体修改模式 - 所有内容设置为相同时间
                    success_count, total_count = set_directory_times_uniformly(self.selected_folder, custom_time)
                else:
                    # 时间差模式 - 保持相对时间差
                    success_count, total_count = adjust_directory_times(self.selected_folder, custom_time)
            else:
                # 文件模式 - 总是整体修改
                total_count = len(self.selected_files)
                for file_path in self.selected_files:
                    try:
                        # 使用modifyFileTime设置文件时间（三个时间都设置为custom_time）
                        if modifyFileTime(file_path, custom_time, custom_time, custom_time):
                            success_count += 1
                        else:
                            print(f"处理文件 {file_path} 时失败（modifyFileTime返回False）")
                    except Exception as e:
                        print(f"处理文件 {file_path} 时出错: {str(e)}")

            # 恢复 UI
            QApplication.restoreOverrideCursor()
            self.ui.pushButton_enter.setEnabled(True)

            # 显示结果
            if success_count == total_count:
                QMessageBox.information(self, "成功", 
                    f"时间调整成功完成！\n"
                    f"共处理 {total_count} 个项目，全部成功。")
            else:
                QMessageBox.warning(self, "部分成功", 
                    f"时间调整完成！\n"
                    f"共处理 {total_count} 个项目，成功 {success_count} 个，失败 {total_count - success_count} 个。\n\n"
                    "失败原因可能是文件被占用或权限不足。")

            # 更新按钮文本
            if not self.ui.checkBox_file_select_change.isChecked():
                # 文件夹模式
                self.drop_button.setText(f"完成! {os.path.basename(self.selected_folder)}")
                self.ui.pushButton_enter.setText(f"执行时间调整: {os.path.basename(self.selected_folder)}")
            else:
                if len(self.selected_files) == 1:
                    file_name = os.path.basename(self.selected_files[0])
                    self.drop_button.setText(f"完成! {file_name}")
                    self.ui.pushButton_enter.setText(f"执行时间调整: {file_name}")
                else:
                    self.drop_button.setText(f"完成! {len(self.selected_files)}个文件")
                    self.ui.pushButton_enter.setText(f"执行时间调整: {len(self.selected_files)}个文件")

        except Exception as e:
            QApplication.restoreOverrideCursor()
            self.ui.pushButton_enter.setEnabled(True)

            QMessageBox.critical(self, "错误", 
                f"处理过程中发生错误:\n{str(e)}")

            # 恢复按钮文本
            if not self.ui.checkBox_file_select_change.isChecked():
                # 文件夹模式
                self.drop_button.setText(os.path.basename(self.selected_folder))
            else:
                if len(self.selected_files) == 1:
                    self.drop_button.setText(os.path.basename(self.selected_files[0]))
                else:
                    self.drop_button.setText(f"{len(self.selected_files)}个文件")

        # 重置时间修改标记
        self.time_changed = False

if __name__ == "__main__":
    # 增加递归深度限制
    import sys
    sys.setrecursionlimit(10000)

    app = QApplication(sys.argv)

    # 设置应用样式
    app.setStyle("Fusion")

    # 设置应用字体
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)

    window = FolderTimeAdjuster()
    window.show()
    sys.exit(app.exec())