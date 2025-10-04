#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书AI发布助手 - Web界面启动脚本
快速启动 FastAPI Web 服务
"""

import sys
import os
import subprocess
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     🌟 小红书AI发布助手 - Web界面                        ║
║                                                          ║
║     版本: 2.0.0                                          ║
║     界面: FastAPI Web                                    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)

def check_dependencies():
    """检查必要依赖"""
    print("📦 检查依赖...")
    
    required = ['fastapi', 'uvicorn', 'playwright', 'sqlalchemy']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (缺失)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  缺少以下依赖: {', '.join(missing)}")
        print("\n安装命令:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    print("   ✅ 所有依赖已安装\n")
    return True

def check_database():
    """检查数据库"""
    print("💾 检查数据库...")
    
    db_dir = Path.home() / '.xhs_system'
    db_path = db_dir / 'xhs_data.db'
    
    if not db_path.exists():
        print(f"   ⚠️  数据库不存在，将自动创建")
        print(f"   📁 路径: {db_path}\n")
    else:
        size = db_path.stat().st_size
        print(f"   ✅ 数据库存在")
        print(f"   📁 路径: {db_path}")
        print(f"   📊 大小: {size:,} 字节\n")
    
    return True

def start_server(host="0.0.0.0", port=8000, reload=False):
    """启动 Web 服务器"""
    print(f"🚀 启动 Web 服务器...")
    print(f"   🌐 地址: http://{host}:{port}")
    print(f"   🔄 自动重载: {'是' if reload else '否'}")
    print("\n" + "="*60)
    print("📝 服务器日志:")
    print("="*60 + "\n")
    
    try:
        # 构建命令
        cmd = [
            sys.executable, "-m", "uvicorn",
            "src.web.app:app",
            "--host", host,
            "--port", str(port)
        ]
        
        if reload:
            cmd.append("--reload")
        
        # 启动服务器
        subprocess.run(cmd, cwd=os.getcwd())
        
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("🛑 服务器已停止")
        print("="*60)
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 请先安装缺失的依赖")
        print("   运行: pip install -r requirements.txt")
        return 1
    
    # 检查数据库
    check_database()
    
    # 解析命令行参数
    host = "0.0.0.0"
    port = 8000
    reload = False
    
    if len(sys.argv) > 1:
        if "--reload" in sys.argv or "-r" in sys.argv:
            reload = True
        
        for arg in sys.argv[1:]:
            if arg.startswith("--port="):
                port = int(arg.split("=")[1])
            elif arg.startswith("--host="):
                host = arg.split("=")[1]
    
    # 打印使用说明
    print("💡 使用说明:")
    print(f"   1️⃣  在浏览器打开: http://localhost:{port}")
    print(f"   2️⃣  如需远程访问: http://服务器IP:{port}")
    print(f"   3️⃣  按 Ctrl+C 停止服务器")
    print()
    
    # 启动服务器
    success = start_server(host, port, reload)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
