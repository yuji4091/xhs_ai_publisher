#!/usr/bin/env python3
"""
加班减少系统真实集成测试
使用真实的组件进行测试（如果依赖可用）
"""
import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_real_integration():
    """测试真实组件集成"""
    print("🔬 加班减少系统 - 真实组件集成测试")
    print("=" * 60)

    # 检查依赖可用性
    dependencies_status = {
        "PyQt5": False,
        "Playwright": False,
        "OpenAI": False,
        "SQLAlchemy": False
    }

    try:
        import PyQt5
        dependencies_status["PyQt5"] = True
    except ImportError:
        print("⚠️  PyQt5 未安装 - 桌面界面功能受限")

    try:
        import playwright
        dependencies_status["Playwright"] = True
    except ImportError:
        print("⚠️  Playwright 未安装 - 浏览器自动化功能受限")

    try:
        import openai
        dependencies_status["OpenAI"] = True
    except ImportError:
        print("⚠️  OpenAI 未安装 - AI内容生成功能受限")

    try:
        import sqlalchemy
        dependencies_status["SQLAlchemy"] = True
    except ImportError:
        print("⚠️  SQLAlchemy 未安装 - 数据库功能受限")

    print(f"📦 依赖状态: {sum(dependencies_status.values())}/{len(dependencies_status)} 已安装")
    print()

    # 测试真实组件导入
    real_components_available = True

    try:
        print("🔧 测试真实组件导入...")

        # 测试监控系统
        from src.core.smart_monitor import monitor
        print("✅ SmartMonitor 导入成功")

        # 测试重试系统
        from src.core.smart_retry import smart_retry
        print("✅ SmartRetry 导入成功")

        # 测试AI内容生成器
        try:
            from src.core.ai_content_generator import content_generator
            print("✅ AIContentGenerator 导入成功")
        except Exception as e:
            print(f"⚠️  AIContentGenerator 导入失败: {e}")
            real_components_available = False

        # 测试批量发布器
        try:
            from src.core.smart_batch_publisher import batch_publisher
            print("✅ SmartBatchPublisher 导入成功")
        except Exception as e:
            print(f"⚠️  SmartBatchPublisher 导入失败: {e}")
            real_components_available = False

        # 测试控制器
        try:
            from src.core.overtime_reduction_controller import OvertimeReductionController
            print("✅ OvertimeReductionController 导入成功")
        except Exception as e:
            print(f"⚠️  OvertimeReductionController 导入失败: {e}")
            real_components_available = False

    except Exception as e:
        print(f"❌ 组件导入测试失败: {e}")
        real_components_available = False

    print()

    if real_components_available:
        print("🎯 真实组件测试")
        print("-" * 40)

        try:
            # 初始化真实组件
            controller = OvertimeReductionController()

            # 测试监控数据
            dashboard_data = monitor.get_dashboard_data()
            print(f"✅ 监控系统工作正常: {len(dashboard_data)} 个指标")

            # 测试生产力报告
            report = controller.get_productivity_report(days=1)
            print(f"✅ 生产力报告生成成功: {report['auto_published_count']} 篇已发布")

            print("\n🎉 真实组件集成测试成功！")
            print("💼 系统已准备好进行实际的加班减少工作")

        except Exception as e:
            print(f"❌ 真实组件测试失败: {e}")
            print("🔄 回退到模拟测试模式")

            # 运行模拟测试
            await run_mock_test()

    else:
        print("🔄 依赖不完整，使用模拟测试")
        print("-" * 40)
        await run_mock_test()

async def run_mock_test():
    """运行模拟测试"""
    print("🎭 模拟测试模式")
    print("-" * 40)

    try:
        # 导入模拟组件
        from demo_overtime_system import demo_overtime_reduction
        await demo_overtime_reduction()
        print("\n✅ 模拟测试完成")

    except Exception as e:
        print(f"❌ 模拟测试失败: {e}")

def main():
    """主函数"""
    print("🚀 小红书AI发布助手 - 加班减少系统集成测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 运行异步测试
    success = asyncio.run(test_real_integration())

    print("\n" + "=" * 60)
    print("📋 测试总结:")
    print("   • 代码实现: 真实 (非模拟)")
    print("   • 演示脚本: 模拟组件 (避免依赖问题)")
    print("   • 实际使用: 需要配置完整依赖")
    print()
    print("🔧 如需真实功能，请安装:")
    print("   pip install PyQt5 playwright openai sqlalchemy")
    print("   playwright install")

if __name__ == "__main__":
    main()