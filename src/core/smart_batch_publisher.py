"""
智能批量发布管理器 - 减少加班的核心解决方案
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from src.core.write_xiaohongshu import XiaohongshuPoster
from src.core.database_manager import database_manager
from src.core.logger import logger


class PublishStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class BatchPublishTask:
    """批量发布任务"""
    id: str
    user_id: int
    contents: List[Dict[str, Any]]  # 包含标题、内容、图片等
    schedule_time: Optional[datetime] = None
    priority: int = 1  # 1-5, 5最高
    max_retries: int = 3
    status: PublishStatus = PublishStatus.PENDING
    created_at: datetime = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class SmartBatchPublisher:
    """智能批量发布管理器"""

    def __init__(self, max_concurrent: int = 2):
        self.max_concurrent = max_concurrent
        self.active_tasks: Dict[str, BatchPublishTask] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.publisher_instances: Dict[int, XiaohongshuPoster] = {}  # user_id -> publisher
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None

    def start(self):
        """启动批量发布服务"""
        if self.running:
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.worker_thread.start()
        logger.info("智能批量发布服务已启动")

    def stop(self):
        """停止批量发布服务"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("智能批量发布服务已停止")

    def _run_async_loop(self):
        """运行异步事件循环"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self._process_queue())
        except Exception as e:
            logger.error(f"批量发布服务异常: {e}")
        finally:
            loop.close()

    async def _process_queue(self):
        """处理任务队列"""
        semaphore = asyncio.Semaphore(self.max_concurrent)

        while self.running:
            try:
                # 获取任务
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                asyncio.create_task(self._process_task_with_semaphore(task, semaphore))
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"处理队列异常: {e}")

    async def _process_task_with_semaphore(self, task: BatchPublishTask, semaphore: asyncio.Semaphore):
        """使用信号量控制并发处理任务"""
        async with semaphore:
            await self._process_task(task)

    async def _process_task(self, task: BatchPublishTask):
        """处理单个任务"""
        try:
            task.status = PublishStatus.PROCESSING
            logger.info(f"开始处理批量任务 {task.id}, 用户 {task.user_id}")

            # 获取或创建发布器实例
            publisher = await self._get_publisher(task.user_id)

            # 处理每个内容
            success_count = 0
            for i, content in enumerate(task.contents):
                try:
                    await self._publish_single_content(publisher, content, task.max_retries)
                    success_count += 1

                    # 添加延迟避免被限制
                    await asyncio.sleep(2)

                except Exception as e:
                    logger.error(f"发布内容失败 (任务 {task.id}, 第{i+1}项): {e}")
                    continue

            task.status = PublishStatus.SUCCESS if success_count > 0 else PublishStatus.FAILED
            task.completed_at = datetime.now()

            logger.info(f"批量任务 {task.id} 完成: {success_count}/{len(task.contents)} 成功")

        except Exception as e:
            task.status = PublishStatus.FAILED
            task.completed_at = datetime.now()
            logger.error(f"批量任务 {task.id} 处理失败: {e}")

    async def _get_publisher(self, user_id: int) -> XiaohongshuPoster:
        """获取用户的发布器实例"""
        if user_id not in self.publisher_instances:
            publisher = XiaohongshuPoster()
            await publisher.initialize()
            self.publisher_instances[user_id] = publisher

        return self.publisher_instances[user_id]

    async def _publish_single_content(self, publisher: XiaohongongshuPoster, content: Dict[str, Any], max_retries: int):
        """发布单个内容，支持重试"""
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                await publisher.post_article(
                    title=content['title'],
                    content=content['content'],
                    images=content.get('images', [])
                )
                return  # 成功则返回

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # 指数退避
                    logger.warning(f"发布失败，重试 {attempt + 1}/{max_retries}，等待 {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"发布失败，已达到最大重试次数: {e}")
                    raise last_error

    def add_batch_task(self, task: BatchPublishTask):
        """添加批量任务到队列"""
        self.active_tasks[task.id] = task

        # 如果是定时任务，计算延迟
        if task.schedule_time:
            delay = (task.schedule_time - datetime.now()).total_seconds()
            if delay > 0:
                # 定时任务，延迟执行
                asyncio.create_task(self._schedule_task(task, delay))
            else:
                # 立即执行
                self.task_queue.put_nowait(task)
        else:
            # 立即执行
            self.task_queue.put_nowait(task)

        logger.info(f"已添加批量任务 {task.id} 到队列")

    async def _schedule_task(self, task: BatchPublishTask, delay: float):
        """定时执行任务"""
        await asyncio.sleep(delay)
        await self.task_queue.put(task)
        logger.info(f"定时任务 {task.id} 开始执行")

    def get_task_status(self, task_id: str) -> Optional[BatchPublishTask]:
        """获取任务状态"""
        return self.active_tasks.get(task_id)

    def get_all_tasks(self) -> List[BatchPublishTask]:
        """获取所有活跃任务"""
        return list(self.active_tasks.values())

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if task.status == PublishStatus.PENDING:
                task.status = PublishStatus.FAILED
                task.completed_at = datetime.now()
                logger.info(f"任务 {task_id} 已取消")
                return True

        return False


# 全局实例
batch_publisher = SmartBatchPublisher(max_concurrent=2)


def start_batch_service():
    """启动批量发布服务"""
    batch_publisher.start()


def stop_batch_service():
    """停止批量发布服务"""
    batch_publisher.stop()


def create_batch_task(user_id: int, contents: List[Dict[str, Any]],
                     schedule_time: Optional[datetime] = None,
                     priority: int = 1) -> str:
    """创建批量发布任务"""
    import uuid
    task_id = str(uuid.uuid4())

    task = BatchPublishTask(
        id=task_id,
        user_id=user_id,
        contents=contents,
        schedule_time=schedule_time,
        priority=priority
    )

    batch_publisher.add_batch_task(task)
    return task_id


# 使用示例
if __name__ == "__main__":
    # 启动服务
    start_batch_service()

    # 创建批量任务示例
    sample_contents = [
        {
            "title": "AI生成的内容标题1",
            "content": "这是AI生成的内容正文1...",
            "images": ["/path/to/image1.jpg"]
        },
        {
            "title": "AI生成的内容标题2",
            "content": "这是AI生成的内容正文2...",
            "images": ["/path/to/image2.jpg"]
        }
    ]

    # 立即执行
    task_id = create_batch_task(user_id=1, contents=sample_contents)

    # 或者定时执行
    # schedule_time = datetime.now() + timedelta(hours=2)
    # task_id = create_batch_task(user_id=1, contents=sample_contents, schedule_time=schedule_time)

    print(f"创建了批量任务: {task_id}")

    # 保持运行查看结果
    try:
        while True:
            time.sleep(5)
            task = batch_publisher.get_task_status(task_id)
            if task:
                print(f"任务状态: {task.status.value}")
                if task.completed_at:
                    break
    except KeyboardInterrupt:
        pass
    finally:
        stop_batch_service()