#!/usr/bin/env python3
"""
加班减少系统命令行界面
提供简单的CLI来演示和使用加班减少功能
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

# 模拟组件定义（用于CLI演示）
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
            ],
            "美妆护肤": [
                "日常护肤步骤详解",
                "不同肤质的护肤建议",
                "化妆技巧分享"
            ],
            "旅行攻略": [
                "热门目的地推荐",
                "旅行准备清单",
                "省钱旅行技巧"
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

def show_menu():
    """显示主菜单"""
    print("\n" + "="*60)
    print("🚀 小红书AI发布助手 - 加班减少系统 CLI")
    print("="*60)
    print("1. 🚀 快速发布 (AI生成+自动发布)")
    print("2. 📝 批量发布 (预先准备的内容)")
    print("3. ⏰ 定时发布 (设置未来发布时间)")
    print("4. 📊 查看生产力报告")
    print("5. 📋 查看系统状态")
    print("6. 🎯 演示完整流程")
    print("0. ❌ 退出")
    print("="*60)

async def quick_publish_flow(controller):
    """快速发布流程"""
    print("\n⚡ 快速发布模式")
    print("-" * 30)

    # 显示可用主题
    topics = ["健康饮食", "运动健身", "美妆护肤", "旅行攻略"]
    print("📚 可用主题:")
    for i, topic in enumerate(topics, 1):
        print(f"   {i}. {topic}")

    try:
        choice = input("\n请选择主题 (1-4): ").strip()
        if choice in ['1', '2', '3', '4']:
            topic = topics[int(choice) - 1]
        else:
            topic = input("请输入自定义主题: ").strip()

        count = input("请输入生成数量 (1-10): ").strip()
        count = min(max(int(count) if count.isdigit() else 3, 1), 10)

        print(f"\n🎯 将生成并发布 {count} 篇关于 '{topic}' 的内容")
        confirm = input("确认开始? (y/N): ").strip().lower()

        if confirm == 'y':
            task_id = await controller.quick_publish(topic, count)
            print(f"\n✅ 快速发布完成! 任务ID: {task_id}")
        else:
            print("❌ 已取消")

    except Exception as e:
        print(f"❌ 操作失败: {e}")

async def batch_publish_flow(batch_publisher):
    """批量发布流程"""
    print("\n📦 批量发布模式")
    print("-" * 30)

    print("请输入要发布的內容 (每行一条, 输入空行结束):")
    contents = []
    while True:
        line = input(f"内容 {len(contents) + 1}: ").strip()
        if not line:
            break
        contents.append(line)

    if not contents:
        print("❌ 没有输入内容")
        return

    print(f"\n📋 共 {len(contents)} 条内容:")
    for i, content in enumerate(contents, 1):
        print(f"   {i}. {content[:50]}{'...' if len(content) > 50 else ''}")

    confirm = input("\n确认发布? (y/N): ").strip().lower()
    if confirm == 'y':
        task = BatchPublishTask(
            task_id=f"batch_{int(datetime.now().timestamp())}",
            user_id=1,
            contents=contents,
            schedule_time=datetime.now()
        )

        batch_publisher.add_task(task)
        await batch_publisher.process_pending_tasks()
        print("✅ 批量发布完成!")
    else:
        print("❌ 已取消")

async def scheduled_publish_flow(batch_publisher):
    """定时发布流程"""
    print("\n⏰ 定时发布模式")
    print("-" * 30)

    try:
        hours = input("请输入多少小时后发布 (1-24): ").strip()
        hours = min(max(int(hours) if hours.isdigit() else 2, 1), 24)

        schedule_time = datetime.now() + timedelta(hours=hours)

        content = input("请输入要发布的内容: ").strip()
        if not content:
            print("❌ 内容不能为空")
            return

        task = BatchPublishTask(
            task_id=f"scheduled_{int(datetime.now().timestamp())}",
            user_id=1,
            contents=[content],
            schedule_time=schedule_time
        )

        batch_publisher.add_task(task)

        print("✅ 定时任务已创建!")
        print(f"   任务ID: {task.task_id}")
        print(f"   发布时间: {schedule_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   内容: {content[:50]}{'...' if len(content) > 50 else ''}")

    except Exception as e:
        print(f"❌ 操作失败: {e}")

def show_productivity_report(controller):
    """显示生产力报告"""
    print("\n📊 生产力报告")
    print("-" * 30)

    report = controller.get_productivity_report(days=1)

    print("今日工作成果:")
    print(f"   🤖 AI生成内容: {report['auto_published_count']} 篇")
    print(f"   📤 自动发布: {report['auto_published_count']} 篇")
    print(f"   📈 成功率: {report['success_rate']:.1f}%")
    print(f"   ⏱️  平均时间: {report['average_publish_time']:.1f} 分钟")
    # 计算时间节省
    manual_time = report['auto_published_count'] * 30  # 假设每篇手动需要30分钟
    ai_time = 15  # AI生成时间
    auto_time = report['auto_published_count'] * 2  # 自动发布每篇2分钟

    print("\n⏱️  时间对比:")
    print(f"   传统方式: {manual_time} 分钟")
    print(f"   自动化方式: {ai_time + auto_time} 分钟")
    print(f"   时间节省: {manual_time - (ai_time + auto_time)} 分钟")
    if manual_time > 0:
        savings_rate = ((manual_time - (ai_time + auto_time)) / manual_time * 100)
        print(f"   💰 效率提升: {savings_rate:.0f}%")
def show_system_status(monitor, batch_publisher):
    """显示系统状态"""
    print("\n📋 系统状态")
    print("-" * 30)

    metrics = monitor.get_dashboard_data()["metrics"]

    print("\n📊 实时指标:")
    print(f"   总任务数: {metrics['total_tasks']}")
    print(f"   成功发布: {metrics['successful_publishes']}")
    print(f"   失败发布: {metrics['failed_publishes']}")
    print(f"   平均发布时间: {metrics['average_publish_time']:.1f} 秒")

    print(f"\n📦 待处理任务: {len([t for t in batch_publisher.tasks if t.status == 'pending'])}")
    print(f"📤 处理中任务: {len([t for t in batch_publisher.tasks if t.status == 'processing'])}")
    print(f"✅ 已完成任务: {len([t for t in batch_publisher.tasks if t.status == 'completed'])}")

async def demo_full_flow(controller):
    """演示完整流程"""
    print("\n🎯 完整流程演示")
    print("-" * 30)

    print("🚀 演示加班减少系统的完整工作流程...")
    print()

    # 1. AI生成内容
    print("1️⃣ AI内容生成阶段")
    await asyncio.sleep(1)

    # 2. 批量发布
    print("2️⃣ 批量发布阶段")
    task_id = await controller.quick_publish("健康饮食", 3)
    print()

    # 3. 查看报告
    print("3️⃣ 生产力报告")
    await asyncio.sleep(1)
    show_productivity_report(controller)
    print()

    print("🎉 完整流程演示完成!")
    print("💡 在真实环境中，这些操作会在后台自动执行，无需手动干预")

async def main():
    """主函数"""
    # 初始化系统
    print("🔧 初始化加班减少系统...")
    monitor = MockSmartMonitor()
    retry_system = MockSmartRetry()
    ai_generator = MockAIContentGenerator()
    batch_publisher = MockSmartBatchPublisher(monitor, retry_system, max_concurrent=3)
    controller = MockOvertimeReductionController(
        ai_generator, batch_publisher, monitor, retry_system
    )
    print("✅ 系统初始化完成")

    while True:
        show_menu()
        choice = input("请选择操作 (0-6): ").strip()

        if choice == '0':
            print("\n👋 感谢使用加班减少系统!")
            break
        elif choice == '1':
            await quick_publish_flow(controller)
        elif choice == '2':
            await batch_publish_flow(batch_publisher)
        elif choice == '3':
            await scheduled_publish_flow(batch_publisher)
        elif choice == '4':
            show_productivity_report(controller)
        elif choice == '5':
            show_system_status(monitor, batch_publisher)
        elif choice == '6':
            await demo_full_flow(controller)
        else:
            print("❌ 无效选择，请重新输入")

        input("\n按回车键继续...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        sys.exit(1)