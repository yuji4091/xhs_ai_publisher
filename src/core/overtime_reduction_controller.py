"""
加班减少系统主控制器 - 整合所有组件
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from src.core.smart_batch_publisher import batch_publisher, BatchPublishTask
from src.core.ai_content_generator import content_generator, GeneratedContent
from src.core.smart_monitor import monitor
from src.core.smart_retry import smart_retry, error_recovery, setup_default_error_recovery
from src.core.logger import logger


class OvertimeReductionController:
    """加班减少系统主控制器"""

    def __init__(self):
        self.running = False
        self.main_thread: Optional[threading.Thread] = None

    def start_system(self):
        """启动整个加班减少系统"""
        if self.running:
            return

        logger.info("🚀 启动加班减少系统...")

        try:
            # 1. 设置错误恢复策略
            setup_default_error_recovery()

            # 2. 启动监控面板
            monitor.start_monitoring()

            # 3. 启动批量发布服务
            batch_publisher.start()

            # 4. 启动主循环
            self.running = True
            self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
            self.main_thread.start()

            logger.info("✅ 加班减少系统启动成功")

        except Exception as e:
            logger.error(f"❌ 系统启动失败: {e}")
            self.stop_system()
            raise

    def stop_system(self):
        """停止整个系统"""
        if not self.running:
            return

        logger.info("🛑 停止加班减少系统...")

        self.running = False

        # 停止各个组件
        batch_publisher.stop()
        monitor.stop_monitoring()

        if self.main_thread:
            self.main_thread.join(timeout=10)

        logger.info("✅ 加班减少系统已停止")

    def _main_loop(self):
        """主循环"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self._async_main_loop())
        except Exception as e:
            logger.error(f"主循环异常: {e}")
        finally:
            loop.close()

    async def _async_main_loop(self):
        """异步主循环"""
        while self.running:
            try:
                # 执行定期维护任务
                await self._perform_maintenance()

                # 检查系统健康状态
                await self._health_check()

                # 等待下一轮
                await asyncio.sleep(300)  # 5分钟检查一次

            except Exception as e:
                logger.error(f"主循环迭代异常: {e}")
                await asyncio.sleep(60)  # 出错时等待1分钟

    async def _perform_maintenance(self):
        """执行维护任务"""
        try:
            # 清理过期任务
            self._cleanup_expired_tasks()

            # 优化系统性能
            await self._optimize_performance()

            # 生成维护报告
            await self._generate_maintenance_report()

        except Exception as e:
            logger.error(f"维护任务异常: {e}")

    def _cleanup_expired_tasks(self):
        """清理过期任务"""
        # 这里可以实现清理逻辑
        pass

    async def _optimize_performance(self):
        """优化系统性能"""
        # 监控内存使用
        # 清理缓存
        # 调整并发数
        pass

    async def _generate_maintenance_report(self):
        """生成维护报告"""
        # 每小时生成一次报告
        pass

    async def _health_check(self):
        """系统健康检查"""
        try:
            # 检查各个组件状态
            components_status = {
                'batch_publisher': batch_publisher.running,
                'monitor': monitor.running,
                'content_generator': bool(content_generator.api_key)
            }

            unhealthy_components = [
                name for name, status in components_status.items()
                if not status
            ]

            if unhealthy_components:
                logger.warning(f"⚠️ 不健康的组件: {', '.join(unhealthy_components)}")

                # 尝试自动恢复
                await self._auto_recover(unhealthy_components)

        except Exception as e:
            logger.error(f"健康检查异常: {e}")

    async def _auto_recover(self, unhealthy_components: List[str]):
        """自动恢复不健康的组件"""
        for component in unhealthy_components:
            try:
                if component == 'batch_publisher':
                    if not batch_publisher.running:
                        batch_publisher.start()
                        logger.info("✅ 批量发布服务已自动恢复")

                elif component == 'monitor':
                    if not monitor.running:
                        monitor.start_monitoring()
                        logger.info("✅ 监控面板已自动恢复")

            except Exception as e:
                logger.error(f"组件 {component} 自动恢复失败: {e}")

    # 高层API - 让用户更容易使用

    async def create_smart_publish_task(self, topic: str, count: int = 5,
                                      template_id: str = 'lifestyle',
                                      schedule_time: Optional[datetime] = None) -> str:
        """创建智能发布任务（自动生成内容+发布）"""
        try:
            logger.info(f"🎯 创建智能发布任务: 主题='{topic}', 数量={count}")

            # 1. AI生成内容
            logger.info("🤖 开始AI生成内容...")
            generated_contents = await content_generator.generate_content_batch(
                topic=topic,
                count=count,
                template_id=template_id
            )

            if not generated_contents:
                raise Exception("AI内容生成失败")

            logger.info(f"✅ 成功生成 {len(generated_contents)} 篇内容")

            # 2. 转换为发布格式
            publish_contents = []
            for content in generated_contents:
                publish_contents.append({
                    'title': content.title,
                    'content': content.content,
                    'images': [],  # 可以后续添加图片
                    'tags': content.tags
                })

            # 3. 创建批量发布任务
            task = BatchPublishTask(
                id=f"smart_{int(time.time())}",
                user_id=1,  # 默认用户ID
                contents=publish_contents,
                schedule_time=schedule_time
            )

            batch_publisher.add_batch_task(task)

            # 4. 记录监控
            monitor.record_task_start(task.id, 'smart_publish', 1)

            logger.info(f"🎉 智能发布任务创建成功: {task.id}")
            return task.id

        except Exception as e:
            logger.error(f"创建智能发布任务失败: {e}")
            raise

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统整体状态"""
        dashboard = monitor.get_dashboard_data()

        return {
            'system_running': self.running,
            'components': {
                'batch_publisher': batch_publisher.running,
                'monitor': monitor.running,
                'content_generator': bool(content_generator.api_key)
            },
            'performance': dashboard['metrics'],
            'alerts': dashboard['alerts'][:5],  # 最近5个告警
            'active_tasks': len([t for t in batch_publisher.get_all_tasks()
                               if t.status.value == 'processing'])
        }

    def get_productivity_report(self, days: int = 7) -> Dict[str, Any]:
        """获取生产力报告"""
        monitor_report = monitor.export_report(days)

        # 计算加班减少指标
        total_auto_published = monitor_report.get('total_publishes', 0)
        estimated_manual_time = total_auto_published * 30  # 假设每篇手动发布需要30分钟
        saved_time_hours = estimated_manual_time / 60

        return {
            'period_days': days,
            'auto_published_count': total_auto_published,
            'estimated_saved_time_hours': round(saved_time_hours, 1),
            'success_rate': monitor_report.get('success_rate', 0),
            'avg_publish_time': monitor_report.get('avg_publish_time', 0),
            'generated_at': datetime.now().isoformat()
        }


# 全局实例
overtime_controller = OvertimeReductionController()


def start_overtime_reduction_system():
    """启动加班减少系统"""
    overtime_controller.start_system()


def stop_overtime_reduction_system():
    """停止加班减少系统"""
    overtime_controller.stop_system()


# 便捷函数
async def quick_publish(topic: str, count: int = 3) -> str:
    """快速发布 - 一键生成并发布内容"""
    return await overtime_controller.create_smart_publish_task(topic, count)


def get_status():
    """获取系统状态"""
    return overtime_controller.get_system_status()


def get_productivity_report(days: int = 7):
    """获取生产力报告"""
    return overtime_controller.get_productivity_report(days)


# 使用示例
async def demo():
    """演示完整的加班减少系统"""
    print("🚀 启动加班减少系统演示...")

    # 启动系统
    start_overtime_reduction_system()

    # 等待系统启动
    await asyncio.sleep(2)

    # 查看初始状态
    status = get_status()
    print("📊 初始系统状态:")
    print(f"  系统运行: {status['system_running']}")
    print(f"  活跃任务: {status['active_tasks']}")

    # 创建智能发布任务
    print("\n🎯 创建智能发布任务...")
    task_id = await quick_publish("健康生活方式", count=2)

    print(f"✅ 任务创建成功: {task_id}")

    # 监控任务进度
    for _ in range(30):  # 最多等待5分钟
        await asyncio.sleep(10)

        # 检查任务状态
        task = batch_publisher.get_task_status(task_id)
        if task:
            print(f"📈 任务状态: {task.status.value}")
            if task.status.value in ['success', 'failed']:
                break

    # 查看最终状态和报告
    final_status = get_status()
    report = get_productivity_report(days=1)

    print("\n📊 最终系统状态:")
    print(f"  活跃任务: {final_status['active_tasks']}")
    print(f"  自动发布数量: {report['auto_published_count']}")
    print(f"  节省时间: {report['estimated_saved_time_hours']:.1f} 小时")
    # 停止系统
    stop_overtime_reduction_system()
    print("\n✅ 演示完成")


if __name__ == "__main__":
    asyncio.run(demo())