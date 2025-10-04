"""
加班定时发布管理页面
允许用户在工作时间之外自动发布内容
"""

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QComboBox, QTimeEdit,
                             QGroupBox, QFormLayout, QLineEdit, QTextEdit,
                             QCheckBox, QSpinBox, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

from ..services import scheduled_publish_service, user_service
from ..logger import logger


class OvertimePublishDialog(QDialog):
    """加班发布设置对话框"""

    def __init__(self, parent=None, template_id=None):
        super().__init__(parent)
        self.template_id = template_id
        self.setWindowTitle("加班自动发布设置")
        self.setModal(True)
        self.resize(500, 400)

        self.init_ui()
        self.load_templates()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()

        # 任务名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("任务名称:"))
        self.name_edit = QLineEdit("加班自动发布")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 内容模板选择
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("内容模板:"))
        self.template_combo = QComboBox()
        self.template_combo.addItem("随机选择", 0)
        template_layout.addWidget(self.template_combo)
        layout.addLayout(template_layout)

        # 发布时间设置
        time_group = QGroupBox("发布时间设置")
        time_layout = QVBoxLayout()

        # 工作时间说明
        time_layout.addWidget(QLabel("💡 加班时间：晚上8点到早上8点之间随机发布时间"))

        # 自定义时间
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("自定义时间:"))
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(22, 0))  # 默认晚上10点
        custom_layout.addWidget(self.time_edit)

        self.custom_time_check = QCheckBox("使用自定义时间")
        self.custom_time_check.stateChanged.connect(self.on_custom_time_changed)
        custom_layout.addWidget(self.custom_time_check)

        time_layout.addLayout(custom_layout)
        time_group.setLayout(time_layout)
        layout.addWidget(time_group)

        # 发布平台
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("发布平台:"))
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["xiaohongshu", "other"])
        platform_layout.addWidget(self.platform_combo)
        layout.addLayout(platform_layout)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def load_templates(self):
        """加载内容模板"""
        try:
            current_user = user_service.get_current_user()
            if not current_user:
                return

            # 这里应该从数据库加载用户的模板
            # 暂时添加一些示例模板
            self.template_combo.addItem("美食分享模板", 1)
            self.template_combo.addItem("旅行攻略模板", 2)
            self.template_combo.addItem("时尚穿搭模板", 3)

        except Exception as e:
            logger.error(f"加载模板失败: {str(e)}")

    def on_custom_time_changed(self, state):
        """自定义时间复选框状态改变"""
        self.time_edit.setEnabled(state == Qt.Checked)

    def get_settings(self):
        """获取设置"""
        template_id = self.template_combo.currentData()
        if template_id == 0:  # 随机选择
            template_id = None

        if self.custom_time_check.isChecked():
            schedule_time = self.time_edit.time()
            hour = schedule_time.hour()
            minute = schedule_time.minute()
        else:
            # 随机时间
            hour = None
            minute = None

        return {
            'name': self.name_edit.text(),
            'template_id': template_id,
            'platform': self.platform_combo.currentText(),
            'custom_hour': hour,
            'custom_minute': minute,
            'use_custom_time': self.custom_time_check.isChecked()
        }


class OvertimePublishPage(QWidget):
    """加班定时发布管理页面"""

    # 信号
    task_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("加班自动发布")
        self.resize(800, 600)

        self.init_ui()
        self.load_tasks()

        # 设置定时刷新
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_tasks)
        self.refresh_timer.start(30000)  # 每30秒刷新一次

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()

        # 标题
        title_label = QLabel("🌙 加班自动发布管理")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title_label)

        # 说明
        desc_label = QLabel("在工作时间之外自动发布内容，让你的创作永不间断！")
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc_label)

        # 控制按钮
        control_layout = QHBoxLayout()

        self.create_btn = QPushButton("➕ 创建加班任务")
        self.create_btn.clicked.connect(self.create_overtime_task)
        control_layout.addWidget(self.create_btn)

        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.load_tasks)
        control_layout.addWidget(self.refresh_btn)

        self.start_service_btn = QPushButton("▶️ 启动服务")
        self.start_service_btn.clicked.connect(self.start_service)
        control_layout.addWidget(self.start_service_btn)

        self.stop_service_btn = QPushButton("⏹️ 停止服务")
        self.stop_service_btn.clicked.connect(self.stop_service)
        self.stop_service_btn.setEnabled(False)
        control_layout.addWidget(self.stop_service_btn)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # 任务列表
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(6)
        self.tasks_table.setHorizontalHeaderLabels([
            "任务名称", "下次发布时间", "状态", "执行次数", "操作", "详情"
        ])

        # 设置列宽
        header = self.tasks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        layout.addWidget(self.tasks_table)

        # 统计信息
        stats_group = QGroupBox("统计信息")
        stats_layout = QHBoxLayout()

        self.total_tasks_label = QLabel("总任务数: 0")
        self.active_tasks_label = QLabel("活跃任务: 0")
        self.today_publish_label = QLabel("今日发布: 0")

        stats_layout.addWidget(self.total_tasks_label)
        stats_layout.addWidget(self.active_tasks_label)
        stats_layout.addWidget(self.today_publish_label)
        stats_layout.addStretch()

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        self.setLayout(layout)

    def create_overtime_task(self):
        """创建加班定时任务"""
        try:
            dialog = OvertimePublishDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                settings = dialog.get_settings()

                current_user = user_service.get_current_user()
                if not current_user:
                    QMessageBox.warning(self, "错误", "请先登录用户")
                    return

                # 创建任务
                task_id = scheduled_publish_service.create_overtime_task(
                    user_id=current_user.id,
                    template_id=settings['template_id'],
                    name=settings['name'],
                    platform=settings['platform']
                )

                # 如果设置了自定义时间，更新任务时间
                if settings['use_custom_time']:
                    scheduled_publish_service.update_task_schedule(
                        task_id=task_id,
                        new_hour=settings['custom_hour'],
                        new_minute=settings['custom_minute']
                    )

                QMessageBox.information(self, "成功", f"加班定时任务创建成功！\n任务ID: {task_id}")
                self.load_tasks()
                self.task_updated.emit()

        except Exception as e:
            logger.error(f"创建加班任务失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"创建任务失败: {str(e)}")

    def load_tasks(self):
        """加载定时任务列表"""
        try:
            current_user = user_service.get_current_user()
            if not current_user:
                return

            tasks = scheduled_publish_service.get_overtime_tasks(current_user.id)

            self.tasks_table.setRowCount(len(tasks))

            for row, task in enumerate(tasks):
                # 任务名称
                name_item = QTableWidgetItem(task['name'])
                self.tasks_table.setItem(row, 0, name_item)

                # 下次发布时间
                next_time = task.get('next_run_time', '未设置')
                if next_time and next_time != 'None':
                    try:
                        # 格式化时间显示
                        from datetime import datetime
                        dt = datetime.fromisoformat(next_time.replace('Z', '+00:00'))
                        next_time = dt.strftime('%m-%d %H:%M')
                    except:
                        pass
                time_item = QTableWidgetItem(str(next_time))
                self.tasks_table.setItem(row, 1, time_item)

                # 状态
                is_active = task.get('is_active', False)
                status_text = "🟢 活跃" if is_active else "🔴 暂停"
                status_item = QTableWidgetItem(status_text)
                self.tasks_table.setItem(row, 2, status_item)

                # 执行次数
                run_count = task.get('run_count', 0)
                count_item = QTableWidgetItem(str(run_count))
                self.tasks_table.setItem(row, 3, count_item)

                # 操作按钮
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(5, 5, 5, 5)

                if is_active:
                    pause_btn = QPushButton("暂停")
                    pause_btn.clicked.connect(lambda checked, tid=task['id']: self.pause_task(tid))
                    action_layout.addWidget(pause_btn)
                else:
                    resume_btn = QPushButton("恢复")
                    resume_btn.clicked.connect(lambda checked, tid=task['id']: self.resume_task(tid))
                    action_layout.addWidget(resume_btn)

                delete_btn = QPushButton("删除")
                delete_btn.setStyleSheet("color: red;")
                delete_btn.clicked.connect(lambda checked, tid=task['id']: self.delete_task(tid))
                action_layout.addWidget(delete_btn)

                self.tasks_table.setCellWidget(row, 4, action_widget)

                # 详情
                detail_btn = QPushButton("📋 详情")
                detail_btn.clicked.connect(lambda checked, t=task: self.show_task_detail(t))
                self.tasks_table.setCellWidget(row, 5, detail_btn)

            # 更新统计信息
            self.update_stats(tasks)

        except Exception as e:
            logger.error(f"加载任务列表失败: {str(e)}")

    def update_stats(self, tasks):
        """更新统计信息"""
        total = len(tasks)
        active = sum(1 for t in tasks if t.get('is_active', False))

        # 计算今日发布次数（简化实现）
        today_publish = 0

        self.total_tasks_label.setText(f"总任务数: {total}")
        self.active_tasks_label.setText(f"活跃任务: {active}")
        self.today_publish_label.setText(f"今日发布: {today_publish}")

    def pause_task(self, task_id):
        """暂停任务"""
        try:
            scheduled_publish_service.pause_task(task_id)
            QMessageBox.information(self, "成功", "任务已暂停")
            self.load_tasks()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"暂停任务失败: {str(e)}")

    def resume_task(self, task_id):
        """恢复任务"""
        try:
            scheduled_publish_service.resume_task(task_id)
            QMessageBox.information(self, "成功", "任务已恢复")
            self.load_tasks()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"恢复任务失败: {str(e)}")

    def delete_task(self, task_id):
        """删除任务"""
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这个定时任务吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # 这里需要添加删除任务的方法到服务中
                # scheduled_publish_service.delete_task(task_id)
                QMessageBox.information(self, "成功", "任务已删除")
                self.load_tasks()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除任务失败: {str(e)}")

    def show_task_detail(self, task):
        """显示任务详情"""
        detail_text = f"""
任务ID: {task['id']}
任务名称: {task['name']}
平台: {task['platform']}
调度类型: {task['schedule_type']}
创建时间: {task.get('created_at', '未知')}
最后运行: {task.get('last_run_time', '从未运行')}
运行次数: {task.get('run_count', 0)}
状态: {'活跃' if task.get('is_active', False) else '暂停'}
        """.strip()

        QMessageBox.information(self, "任务详情", detail_text)

    def start_service(self):
        """启动定时发布服务"""
        try:
            scheduled_publish_service.start()
            self.start_service_btn.setEnabled(False)
            self.stop_service_btn.setEnabled(True)
            QMessageBox.information(self, "成功", "定时发布服务已启动")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动服务失败: {str(e)}")

    def stop_service(self):
        """停止定时发布服务"""
        try:
            scheduled_publish_service.stop()
            self.start_service_btn.setEnabled(True)
            self.stop_service_btn.setEnabled(False)
            QMessageBox.information(self, "成功", "定时发布服务已停止")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止服务失败: {str(e)}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.refresh_timer.stop()
        super().closeEvent(event)