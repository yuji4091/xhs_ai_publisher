#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书AI发布助手 - 安装验证脚本
检查系统环境和依赖是否正确安装
"""

import sys
import os
from pathlib import Path

def print_header(text):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    print(f"   Python版本: {version_str}")
    
    if version.major == 3 and version.minor >= 8:
        print("   ✅ Python版本符合要求 (>= 3.8)")
        return True
    else:
        print("   ❌ Python版本不符合要求 (需要 >= 3.8)")
        return False

def check_dependencies():
    """检查依赖包"""
    print("\n📦 检查依赖包...")
    
    dependencies = {
        'PyQt5': 'PyQt5桌面GUI界面',
        'playwright': 'Playwright浏览器自动化',
        'SQLAlchemy': 'SQLAlchemy数据库',
        'requests': 'Requests HTTP库',
        'Pillow': 'Pillow图像处理',
        'openai': 'OpenAI API',
        'fastapi': 'FastAPI Web框架',
        'uvicorn': 'Uvicorn ASGI服务器',
    }
    
    installed = []
    missing = []
    
    for package, description in dependencies.items():
        try:
            if package == 'Pillow':
                __import__('PIL')
            else:
                __import__(package.lower())
            installed.append((package, description))
            print(f"   ✅ {package:15} - {description}")
        except ImportError:
            missing.append((package, description))
            print(f"   ❌ {package:15} - {description} (未安装)")
    
    return len(missing) == 0, installed, missing

def check_display_environment():
    """检查显示环境"""
    print("\n🖥️  检查显示环境...")
    
    display = os.environ.get('DISPLAY')
    if display:
        print(f"   DISPLAY环境变量: {display}")
    else:
        print("   ⚠️  DISPLAY环境变量未设置 (无法运行PyQt5 GUI)")
        return False
    
    # 尝试创建QApplication
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication([])
        print("   ✅ PyQt5 GUI环境可用")
        return True
    except Exception as e:
        print(f"   ❌ PyQt5 GUI环境不可用: {str(e)[:50]}...")
        return False

def check_web_interface():
    """检查Web界面是否可用"""
    print("\n🌐 检查Web界面...")
    
    try:
        from src.web.app import app
        print("   ✅ FastAPI Web应用可以导入")
        return True
    except Exception as e:
        print(f"   ⚠️  Web应用导入失败: {str(e)[:100]}...")
        return False

def check_database():
    """检查数据库"""
    print("\n💾 检查数据库...")
    
    db_dir = Path.home() / '.xhs_system'
    db_path = db_dir / 'xhs_data.db'
    
    if db_path.exists():
        size = db_path.stat().st_size
        print(f"   ✅ 数据库文件存在: {db_path}")
        print(f"   📊 数据库大小: {size:,} 字节")
        return True
    else:
        print(f"   ⚠️  数据库文件不存在: {db_path}")
        print("   💡 首次运行时会自动创建")
        return False

def print_execution_instructions(gui_available, web_available):
    """打印执行说明"""
    print_header("🚀 执行方法")
    
    if gui_available:
        print("✅ PyQt5 GUI界面可用:")
        print("   python main.py")
        print("   或运行: ./启动程序.sh (macOS/Linux)")
        print("   或运行: 启动程序.bat (Windows)\n")
    else:
        print("❌ PyQt5 GUI界面不可用 (需要图形显示环境)\n")
    
    if web_available:
        print("✅ Web界面可用:")
        print("   python -m uvicorn src.web.app:app --host 0.0.0.0 --port 8000")
        print("   然后在浏览器访问: http://localhost:8000\n")
    else:
        print("❌ Web界面不可用 (缺少依赖或配置问题)\n")
    
    if not gui_available and not web_available:
        print("⚠️  当前环境无法运行界面！")
        print("\n建议:")
        print("1. 如果在服务器环境，请安装缺失的依赖")
        print("2. 如果需要GUI界面，请在有图形显示的环境中运行")
        print("3. 如果使用Web界面，请安装: pip install fastapi uvicorn aiofiles")

def main():
    """主函数"""
    print_header("小红书AI发布助手 - 安装验证")
    
    # 检查Python版本
    python_ok = check_python_version()
    
    # 检查依赖
    deps_ok, installed, missing = check_dependencies()
    
    # 检查显示环境
    gui_available = check_display_environment()
    
    # 检查Web界面
    web_available = check_web_interface()
    
    # 检查数据库
    db_exists = check_database()
    
    # 打印执行说明
    print_execution_instructions(gui_available, web_available)
    
    # 总结
    print_header("📊 验证总结")
    
    print(f"✅ Python版本: {'通过' if python_ok else '失败'}")
    print(f"{'✅' if deps_ok else '⚠️'} 依赖包: {len(installed)}/{len(installed)+len(missing)} 已安装")
    print(f"{'✅' if gui_available else '❌'} PyQt5 GUI: {'可用' if gui_available else '不可用'}")
    print(f"{'✅' if web_available else '⚠️'} Web界面: {'可用' if web_available else '不可用'}")
    print(f"{'✅' if db_exists else '⚠️'} 数据库: {'存在' if db_exists else '将自动创建'}")
    
    print("\n" + "="*60)
    
    if gui_available or web_available:
        print("🎉 恭喜！系统已准备就绪，可以开始使用！")
        if missing:
            print(f"\n💡 建议安装缺失的依赖以获得完整功能:")
            for pkg, desc in missing:
                print(f"   pip install {pkg.lower()}")
    else:
        print("⚠️  系统尚未完全配置，请按照上述建议进行配置。")
    
    print("="*60 + "\n")
    
    return 0 if (python_ok and (gui_available or web_available)) else 1

if __name__ == "__main__":
    sys.exit(main())
