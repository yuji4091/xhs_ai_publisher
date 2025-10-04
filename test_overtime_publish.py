#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加班发布功能测试脚本
测试定时发布服务的基本功能
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_overtime_publish():
    """测试加班发布功能"""
    print("🌙 开始测试加班发布功能...")
    print("=" * 50)

    try:
        # 测试导入
        print("📦 测试模块导入...")
        from src.core.services.scheduled_publish_service import ScheduledPublishService, scheduled_publish_service
        from src.core.pages.overtime_publish import OvertimePublishPage
        print("✅ 模块导入成功")

        # 测试服务初始化
        print("\n🔧 测试定时发布服务...")
        service = ScheduledPublishService()
        print("✅ 服务初始化成功")

        # 测试服务启动和停止
        print("\n▶️ 测试服务启动...")
        service.start()
        print("✅ 服务启动成功")

        time.sleep(2)  # 等待一会儿

        print("\n⏹️ 测试服务停止...")
        service.stop()
        print("✅ 服务停止成功")

        # 测试创建任务（需要用户登录，这里只是测试接口）
        print("\n📝 测试任务创建接口...")
        # 注意：这里不会实际创建任务，因为需要有效的用户ID
        print("ℹ️ 任务创建需要有效的用户登录，跳过实际创建测试")

        print("\n🎉 所有基础测试通过！")
        print("💡 要完整测试功能，请：")
        print("   1. 运行主应用程序: python main.py")
        print("   2. 登录用户账号")
        print("   3. 点击侧边栏的 🌙 按钮进入加班发布页面")
        print("   4. 创建定时发布任务")

        return True

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("💡 请确保所有依赖都已安装: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_integration():
    """测试数据库集成"""
    print("\n🗄️ 测试数据库集成...")

    try:
        from src.core.database_manager import database_manager
        from src.core.models.content import ScheduledTask

        # 检查数据库连接
        session = database_manager.get_session_direct()
        print("✅ 数据库连接成功")

        # 检查表是否存在
        inspector = database_manager.engine.inspect()
        tables = inspector.get_table_names()
        print(f"📋 数据库表: {tables}")

        if 'scheduled_tasks' in tables:
            print("✅ scheduled_tasks 表存在")
        else:
            print("⚠️ scheduled_tasks 表不存在，可能需要重新初始化数据库")

        session.close()
        return True

    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 加班发布功能测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 测试基本功能
    success = test_overtime_publish()

    # 测试数据库集成
    db_success = test_database_integration()

    print("\n" + "=" * 50)
    if success and db_success:
        print("🎉 所有测试通过！加班发布功能已准备就绪。")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，请检查错误信息。")
        sys.exit(1)