#!/usr/bin/env python3
"""
文献处理Agent快速启动脚本
提供多种启动方式的便捷入口

使用方法:
1. python run_agent.py gui          # 启动图形界面
2. python run_agent.py cli          # 启动命令行界面
3. python run_agent.py demo         # 运行演示示例
4. python run_agent.py --help       # 显示帮助信息

作者: AI Assistant
日期: 2025年1月
"""

import sys
import os
import argparse
from pathlib import Path

def check_dependencies():
    """检查依赖项"""
    missing_deps = []
    
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter (GUI界面需要)")
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        from openai import OpenAI
    except ImportError:
        missing_deps.append("openai")
    
    if missing_deps:
        print("❌ 缺少以下依赖项:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n请安装缺少的依赖项后重试。")
        return False
    
    return True

def check_files():
    """检查必要文件是否存在"""
    required_files = [
        "literature_processing_agent.py",
        "mineru_pdf_parser.py", 
        "full_structure_property_extraction.py",
        "literature_agent_gui.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ 缺少以下必要文件:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n请确保所有文件都在当前目录中。")
        return False
    
    return True

def run_gui():
    """启动图形界面"""
    print("🚀 启动现代化Web界面...")
    try:
        # 优先尝试Gradio界面
        try:
            from literature_agent_gradio import LiteratureAgentGradio
            app = LiteratureAgentGradio()
            app.launch()
        except ImportError:
            print("⚠️ Gradio未安装，尝试启动备用tkinter界面...")
            # 备用tkinter界面
            from literature_agent_gui import LiteratureAgentGUI
            app = LiteratureAgentGUI()
            app.run()
    except Exception as e:
        print(f"❌ 启动GUI失败: {e}")
        print("提示:")
        print("1. 安装Gradio获得最佳体验: pip install gradio")
        print("2. 或使用命令行模式: python run_agent.py cli")
        print("3. 检查依赖是否完整: pip install -r requirements.txt")

def run_cli():
    """启动命令行界面"""
    print("🚀 启动命令行界面...")
    try:
        from literature_processing_agent import LiteratureProcessingAgent
        from pathlib import Path
        
        # 交互式CLI界面
        print("\n文献处理Agent - 命令行模式")
        print("=" * 50)
        
        # 查找PDF文件
        pdf_files = list(Path('.').glob('*.pdf'))
        if not pdf_files:
            print("❌ 当前目录没有找到PDF文件")
            print("请将PDF文件放在当前目录中，然后重新运行。")
            return
        
        print(f"📄 发现 {len(pdf_files)} 个PDF文件:")
        for i, pdf in enumerate(pdf_files, 1):
            size = os.path.getsize(pdf) / (1024*1024)
            print(f"  {i}. {pdf.name} ({size:.1f} MB)")
        
        # 选择处理模式
        print(f"\n请选择处理模式:")
        print("1. 单个文件处理")
        print("2. 批量处理")
        
        try:
            mode_choice = input("请输入选择 (1-2): ").strip()
            
            if mode_choice not in ['1', '2']:
                print("❌ 无效选择")
                return
            
            # 获取用户需求
            print(f"\n请描述您想从文献中提取的信息:")
            print("(例如: 提取材料性质、合成方法和实验数据)")
            requirements = input("> ").strip()
            
            if not requirements:
                print("❌ 需求不能为空")
                return
            
            # 初始化Agent
            agent = LiteratureProcessingAgent()
            
            if mode_choice == "1":
                # 单文件处理
                if len(pdf_files) == 1:
                    selected_pdf = pdf_files[0]
                else:
                    print(f"\n请选择要处理的文件:")
                    file_choice = int(input(f"请输入文件编号 (1-{len(pdf_files)}): ")) - 1
                    if 0 <= file_choice < len(pdf_files):
                        selected_pdf = pdf_files[file_choice]
                    else:
                        print("❌ 无效选择")
                        return
                
                print(f"\n🚀 开始处理: {selected_pdf.name}")
                result = agent.process_single_pdf(str(selected_pdf), requirements)
                
                if result:
                    print(f"\n✅ 处理完成!")
                    print(f"📁 结果目录: {result['result_dir']}")
                else:
                    print(f"\n❌ 处理失败")
            
            elif mode_choice == "2":
                # 批量处理
                print(f"\n🚀 开始批量处理 {len(pdf_files)} 个文件")
                confirm = input("确认继续? (y/N): ").strip().lower()
                if confirm != 'y':
                    print("❌ 用户取消")
                    return
                
                result = agent.process_batch_pdfs([str(f) for f in pdf_files], requirements)
                
                if result:
                    print(f"\n✅ 批量处理完成!")
                    print(f"📊 成功处理: {result['total_processed']}/{result['total_files']} 个文件")
                    print(f"📁 报告目录: {result['batch_report_dir']}")
                else:
                    print(f"\n❌ 批量处理失败")
                    
        except KeyboardInterrupt:
            print("\n👋 用户中断")
        except ValueError:
            print("❌ 输入无效")
        except Exception as e:
            print(f"❌ 处理出错: {e}")
            
    except Exception as e:
        print(f"❌ 启动CLI失败: {e}")

def run_demo():
    """运行演示示例"""
    print("🚀 运行演示示例...")
    
    # 检查是否有示例PDF文件
    pdf_files = list(Path('.').glob('*.pdf'))
    
    if not pdf_files:
        print("❌ 当前目录没有找到PDF文件用于演示")
        print("请将PDF文件放在当前目录中，然后重新运行演示。")
        return
    
    print(f"📄 找到 {len(pdf_files)} 个PDF文件:")
    for i, pdf in enumerate(pdf_files, 1):
        size = os.path.getsize(pdf) / (1024*1024)
        print(f"  {i}. {pdf.name} ({size:.1f} MB)")
    
    # 选择文件
    if len(pdf_files) == 1:
        selected_pdf = pdf_files[0]
        print(f"\n📄 自动选择: {selected_pdf.name}")
    else:
        try:
            choice = int(input(f"\n请选择要演示的文件 (1-{len(pdf_files)}): ")) - 1
            if 0 <= choice < len(pdf_files):
                selected_pdf = pdf_files[choice]
            else:
                print("❌ 无效选择")
                return
        except (ValueError, KeyboardInterrupt):
            print("❌ 输入无效或用户取消")
            return
    
    # 演示需求
    demo_requirements = """提取以下信息：
1. 材料的化学名称和分子式
2. 合成方法和实验条件
3. 主要性能参数和测试结果
4. 材料的应用领域和优势
5. 实验中使用的主要设备和方法"""
    
    print(f"\n🎯 演示提取需求:")
    print(demo_requirements)
    
    # 确认演示
    confirm = input("\n确认开始演示? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ 用户取消演示")
        return
    
    try:
        from literature_processing_agent import LiteratureProcessingAgent
        
        print("\n" + "="*60)
        print("开始演示处理...")
        
        # 创建Agent并处理
        agent = LiteratureProcessingAgent()
        result = agent.process_single_pdf(str(selected_pdf), demo_requirements)
        
        if result:
            print("\n🎉 演示完成!")
            print(f"📁 结果保存在: {result['result_dir']}")
            print("\n📋 演示结果概览:")
            print(f"- 信息提取: {'✅' if result['extracted_info'] else '❌'}")
            print(f"- 思维导图: {'✅' if result['mindmap_data'] else '❌'}")
            
            # 显示提取信息的简要概览
            if result['extracted_info']:
                import json
                info_str = json.dumps(result['extracted_info'], ensure_ascii=False, indent=2)
                print(f"\n📄 提取信息预览 (前500字符):")
                print("-" * 40)
                print(info_str[:500] + "..." if len(info_str) > 500 else info_str)
                print("-" * 40)
            
            print(f"\n💡 查看完整结果请访问: {result['result_dir']}")
        else:
            print("\n❌ 演示处理失败")
            
    except Exception as e:
        print(f"❌ 演示运行失败: {e}")

def show_help():
    """显示帮助信息"""
    help_text = """
🔬 文献处理Agent - 全流程PDF文献分析工具

功能特点:
• 📄 PDF文档智能解析 (使用MinerU API)
• 🧠 根据用户需求动态生成提取提示词
• 🔍 基于大模型的信息提取 (使用O3 API)
• 🗺️ 自动生成文献思维导图
• 📊 支持单文件和批量处理
• 🖥️ 提供图形界面和命令行界面

使用方法:

1. 图形界面 (推荐):
   python run_agent.py gui
   
   特点: 友好的图形界面，支持拖拽文件，实时进度显示

2. 命令行界面:
   python run_agent.py cli
   
   特点: 交互式命令行界面，自动检测PDF文件，引导式操作

3. 运行演示:
   python run_agent.py demo
   
   特点: 快速体验功能，使用预设需求演示完整流程

4. 高级用法 - 直接命令行参数:
   python literature_processing_agent.py single --pdf "文件.pdf" --requirements "提取需求"
   python literature_processing_agent.py batch --dir "PDF目录" --requirements "提取需求"

环境要求:
• Python 3.7+
• tkinter (GUI界面)
• requests, openai (API调用)
• 有效的MinerU API token (在mineru_pdf_parser.py中配置)
• 有效的O3 API key (在literature_processing_agent.py中配置)

输出结果:
• extracted_information.json - 结构化提取信息
• mindmap.json - 思维导图数据
• mindmap.mmd - Mermaid格式思维导图
• processing_report.md - 处理报告

注意事项:
• 请将PDF文件放在当前目录中
• PDF文件大小不超过200MB
• 确保网络连接正常（需要调用API）
• 首次使用建议先运行演示: python run_agent.py demo

快速开始:
1. 将PDF文件放在当前目录
2. 运行: python run_agent.py gui (图形界面) 或 python run_agent.py cli (命令行)
3. 按提示输入提取需求
4. 等待处理完成，查看结果

如需帮助，请查看README.md或INSTALL.md。
"""
    print(help_text)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="文献处理Agent启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_agent.py gui     # 启动图形界面
  python run_agent.py cli     # 启动命令行界面  
  python run_agent.py demo    # 运行演示
        """
    )
    
    parser.add_argument("mode", nargs='?', choices=["gui", "cli", "demo"], 
                       default="gui", help="启动模式")
    
    args = parser.parse_args()
    
    # 显示标题
    print("="*60)
    print("🔬 文献处理Agent - 全流程PDF文献分析工具")
    print("="*60)
    
    # 检查依赖和文件
    if not check_dependencies():
        return 1
    
    if not check_files():
        return 1
    
    # 根据模式启动
    if args.mode == "gui":
        run_gui()
    elif args.mode == "cli":
        run_cli()
    elif args.mode == "demo":
        run_demo()
    else:
        show_help()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，程序退出")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)