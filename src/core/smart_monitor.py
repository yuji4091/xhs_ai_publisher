"""
智能监控面板 - 实时了解发布状态，减少人工监控
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import os
import logging

from src.core.logger import logger


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """告警信息"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class SystemMetrics:
    """系统指标"""
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_publish_count: int = 0
    success_rate: float = 0.0
    avg_publish_time: float = 0.0
    last_update: datetime = None

    def __post_init__(self):
        if self.last_update is None:
            self.last_update = datetime.now()


class SmartMonitor:
    """智能监控面板"""

    def __init__(self):
        self.metrics = SystemMetrics()
        self.alerts: List[Alert] = []
        self.task_history: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.alert_callbacks: List[callable] = []

    def start_monitoring(self):
        """启动监控"""
        if self.running:
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("智能监控面板已启动")

    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("智能监控面板已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self._update_metrics()
                self._check_alerts()
                self._cleanup_old_data()

                time.sleep(30)  # 每30秒更新一次

            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                time.sleep(60)  # 出错时等待更长时间

    def _update_metrics(self):
        """更新系统指标"""
        try:
            # 这里应该从数据库或其他来源获取实际数据
            # 暂时使用模拟数据
            self.metrics.last_update = datetime.now()

            # 计算成功率
            total = self.metrics.completed_tasks + self.metrics.failed_tasks
            if total > 0:
                self.metrics.success_rate = (self.metrics.completed_tasks / total) * 100

        except Exception as e:
            logger.error(f"更新指标失败: {e}")

    def _check_alerts(self):
        """检查告警条件"""
        # 检查失败率过高
        if self.metrics.success_rate < 50 and self.metrics.total_publish_count > 10:
            self._create_alert(
                AlertLevel.WARNING,
                "发布成功率过低",
                f"当前成功率仅为{self.metrics.success_rate:.1f}%，请检查网络或账号状态"
            )

        # 检查长时间无活动
        if self.metrics.last_update and (datetime.now() - self.metrics.last_update).seconds > 3600:
            self._create_alert(
                AlertLevel.WARNING,
                "系统长时间无活动",
                "超过1小时没有发布活动，请检查系统状态"
            )

        # 检查活跃任务过多
        if self.metrics.active_tasks > 10:
            self._create_alert(
                AlertLevel.WARNING,
                "活跃任务过多",
                f"当前有{self.metrics.active_tasks}个活跃任务，可能影响性能"
            )

    def _create_alert(self, level: AlertLevel, title: str, message: str):
        """创建告警"""
        import uuid
        alert = Alert(
            id=str(uuid.uuid4()),
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now()
        )

        self.alerts.append(alert)

        # 只保留最近100个告警
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

        # 触发回调
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")

        logger.warning(f"创建告警: {title} - {message}")

    def add_alert_callback(self, callback: callable):
        """添加告警回调"""
        self.alert_callbacks.append(callback)

    def resolve_alert(self, alert_id: str):
        """解决告警"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"告警已解决: {alert.title}")
                break

    def record_task_start(self, task_id: str, task_type: str, user_id: int):
        """记录任务开始"""
        self.task_history[task_id] = {
            'type': task_type,
            'user_id': user_id,
            'start_time': datetime.now(),
            'status': 'running'
        }
        self.metrics.active_tasks += 1

    def record_task_end(self, task_id: str, success: bool, publish_count: int = 0):
        """记录任务结束"""
        if task_id in self.task_history:
            task = self.task_history[task_id]
            task['end_time'] = datetime.now()
            task['success'] = success
            task['publish_count'] = publish_count
            task['status'] = 'completed'

            # 更新指标
            self.metrics.active_tasks -= 1
            if success:
                self.metrics.completed_tasks += 1
            else:
                self.metrics.failed_tasks += 1

            self.metrics.total_publish_count += publish_count

            # 计算平均发布时间
            if task['end_time'] and task['start_time']:
                duration = (task['end_time'] - task['start_time']).total_seconds()
                if publish_count > 0:
                    avg_time = duration / publish_count
                    # 简单移动平均
                    self.metrics.avg_publish_time = (
                        self.metrics.avg_publish_time * 0.9 + avg_time * 0.1
                    )

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        return {
            'metrics': {
                'active_tasks': self.metrics.active_tasks,
                'completed_tasks': self.metrics.completed_tasks,
                'failed_tasks': self.metrics.failed_tasks,
                'total_publish_count': self.metrics.total_publish_count,
                'success_rate': round(self.metrics.success_rate, 1),
                'avg_publish_time': round(self.metrics.avg_publish_time, 1),
                'last_update': self.metrics.last_update.isoformat() if self.metrics.last_update else None
            },
            'alerts': [
                {
                    'id': alert.id,
                    'level': alert.level.value,
                    'title': alert.title,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'resolved': alert.resolved
                }
                for alert in self.alerts[-10:]  # 只返回最近10个告警
            ],
            'recent_tasks': list(self.task_history.values())[-5:]  # 最近5个任务
        }

    def _cleanup_old_data(self):
        """清理旧数据"""
        # 删除7天前的任务历史
        cutoff = datetime.now() - timedelta(days=7)
        to_remove = []
        for task_id, task in self.task_history.items():
            if task.get('end_time') and task['end_time'] < cutoff:
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.task_history[task_id]

        # 删除已解决的旧告警（保留7天）
        to_remove_alerts = []
        for alert in self.alerts:
            if alert.resolved and alert.resolved_at and alert.resolved_at < cutoff:
                to_remove_alerts.append(alert)

        for alert in to_remove_alerts:
            self.alerts.remove(alert)

    def export_report(self, days: int = 7) -> Dict[str, Any]:
        """导出报告"""
        cutoff = datetime.now() - timedelta(days=days)

        # 筛选时间范围内的任务
        relevant_tasks = [
            task for task in self.task_history.values()
            if task.get('end_time') and task['end_time'] >= cutoff
        ]

        # 计算统计数据
        total_tasks = len(relevant_tasks)
        successful_tasks = len([t for t in relevant_tasks if t.get('success')])
        total_publishes = sum(t.get('publish_count', 0) for t in relevant_tasks)

        return {
            'period_days': days,
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'success_rate': (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'total_publishes': total_publishes,
            'avg_publish_time': self.metrics.avg_publish_time,
            'generated_at': datetime.now().isoformat()
        }


# 全局实例
monitor = SmartMonitor()


def start_monitoring():
    """启动监控"""
    monitor.start_monitoring()


def stop_monitoring():
    """停止监控"""
    monitor.stop_monitoring()


# 告警处理示例
def handle_alert(alert: Alert):
    """处理告警"""
    if alert.level == AlertLevel.CRITICAL:
        # 发送紧急通知
        print(f"🚨 紧急告警: {alert.title}")
    elif alert.level == AlertLevel.ERROR:
        print(f"❌ 错误告警: {alert.title}")
    elif alert.level == AlertLevel.WARNING:
        print(f"⚠️ 警告告警: {alert.title}")
    else:
        print(f"ℹ️ 信息: {alert.title}")

    print(f"   {alert.message}")


# 使用示例
if __name__ == "__main__":
    # 添加告警处理
    monitor.add_alert_callback(handle_alert)

    # 启动监控
    start_monitoring()

    # 模拟一些任务
    import uuid
    for i in range(3):
        task_id = str(uuid.uuid4())
        monitor.record_task_start(task_id, 'batch_publish', 1)

        # 模拟处理时间
        time.sleep(2)

        # 模拟结果
        success = i < 2  # 前两个成功，最后一个失败
        monitor.record_task_end(task_id, success, 5 if success else 0)

    # 查看仪表板
    dashboard = monitor.get_dashboard_data()
    print("\n=== 监控仪表板 ===")
    print(json.dumps(dashboard, indent=2, ensure_ascii=False, default=str))

    # 导出报告
    report = monitor.export_report(days=1)
    print("\n=== 7天报告 ===")
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))

    # 停止监控
    stop_monitoring()