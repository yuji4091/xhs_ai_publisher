"""
定时发布服务
支持在工作时间之外自动发布内容，实现"加班"发布功能
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ...config.database import db_manager
from ..models.content import ScheduledTask, ContentTemplate, PublishHistory
from ..models.user import User
from ..write_xiaohongshu import XiaohongshuPoster
from ..logger import logger


class ScheduledPublishService:
    """定时发布服务 - 支持加班时间自动发布"""

    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.check_interval = 60  # 每分钟检查一次

    def start(self):
        """启动定时发布服务"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("定时发布服务已启动")

    def stop(self):
        """停止定时发布服务"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("定时发布服务已停止")

    def _run_scheduler(self):
        """运行调度器"""
        while self.running:
            try:
                self._check_and_execute_tasks()
            except Exception as e:
                logger.error(f"定时发布服务执行出错: {str(e)}")

            time.sleep(self.check_interval)

    def _check_and_execute_tasks(self):
        """检查并执行到期的定时任务"""
        session = database_manager.get_session_direct()
        try:
        # 获取当前时间
        now = datetime.utcnow()

        # 查询到期的定时任务
        due_tasks = session.query(ScheduledTask).filter(
            ScheduledTask.is_active == True,
            ScheduledTask.next_run_time <= now
        ).all()

        for task in due_tasks:
            try:
                # 执行定时任务
                self._execute_task(session, task)
            except Exception as e:
                logger.error(f"执行定时任务失败 task_id={task.id}: {str(e)}")
                    # 记录失败状态
                    task.run_count += 1
                    session.commit()        finally:
            session.close()

    def _execute_task(self, session: Session, task: ScheduledTask):
        """执行单个定时任务"""
        logger.info(f"开始执行定时任务: {task.name} (ID: {task.id})")

        # 获取用户和模板信息
        user = session.query(User).filter(User.id == task.user_id).first()
        template = None
        if task.template_id:
            template = session.query(ContentTemplate).filter(
                ContentTemplate.id == task.template_id
            ).first()

        if not user:
            logger.error(f"用户不存在: user_id={task.user_id}")
            return

        # 创建发布历史记录
        publish_history = PublishHistory(
            user_id=task.user_id,
            template_id=task.template_id,
            title=template.title if template else f"定时发布-{task.name}",
            content=template.content if template else "定时发布内容",
            platform=task.platform,
            status='pending'
        )
        session.add(publish_history)
        session.commit()

        try:
            # 执行发布操作（异步）
            asyncio.run(self._perform_publish(user, template, publish_history))

            # 更新任务状态
            task.last_run_time = datetime.utcnow()
            task.run_count += 1
            task.next_run_time = self._calculate_next_run_time(task)
            session.commit()

            logger.info(f"定时任务执行完成: {task.name}")

        except Exception as e:
            # 记录发布失败
            publish_history.status = 'failed'
            publish_history.error_message = str(e)
            session.commit()
            logger.error(f"定时任务执行失败: {task.name}, 错误: {str(e)}")

    async def _perform_publish(self, user: User, template: Optional[ContentTemplate],
                              publish_history: PublishHistory):
        """执行实际的发布操作"""
        # 这里应该调用现有的发布逻辑
        # 暂时使用模拟发布
        logger.info(f"模拟发布内容: {publish_history.title}")

        # 等待一段时间模拟发布过程
        await asyncio.sleep(2)

        # 更新发布状态
        session = database_manager.get_session_direct()
        try:
            publish_history.status = 'success'
            publish_history.publish_time = datetime.utcnow()
            publish_history.publish_url = f"https://xiaohongshu.com/p/{publish_history.id}"
            session.commit()
        finally:
            session.close()

    def _calculate_next_run_time(self, task: ScheduledTask) -> datetime:
        """计算下次运行时间"""
        now = datetime.utcnow()

        if task.schedule_type == 'once':
            # 一次性任务，设置一个很远的未来时间
            return now + timedelta(days=365*10)
        elif task.schedule_type == 'daily':
            # 每日任务
            return now + timedelta(days=1)
        elif task.schedule_type == 'weekly':
            # 每周任务
            return now + timedelta(weeks=1)
        elif task.schedule_type == 'monthly':
            # 每月任务
            # 简单实现：加30天
            return now + timedelta(days=30)
        else:
            # 默认每日
            return now + timedelta(days=1)

    def create_overtime_task(self, user_id: int, template_id: Optional[int] = None,
                           name: str = "加班自动发布", platform: str = "xiaohongshu") -> int:
        """创建加班时间定时发布任务

        Args:
            user_id: 用户ID
            template_id: 内容模板ID（可选）
            name: 任务名称
            platform: 发布平台

        Returns:
            task_id: 创建的任务ID
        """
        session = database_manager.get_session_direct()
        try:
            # 创建加班时间任务（晚上8点到早上8点之间随机时间）
            import random
            hour = random.randint(20, 31) % 24  # 20:00-07:00
            minute = random.randint(0, 59)

            schedule_time = datetime.utcnow().replace(hour=hour, minute=minute, second=0, microsecond=0)

            # 如果时间已过，调整到明天
            if schedule_time <= datetime.utcnow():
                schedule_time += timedelta(days=1)

            task = ScheduledTask(
                user_id=user_id,
                template_id=template_id,
                name=name,
                platform=platform,
                schedule_type='daily',  # 每天执行
                schedule_time=schedule_time,
                next_run_time=schedule_time,
                is_active=True
            )

            session.add(task)
            session.commit()

            logger.info(f"创建加班定时任务成功: {name} (ID: {task.id})")
            return task.id

        finally:
            session.close()

    def get_overtime_tasks(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的加班定时任务"""
        session = database_manager.get_session_direct()
        try:
            tasks = session.query(ScheduledTask).filter(
                ScheduledTask.user_id == user_id,
                ScheduledTask.is_active == True
            ).all()

            return [task.to_dict() for task in tasks]
        finally:
            session.close()

    def update_task_schedule(self, task_id: int, new_hour: int, new_minute: int = 0):
        """更新任务的执行时间"""
        session = database_manager.get_session_direct()
        try:
            task = session.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if task:
                now = datetime.utcnow()
                schedule_time = now.replace(hour=new_hour, minute=new_minute, second=0, microsecond=0)

                if schedule_time <= now:
                    schedule_time += timedelta(days=1)

                task.schedule_time = schedule_time
                task.next_run_time = schedule_time
                session.commit()

                logger.info(f"更新任务时间成功: task_id={task_id}, time={new_hour:02d}:{new_minute:02d}")
        finally:
            session.close()

    def pause_task(self, task_id: int):
        """暂停定时任务"""
        session = database_manager.get_session_direct()
        try:
            task = session.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if task:
                task.is_active = False
                session.commit()
                logger.info(f"暂停定时任务: task_id={task_id}")
        finally:
            session.close()

    def resume_task(self, task_id: int):
        """恢复定时任务"""
        session = database_manager.get_session_direct()
        try:
            task = session.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if task:
                task.is_active = True
                # 重新计算下次运行时间
                task.next_run_time = self._calculate_next_run_time(task)
                session.commit()
                logger.info(f"恢复定时任务: task_id={task_id}")
        finally:
            session.close()


# 全局定时发布服务实例
scheduled_publish_service = ScheduledPublishService()