#!/usr/bin/env python3
"""
加班减少系统演示脚本
展示如何使用新实现的自动化功能
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 模拟组件定义（用于演示）
class PublishStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class BatchPublishTask:
    """批量发布任务"""
    task_id: str
    user_id: int
    contents: List[str]
    schedule_time: Optional[datetime] = None
    status: str = "pending"
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class MockSmartMonitor:
    """模拟监控器"""
    def __init__(self):
        self.metrics = {
            "total_tasks": 0,
            "successful_publishes": 0,
            "failed_publishes": 0,
            "average_publish_time": 0
        }

    def record_publish_success(self, duration: float):
        self.metrics["successful_publishes"] += 1
        self.metrics["total_tasks"] += 1

    def record_publish_failure(self):
        self.metrics["failed_publishes"] += 1
        self.metrics["total_tasks"] += 1

    def get_dashboard_data(self) -> Dict[str, Any]:
        return {
            "metrics": self.metrics,
            "timestamp": datetime.now().isoformat()
        }

class MockSmartRetry:
    """模拟重试系统"""
    def __init__(self):
        self.retry_count = 0

    async def execute_with_retry(self, func, max_attempts: int = 3):
        """执行带重试的函数"""
        for attempt in range(max_attempts):
            try:
                self.retry_count += 1
                if asyncio.iscoroutinefunction(func):
                    return await func()
                else:
                    return func()
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e
                await asyncio.sleep(0.1 * (2 ** attempt))
        return None

class MockAIContentGenerator:
    """模拟AI内容生成器"""
    def __init__(self):
        self.templates = {
            "健康饮食": [
                "饮食健康指南：均衡营养是健康的基础",
                "美味又健康的食谱分享",
                "饮食习惯如何影响身体健康"
            ],
            "运动健身": [
                "居家健身计划分享",
                "运动前后饮食注意事项",
                "不同年龄段的运动建议"
            ]
        }

    async def generate_content_batch(self, topic: str, count: int = 3) -> List[str]:
        """生成内容批次"""
        if topic in self.templates:
            contents = self.templates[topic]
        else:
            contents = [f"{topic}相关内容{i+1}" for i in range(count)]

        await asyncio.sleep(0.2)
        return contents[:count]

class MockSmartBatchPublisher:
    """模拟智能批量发布器"""
    def __init__(self, monitor: MockSmartMonitor, retry_system: MockSmartRetry, max_concurrent: int = 2):
        self.monitor = monitor
        self.retry_system = retry_system
        self.max_concurrent = max_concurrent
        self.tasks: List[BatchPublishTask] = []
        self.semaphore = asyncio.Semaphore(max_concurrent)

    def add_task(self, task: BatchPublishTask):
        """添加任务"""
        self.tasks.append(task)

    async def process_pending_tasks(self):
        """处理待处理任务"""
        pending_tasks = [t for t in self.tasks if t.status == "pending"]

        if not pending_tasks:
            print("📭 没有待处理的任务")
            return

        print(f"🚀 开始处理 {len(pending_tasks)} 个任务...")

        tasks = []
        for task in pending_tasks:
            tasks.append(self._process_single_task(task))

        await asyncio.gather(*tasks, return_exceptions=True)
        print("✅ 所有任务处理完成")

    async def _process_single_task(self, task: BatchPublishTask):
        """处理单个任务"""
        async with self.semaphore:
            task.status = "processing"
            print(f"📤 处理任务: {task.task_id}")

            success_count = 0
            for i, content in enumerate(task.contents):
                try:
                    await asyncio.sleep(0.5)

                    if i < len(task.contents) * 0.9:
                        self.monitor.record_publish_success(0.5)
                        success_count += 1
                        print(f"  ✅ 发布成功: {content[:30]}...")
                    else:
                        raise Exception("模拟发布失败")

                except Exception as e:
                    print(f"  ❌ 发布失败: {content[:30]}... - {e}")
                    self.monitor.record_publish_failure()

            task.status = "completed" if success_count > 0 else "failed"
            print(f"📊 任务 {task.task_id} 完成: {success_count}/{len(task.contents)} 成功")

class MockOvertimeReductionController:
    """模拟加班减少控制器"""
    def __init__(self, ai_generator, batch_publisher, monitor, retry_system):
        self.ai_generator = ai_generator
        self.batch_publisher = batch_publisher
        self.monitor = monitor
        self.retry_system = retry_system

    async def quick_publish(self, topic: str, count: int = 3) -> str:
        """快速发布：生成内容并批量发布"""
        print(f"⚡ 开始快速发布: 主题 '{topic}', 数量 {count}")

        if self.ai_generator:
            contents = await self.ai_generator.generate_content_batch(topic, count)
            print(f"🤖 AI生成 {len(contents)} 条内容")
        else:
            contents = [f"{topic}内容{i+1}" for i in range(count)]
            print(f"📝 生成 {len(contents)} 条模拟内容")

        task = BatchPublishTask(
            task_id=f"quick_{topic}_{int(datetime.now().timestamp())}",
            user_id=1,
            contents=contents,
            schedule_time=datetime.now()
        )

        self.batch_publisher.add_task(task)
        await self.batch_publisher.process_pending_tasks()

        return task.task_id

    def get_productivity_report(self, days: int = 7) -> Dict[str, Any]:
        """获取生产力报告"""
        metrics = self.monitor.get_dashboard_data()["metrics"]

        auto_published = metrics["successful_publishes"]
        manual_time_per_post = 30
        saved_time_minutes = auto_published * manual_time_per_post

        return {
            "period_days": days,
            "auto_published_count": auto_published,
            "success_rate": metrics["successful_publishes"] / max(metrics["total_tasks"], 1),
            "estimated_saved_time_hours": saved_time_minutes / 60,
            "average_publish_time": metrics["average_publish_time"]
        }

async def demo_overtime_reduction():
    """演示加班减少系统功能"""
    print("🚀 小红书AI发布助手 - 加班减少系统演示")
    print("=" * 60)

    print("⚠️  注意：本演示使用模拟组件，实际使用时需要配置相应依赖")
    print()

    try:
        # 初始化模拟组件
        print("🔧 初始化加班减少系统...")
        monitor = MockSmartMonitor()
        retry_system = MockSmartRetry()
        ai_generator = MockAIContentGenerator()
        batch_publisher = MockSmartBatchPublisher(monitor, retry_system, max_concurrent=3)
        controller = MockOvertimeReductionController(
            ai_generator, batch_publisher, monitor, retry_system
        )
        print("✅ 系统初始化完成")
        print()

        # 演示场景1：快速生成并发布内容
        print("📝 场景1：一键生成并发布健康饮食内容")
        print("-" * 40)

        task_id = await controller.quick_publish("健康饮食", count=5)
        print(f"✅ 快速发布任务完成: {task_id}")
        print()

        # 演示场景2：批量处理预先准备的内容
        print("📦 场景2：批量发布预先准备的内容")
        print("-" * 40)

        prepared_contents = [
            "晨间运动的好处：开启活力一天",
            "健康早餐搭配指南",
            "办公室健康小技巧",
            "睡前放松方法分享",
            "周末家庭健身计划"
        ]

        batch_task = BatchPublishTask(
            task_id="demo_batch_001",
            user_id=1,
            contents=prepared_contents,
            schedule_time=datetime.now()
        )

        batch_publisher.add_task(batch_task)
        await batch_publisher.process_pending_tasks()
        print()

        # 演示场景3：创建定时发布任务
        print("⏰ 场景3：创建定时发布任务")
        print("-" * 40)

        schedule_time = datetime.now() + timedelta(hours=2)
        scheduled_contents = [
            "晚间阅读推荐",
            "睡前冥想指南"
        ]

        scheduled_task = BatchPublishTask(
            task_id="scheduled_demo_001",
            user_id=1,
            contents=scheduled_contents,
            schedule_time=schedule_time
        )

        print(f"📅 已创建定时任务: {scheduled_task.task_id}")
        print(f"   计划执行时间: {schedule_time.strftime('%H:%M:%S')}")
        print(f"   内容数量: {len(scheduled_contents)}")
        print()

        # 显示生产力报告
        print("📊 生产力提升报告")
        print("-" * 40)

        report = controller.get_productivity_report(days=1)
        print("今日工作成果:")
        print(f"   🤖 AI生成内容: {5 + 2} 篇")
        print(f"   📤 自动发布: {report['auto_published_count']} 篇")
        print(f"   ✅ 成功率: {report['success_rate']:.1%}")
        print(f"   💰 节省时间: {report['estimated_saved_time_hours']:.1f} 小时")
        print()

        # 显示时间节省计算
        print("⏱️  时间节省分析")
        print("-" * 40)

        manual_time_per_post = 30
        ai_generation_time = 15
        manual_total_time = report['auto_published_count'] * manual_time_per_post
        automated_total_time = ai_generation_time + (report['auto_published_count'] * 2)

        print(f"   传统方式总时间: {manual_total_time} 分钟")
        print(f"   自动化方式总时间: {automated_total_time} 分钟")
        print(f"   时间节省: {manual_total_time - automated_total_time} 分钟")
        print(f"   效率提升: {((manual_total_time - automated_total_time) / manual_total_time * 100):.0f}%")
        print()

        # 显示系统优势
        print("💡 系统核心优势")
        print("-" * 40)
        advantages = [
            "⚡ 快速内容生成：AI驱动，质量保证",
            "🔄 智能批量处理：并发执行，提高效率",
            "⏰ 定时自动发布：无需手动值守",
            "🔁 自动错误恢复：智能重试机制",
            "📊 实时性能监控：数据驱动优化",
            "🎯 一键全自动化：从 ideation 到发布"
        ]

        for advantage in advantages:
            print(f"   {advantage}")
        print()

        print("🎉 演示完成！")
        print("💼 加班减少系统已准备就绪，可以帮助您显著提升工作效率")
        print()
        print("📋 使用建议:")
        print("   1. 配置 OpenAI API Key 以启用 AI 内容生成")
        print("   2. 安装 PyQt5 和 Playwright 用于完整功能")
        print("   3. 运行 python main.py 启动桌面应用")
        print("   4. 或运行 python src/web/app.py 启动 web 界面")

        return True

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(demo_overtime_reduction())
    print("\n" + "=" * 60)
    if success:
        print("🎯 演示结果: 成功 ✅")
    else:
        print("🎯 演示结果: 失败 ❌")
    sys.exit(0 if success else 1)