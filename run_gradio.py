#!/usr/bin/env python3
"""
文献处理Agent - Gradio专用启动脚本
提供高端的Web界面体验

使用方法:
1. python run_gradio.py                    # 默认启动
2. python run_gradio.py --port 8080        # 指定端口
3. python run_gradio.py --share            # 生成公共链接
4. python run_gradio.py --debug            # 调试模式

作者: AI Assistant
日期: 2025年1月
"""

import argparse
import sys
import os

def check_gradio():
    """检查Gradio是否已安装"""
    try:
        import gradio as gr
        print(f"✅ Gradio版本: {gr.__version__}")
        return True
    except ImportError:
        print("❌ Gradio未安装")
        print("\n请安装Gradio:")
        print("pip install gradio>=4.0.0")
        print("\n或安装所有依赖:")
        print("pip install -r requirements.txt")
        return False

def check_dependencies():
    """检查核心依赖"""
    missing_deps = []
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        from openai import OpenAI
    except ImportError:
        missing_deps.append("openai")
    
    if missing_deps:
        print("❌ 缺少依赖项:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n请安装: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="文献处理Agent - Gradio高端界面",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run_gradio.py                    # 默认启动 (localhost:7860)
  python run_gradio.py --port 8080        # 指定端口
  python run_gradio.py --share            # 生成公共分享链接
  python run_gradio.py --debug            # 开启调试模式
  python run_gradio.py --host 0.0.0.0     # 允许外部访问

特性:
  🎨 现代化Web界面设计
  📁 拖拽式文件上传
  🔄 实时处理进度
  📊 结果可视化展示
  🧠 思维导图预览
  📱 响应式设计
        """
    )
    
    parser.add_argument("--port", type=int, default=7860, 
                       help="Web服务器端口 (默认: 7860)")
    parser.add_argument("--host", default="127.0.0.1", 
                       help="服务器主机地址 (默认: 127.0.0.1)")
    parser.add_argument("--share", action="store_true", 
                       help="生成公共分享链接 (可通过互联网访问)")
    parser.add_argument("--debug", action="store_true", 
                       help="开启调试模式")
    parser.add_argument("--no-auto-open", action="store_true", 
                       help="不自动打开浏览器")
    
    args = parser.parse_args()
    
    print("="*80)
    print("🔬 文献处理Agent - Gradio高端界面")
    print("="*80)
    
    # 检查依赖
    if not check_gradio():
        return 1
    
    if not check_dependencies():
        return 1
    
    # 检查API配置提醒
    print("\n📋 启动前检查:")
    print("✅ 依赖项检查完成")
    
    # 提醒API配置
    print("⚠️  请确保已配置API密钥:")
    print("   - MinerU API Token (在 mineru_pdf_parser.py)")
    print("   - O3 API Key (在 literature_processing_agent.py)")
    
    # 检查PDF文件
    from pathlib import Path
    pdf_count = len(list(Path('.').glob('*.pdf')))
    if pdf_count > 0:
        print(f"📄 发现 {pdf_count} 个PDF文件")
    else:
        print("📄 当前目录无PDF文件 (可在界面中上传)")
    
    print(f"\n🚀 启动Gradio界面...")
    print(f"🌐 访问地址: http://{args.host}:{args.port}")
    
    if args.share:
        print("🔗 将生成公共分享链接...")
    
    try:
        # 导入并启动Gradio应用
        from literature_agent_gradio import LiteratureAgentGradio
        
        app = LiteratureAgentGradio()
        
        # 启动参数
        launch_kwargs = {
            "server_name": args.host,
            "server_port": args.port,
            "share": args.share,
            "debug": args.debug,
            "inbrowser": not args.no_auto_open,
            "quiet": False
        }
        
        # 启动应用
        app.launch(**launch_kwargs)
        
    except KeyboardInterrupt:
        print("\n👋 用户中断，程序退出")
        return 0
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        
        # 提供调试信息
        if args.debug:
            import traceback
            traceback.print_exc()
        
        print("\n💡 故障排除建议:")
        print("1. 检查端口是否被占用")
        print("2. 尝试不同的端口: --port 8080")
        print("3. 检查防火墙设置")
        print("4. 重新安装Gradio: pip install --upgrade gradio")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())