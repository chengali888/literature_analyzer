#!/usr/bin/env python3
"""
文献处理Agent - Gradio高端图形界面
使用Gradio创建专业级的Web界面，支持文件上传、实时处理和结果可视化

功能特点:
- 🎨 现代化的Web界面设计
- 📁 拖拽式文件上传，支持多文件选择
- 🔄 实时处理进度和日志显示
- 📊 结果可视化和交互式展示
- 🧠 思维导图在线预览
- 💾 一键导出和下载功能
- 📱 响应式设计，支持移动端

作者: AI Assistant
日期: 2025年1月
"""

import gradio as gr
import json
import os
import time
import threading
from datetime import datetime
from pathlib import Path
import tempfile
import shutil
from typing import List, Optional, Tuple, Dict, Any

# 导入我们的核心模块
from literature_processing_agent import LiteratureProcessingAgent

class LiteratureAgentGradio:
    """基于Gradio的高端文献处理Agent界面"""
    
    def __init__(self):
        self.agent = LiteratureProcessingAgent()
        self.current_results = None
        self.processing_status = {"is_processing": False, "progress": 0, "message": ""}
        self.log_messages = []
        
    def add_log(self, message: str) -> str:
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_messages.append(log_entry)
        # 保持最新100条日志
        if len(self.log_messages) > 100:
            self.log_messages = self.log_messages[-100:]
        return "\n".join(self.log_messages)
    
    def update_status(self, message: str, progress: int = None) -> Tuple[str, str]:
        """更新处理状态"""
        self.processing_status["message"] = message
        if progress is not None:
            self.processing_status["progress"] = progress
        
        log_output = self.add_log(message)
        progress_text = f"进度: {self.processing_status['progress']}% | {message}"
        return progress_text, log_output
    
    def validate_files(self, files: List) -> Tuple[bool, str]:
        """验证上传的文件"""
        if not files:
            return False, "❌ 请上传至少一个PDF文件"
        
        valid_files = []
        errors = []
        
        for file in files:
            if not file:
                continue
                
            file_path = file.name if hasattr(file, 'name') else str(file)
            
            # 检查文件扩展名
            if not file_path.lower().endswith('.pdf'):
                errors.append(f"⚠️ {os.path.basename(file_path)}: 不是PDF文件")
                continue
            
            # 检查文件大小
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 200 * 1024 * 1024:  # 200MB
                    errors.append(f"⚠️ {os.path.basename(file_path)}: 文件过大 ({file_size/(1024*1024):.1f}MB > 200MB)")
                    continue
                valid_files.append(file_path)
            except:
                errors.append(f"⚠️ {os.path.basename(file_path)}: 无法读取文件")
        
        if not valid_files:
            return False, "❌ 没有有效的PDF文件\n" + "\n".join(errors)
        
        status_msg = f"✅ 发现 {len(valid_files)} 个有效PDF文件"
        if errors:
            status_msg += f"\n\n⚠️ 跳过的文件:\n" + "\n".join(errors)
        
        return True, status_msg
    
    def process_single_file(self, file, requirements: str, progress=gr.Progress()) -> Tuple[str, str, str, str, str]:
        """处理单个文件"""
        try:
            # 验证输入
            if not file:
                return "❌ 请上传PDF文件", "", "", "", ""
            
            if not requirements.strip():
                return "❌ 请输入提取需求", "", "", "", ""
            
            # 更新状态
            progress(0.1, desc="验证文件...")
            self.processing_status["is_processing"] = True
            
            file_path = file.name
            filename = os.path.basename(file_path)
            
            progress(0.2, desc=f"开始处理 {filename}...")
            status, log = self.update_status(f"🚀 开始处理文件: {filename}")
            
            # 调用处理Agent
            def progress_callback(step, message):
                if step == "pdf_parsing":
                    progress(0.3, desc="解析PDF文档...")
                elif step == "prompt_generation":
                    progress(0.5, desc="生成提取提示词...")
                elif step == "information_extraction":
                    progress(0.7, desc="提取文献信息...")
                elif step == "mindmap_generation":
                    progress(0.9, desc="生成思维导图...")
                self.update_status(message)
            
            # 执行处理
            result = self.agent.process_single_pdf(file_path, requirements)
            
            if result:
                progress(1.0, desc="处理完成!")
                self.current_results = result
                
                # 格式化结果
                status_msg = f"✅ 处理完成!\n📁 结果目录: {result['result_dir']}"
                
                # 提取信息展示
                info_json = ""
                if result.get('extracted_info'):
                    info_json = json.dumps(result['extracted_info'], ensure_ascii=False, indent=2)
                
                # 思维导图展示
                mindmap_content = ""
                mindmap_html = ""
                if result.get('mermaid_code'):
                    mindmap_content = f"```mermaid\n{result['mermaid_code']}\n```"
                    mindmap_html = self.generate_mermaid_html(result['mermaid_code'])
                elif result.get('mindmap_data'):
                    mindmap_content = json.dumps(result['mindmap_data'], ensure_ascii=False, indent=2)
                    mindmap_html = "<div style='text-align:center; padding:20px; color:#666;'>思维导图数据格式不支持可视化，请查看左侧文本</div>"
                else:
                    mindmap_content = "思维导图生成失败"
                    mindmap_html = "<div style='text-align:center; padding:20px; color:#666;'>思维导图生成失败</div>"
                
                # 处理报告
                report = self.generate_processing_report(result, requirements)
                
                final_log = self.add_log("🎉 所有处理步骤完成!")
                
                return status_msg, info_json, mindmap_content, mindmap_html, report
            else:
                error_msg = "❌ 处理失败，请查看日志了解详情"
                return error_msg, "", "", "", ""
                
        except Exception as e:
            error_msg = f"❌ 处理过程中出错: {str(e)}"
            self.add_log(error_msg)
            return error_msg, "", "", "", ""
        
        finally:
            self.processing_status["is_processing"] = False
    
    def process_batch_files(self, files: List, requirements: str, progress=gr.Progress()) -> Tuple[str, str, str, str]:
        """批量处理文件"""
        try:
            # 验证输入
            if not files:
                return "❌ 请上传PDF文件", "", "", ""
            
            if not requirements.strip():
                return "❌ 请输入提取需求", "", "", ""
            
            # 验证文件
            is_valid, validation_msg = self.validate_files(files)
            if not is_valid:
                return validation_msg, "", "", ""
            
            # 获取有效文件路径
            valid_files = []
            for file in files:
                if file and file.name.lower().endswith('.pdf'):
                    valid_files.append(file.name)
            
            progress(0.1, desc=f"准备批量处理 {len(valid_files)} 个文件...")
            self.processing_status["is_processing"] = True
            
            # 执行批量处理
            result = self.agent.process_batch_pdfs(valid_files, requirements)
            
            if result:
                progress(1.0, desc="批量处理完成!")
                self.current_results = result
                
                # 格式化批量结果
                status_msg = f"✅ 批量处理完成!\n"
                status_msg += f"📊 成功处理: {result['total_processed']}/{result['total_files']} 个文件\n"
                status_msg += f"📁 报告目录: {result['batch_report_dir']}"
                
                # 批量信息展示
                batch_info = self.format_batch_results(result)
                
                # 批量报告
                report = self.generate_batch_report(result, requirements)
                
                return status_msg, batch_info, "批量处理的思维导图请查看各个文件的结果目录", report
            else:
                return "❌ 批量处理失败", "", "", ""
                
        except Exception as e:
            error_msg = f"❌ 批量处理出错: {str(e)}"
            return error_msg, "", "", ""
        
        finally:
            self.processing_status["is_processing"] = False
    
    def format_batch_results(self, result: Dict) -> str:
        """格式化批量处理结果"""
        output = f"# 批量处理结果概览\n\n"
        output += f"**总文件数**: {result['total_files']}\n"
        output += f"**成功处理**: {result['total_processed']}\n"
        output += f"**成功率**: {result['total_processed']/result['total_files']*100:.1f}%\n\n"
        
        output += "## 文件处理详情\n\n"
        
        for i, file_result in enumerate(result.get('results', []), 1):
            extract_dir = file_result['processing_info']['extract_dir']
            filename = os.path.basename(extract_dir)
            
            output += f"### {i}. {filename}\n\n"
            
            # 处理状态
            if file_result['extracted_data']:
                output += "- ✅ **信息提取**: 成功\n"
            else:
                output += "- ❌ **信息提取**: 失败\n"
            
            if file_result['mindmap_data']:
                output += "- ✅ **思维导图**: 已生成\n"
            else:
                output += "- ❌ **思维导图**: 生成失败\n"
            
            # 简要信息预览
            if file_result['extracted_data']:
                data_preview = str(file_result['extracted_data'])[:200]
                output += f"- **信息预览**: {data_preview}...\n"
            
            output += "\n"
        
        return output
    
    def generate_processing_report(self, result: Dict, requirements: str) -> str:
        """生成处理报告"""
        report = f"# 文献处理报告\n\n"
        report += f"**处理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**用户需求**: {requirements}\n\n"
        
        report += "## 处理结果\n\n"
        report += f"- **结果目录**: {result.get('result_dir', 'N/A')}\n"
        report += f"- **信息提取**: {'✅ 成功' if result.get('extracted_info') else '❌ 失败'}\n"
        report += f"- **思维导图**: {'✅ 已生成' if result.get('mindmap_data') else '❌ 生成失败'}\n\n"
        
        if result.get('dynamic_prompts'):
            report += "## 生成的提示词\n\n"
            report += "```json\n"
            report += json.dumps(result['dynamic_prompts'], ensure_ascii=False, indent=2)
            report += "\n```\n\n"
        
        report += "---\n*由文献处理Agent自动生成*"
        return report
    
    def generate_batch_report(self, result: Dict, requirements: str) -> str:
        """生成批量处理报告"""
        report = f"# 批量文献处理报告\n\n"
        report += f"**处理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**用户需求**: {requirements}\n"
        report += f"**报告目录**: {result.get('batch_report_dir', 'N/A')}\n\n"
        
        report += "## 批量处理统计\n\n"
        report += f"- **总文件数**: {result['total_files']}\n"
        report += f"- **成功处理**: {result['total_processed']}\n"
        report += f"- **成功率**: {result['total_processed']/result['total_files']*100:.1f}%\n\n"
        
        report += "## 详细结果\n\n"
        for i, file_result in enumerate(result.get('results', []), 1):
            extract_dir = file_result['processing_info']['extract_dir']
            filename = os.path.basename(extract_dir)
            
            status_info = "✅ 成功" if file_result['extracted_data'] else "❌ 失败"
            mindmap_info = "✅ 已生成" if file_result['mindmap_data'] else "❌ 生成失败"
            
            report += f"{i}. **{filename}**: 信息提取 {status_info} | 思维导图 {mindmap_info}\n"
        
        report += "\n---\n*由文献处理Agent自动生成*"
        return report
    
    def generate_mermaid_html(self, mermaid_code: str) -> str:
        """生成在Gradio内嵌入显示的思维导图"""
        if not mermaid_code or mermaid_code.strip() == "":
            return "<div style='text-align:center; padding:20px; color:#666; border: 1px solid #ddd; border-radius: 8px;'>暂无思维导图</div>"
        
        # 清理Mermaid代码
        cleaned_code = mermaid_code.strip()
        if cleaned_code.startswith("```mermaid"):
            cleaned_code = cleaned_code.replace("```mermaid", "").replace("```", "").strip()
        elif cleaned_code.startswith("```"):
            cleaned_code = cleaned_code.replace("```", "").strip()
        
        # 生成独立HTML文件用于iframe嵌入
        import uuid
        import os
        
        file_id = uuid.uuid4().hex[:8]
        html_filename = f"mindmap_{file_id}.html"
        html_filepath = os.path.join(os.getcwd(), html_filename)
        
        # 创建独立的HTML文件，专门为iframe优化
        iframe_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>思维导图</title>
    <style>
        body {{ 
            margin: 0; 
            padding: 15px; 
            font-family: Arial, sans-serif; 
            background: #f8f9fa;
            overflow: auto;
        }}
        .mindmap-container {{ 
            background: white; 
            border-radius: 8px; 
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            min-height: 400px;
        }}
        .mermaid {{ 
            text-align: center;
            background: white;
        }}
        .loading {{
            text-align: center;
            color: #666;
            padding: 50px;
            font-size: 16px;
        }}
    </style>
</head>
<body>
    <div class="mindmap-container">
        <div id="loading" class="loading">🔄 正在生成思维导图...</div>
        <div class="mermaid" id="mindmap-content" style="display: none;">
{cleaned_code}
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
    <script>
        // 配置Mermaid
        mermaid.initialize({{
            startOnLoad: false,
            theme: 'default',
            securityLevel: 'loose',
            mindmap: {{
                padding: 20,
                useMaxWidth: true
            }}
        }});
        
        // 等待页面加载完成
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(function() {{
                try {{
                    // 获取元素
                    const loadingDiv = document.getElementById('loading');
                    const contentDiv = document.getElementById('mindmap-content');
                    
                    // 渲染思维导图
                    mermaid.init(undefined, contentDiv);
                    
                    // 隐藏loading，显示内容
                    loadingDiv.style.display = 'none';
                    contentDiv.style.display = 'block';
                    
                }} catch (error) {{
                    console.error('渲染错误:', error);
                    document.getElementById('loading').innerHTML = '⚠️ 渲染失败: ' + error.message;
                }}
            }}, 1000);
        }});
    </script>
</body>
</html>"""
        
        # 写入文件
        try:
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(iframe_html)
            
            # 返回iframe嵌入的HTML
            return f"""
<div style="width: 100%; height: 500px; border: 2px solid #3498db; border-radius: 8px; background: #ffffff; overflow: hidden;">
    <div style="background: #3498db; color: white; padding: 8px 15px; font-size: 14px; font-weight: bold;">
        🧠 思维导图可视化
    </div>
    <iframe 
        src="http://localhost:8080/{html_filename}" 
        width="100%" 
        height="460" 
        frameborder="0" 
        style="border: none; background: white;">
        <p>您的浏览器不支持iframe。请<a href="http://localhost:8080/{html_filename}" target="_blank">点击这里</a>查看思维导图。</p>
    </iframe>
</div>
            """
            
        except Exception as e:
            return f"""
<div style="padding: 40px; color: #e74c3c; background: #ffeaea; border: 2px solid #e74c3c; border-radius: 8px; text-align: center;">
    <div style="font-size: 18px; margin-bottom: 15px;">⚠️ 文件生成失败</div>
    <div style="font-size: 14px; margin-bottom: 10px;">错误: {str(e)}</div>
    <div style="font-size: 12px; color: #666;">请检查文件写入权限</div>
</div>
            """
    
    def generate_text_mindmap_visualization(self, mermaid_code: str) -> str:
        """生成文本版思维导图可视化（备用方案）"""
        if not mermaid_code or mermaid_code.strip() == "":
            return "<div style='text-align:center; padding:20px; color:#666;'>暂无思维导图</div>"
        
        # 解析Mermaid代码生成文本树
        lines = mermaid_code.strip().split('\n')
        text_tree = "📊 思维导图结构:\n\n"
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('mindmap'):
                continue
                
            # 计算缩进级别
            indent_level = 0
            original_line = line
            while line.startswith('  '):
                indent_level += 1
                line = line[2:]
            
            # 清理格式
            line = line.replace('root((', '').replace('))', '').replace('((', '').replace('))', '')
            
            # 生成树状结构
            prefix = "  " * indent_level
            if indent_level == 0:
                text_tree += f"🎯 {line}\n"
            elif indent_level == 1:
                text_tree += f"├── 📁 {line}\n"
            elif indent_level == 2:
                text_tree += f"│   ├── 📄 {line}\n"
            else:
                text_tree += f"{'│   ' * (indent_level-1)}├── • {line}\n"
        
        return f"""
<div style="width: 100%; height: 500px; border: 1px solid #ddd; border-radius: 8px; overflow: auto; background: #f8f9fa; padding: 20px; font-family: 'Courier New', monospace;">
    <div style="white-space: pre-line; line-height: 1.6; color: #2c3e50;">
{text_tree}
    </div>
    <div style="text-align: center; margin-top: 20px; color: #7f8c8d; font-size: 12px;">
        📝 文本版思维导图 | 如需图形版本，请检查网络连接
    </div>
</div>
        """
    
    def generate_demo_mindmap(self) -> Tuple[str, str]:
        """生成演示思维导图"""
        demo_mermaid = """mindmap
  root((📚 文献分析))
    🔍 研究背景
      问题定义
      研究意义
    ⚗️ 研究方法
      实验设计
      数据收集
    📊 主要发现
      关键结果
      数据分析
    💡 结论建议
      主要结论
      实际应用"""
        
        demo_html = self.generate_mermaid_html(demo_mermaid)
        return demo_mermaid, demo_html
    
    def get_preset_requirements(self) -> Dict[str, str]:
        """获取预设需求选项"""
        return {
            "材料科学研究": """从文献中提取以下材料科学信息：
1. 材料名称、化学式和结构信息
2. 合成方法和实验条件
3. 物理化学性质参数
4. 表征方法和测试结果
5. 应用领域和性能优势""",
            
            "实验数据提取": """提取以下实验相关信息：
1. 实验设计和方法流程
2. 实验条件和参数设置
3. 测量数据和统计结果
4. 对照组和实验组对比
5. 结论和数据分析""",
            
            "文献综述分析": """从综述文献中提取：
1. 研究领域和发展趋势
2. 主要技术方法对比
3. 关键研究成果汇总
4. 存在问题和挑战
5. 未来发展方向""",
            
            "技术方法研究": """提取技术方法相关信息：
1. 技术原理和创新点
2. 方法流程和关键步骤
3. 技术参数和优化条件
4. 性能评估和对比
5. 应用场景和局限性""",
            
            "自定义需求": ""
        }
    
    def download_results(self) -> str:
        """打包下载结果"""
        if not self.current_results:
            return "没有可下载的结果"
        
        try:
            # 创建临时ZIP文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"literature_results_{timestamp}.zip"
            
            # 这里应该实现ZIP打包逻辑
            # 由于Gradio的限制，我们返回结果目录路径
            result_dir = self.current_results.get('result_dir') or self.current_results.get('batch_report_dir')
            return f"结果保存在: {result_dir}"
            
        except Exception as e:
            return f"下载失败: {str(e)}"
    
    def create_interface(self):
        """创建Gradio界面"""
        # 自定义CSS样式
        custom_css = """
        .gradio-container {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .header-text {
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 0.5em;
        }
        .feature-box {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
        }
        .status-success {
            color: #28a745;
            font-weight: bold;
        }
        .status-error {
            color: #dc3545;
            font-weight: bold;
        }
        .status-processing {
            color: #007bff;
            font-weight: bold;
        }
        """
        
        # 创建界面
        with gr.Blocks(css=custom_css, title="文献处理Agent", theme=gr.themes.Soft()) as interface:
            
            # 标题和介绍
            gr.HTML("""
            <div class="header-text">🔬 文献处理Agent</div>
            <div style="text-align: center; margin-bottom: 2em;">
                <p style="font-size: 1.2em; color: #666;">
                    全流程PDF文献分析工具 | 智能信息提取 | 思维导图生成
                </p>
            </div>
            """)
            
            # 功能特点展示
            with gr.Row():
                gr.HTML("""
                <div class="feature-box">
                    <h3>🚀 核心功能</h3>
                    <ul>
                        <li>📄 <b>智能PDF解析</b> - 使用MinerU API高质量解析</li>
                        <li>🧠 <b>动态信息提取</b> - 根据需求自动生成提示词</li>
                        <li>🗺️ <b>思维导图生成</b> - 可视化文献核心内容</li>
                        <li>📊 <b>批量处理</b> - 支持大量文件高效处理</li>
                    </ul>
                </div>
                """)
            
            # 主要功能区域
            with gr.Tabs() as tabs:
                
                # 单文件处理标签页
                with gr.TabItem("📄 单文件处理", id="single"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### 📁 文件上传")
                            single_file = gr.File(
                                label="选择PDF文件", 
                                file_types=[".pdf"],
                                type="filepath"
                            )
                            
                            gr.Markdown("### 🎯 提取需求")
                            
                            # 预设需求选择
                            preset_dropdown = gr.Dropdown(
                                choices=list(self.get_preset_requirements().keys()),
                                label="快速选择预设需求",
                                value="自定义需求",
                                interactive=True
                            )
                            
                            # 需求输入框
                            single_requirements = gr.Textbox(
                                label="详细需求描述",
                                placeholder="请详细描述您想从文献中提取的信息...",
                                lines=6,
                                max_lines=10
                            )
                            
                            # 处理按钮
                            single_process_btn = gr.Button(
                                "🚀 开始处理", 
                                variant="primary",
                                size="lg"
                            )
                        
                        with gr.Column(scale=2):
                            # 处理状态显示
                            single_status = gr.Textbox(
                                label="📊 处理状态",
                                interactive=False,
                                lines=3
                            )
                    
                    # 结果展示区域
                    with gr.Row():
                        with gr.Tabs():
                            with gr.TabItem("📋 提取信息"):
                                single_info_output = gr.Textbox(
                                    label="结构化信息 (JSON格式)",
                                    lines=15,
                                    max_lines=20,
                                    interactive=False
                                )
                            
                            with gr.TabItem("🧠 思维导图"):
                                with gr.Row():
                                    with gr.Column(scale=1):
                                        single_mindmap_output = gr.Textbox(
                                            label="思维导图代码 (Mermaid格式)",
                                            lines=15,
                                            max_lines=20,
                                            interactive=False
                                        )
                                    with gr.Column(scale=1):
                                        single_mindmap_visual = gr.HTML(
                                            label="思维导图可视化 (内嵌显示)",
                                            value="<div style='text-align:center; padding:20px; color:#666;'>处理完成后将显示交互式思维导图</div>"
                                        )
                            
                            with gr.TabItem("📄 处理报告"):
                                single_report_output = gr.Textbox(
                                    label="处理报告 (Markdown格式)",
                                    lines=15,
                                    max_lines=20,
                                    interactive=False
                                )
                
                # 批量处理标签页
                with gr.TabItem("📊 批量处理", id="batch"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### 📁 批量文件上传")
                            batch_files = gr.File(
                                label="选择多个PDF文件", 
                                file_count="multiple",
                                file_types=[".pdf"],
                                type="filepath"
                            )
                            
                            gr.Markdown("### 🎯 批量提取需求")
                            
                            # 批量预设需求
                            batch_preset_dropdown = gr.Dropdown(
                                choices=list(self.get_preset_requirements().keys()),
                                label="批量处理预设需求",
                                value="自定义需求",
                                interactive=True
                            )
                            
                            batch_requirements = gr.Textbox(
                                label="批量处理需求描述",
                                placeholder="请描述要从所有文献中统一提取的信息...",
                                lines=6,
                                max_lines=10
                            )
                            
                            # 批量处理按钮
                            batch_process_btn = gr.Button(
                                "🚀 开始批量处理", 
                                variant="primary",
                                size="lg"
                            )
                        
                        with gr.Column(scale=2):
                            # 批量处理状态
                            batch_status = gr.Textbox(
                                label="📊 批量处理状态",
                                interactive=False,
                                lines=3
                            )
                    
                    # 批量结果展示
                    with gr.Row():
                        with gr.Tabs():
                            with gr.TabItem("📊 批量结果"):
                                batch_info_output = gr.Textbox(
                                    label="批量处理结果概览",
                                    lines=15,
                                    max_lines=20,
                                    interactive=False
                                )
                            
                            with gr.TabItem("🗺️ 批量思维导图"):
                                gr.Markdown("### 📊 批量处理思维导图说明")
                                batch_mindmap_output = gr.Textbox(
                                    label="说明信息",
                                    lines=8,
                                    max_lines=10,
                                    interactive=False,
                                    value="批量处理的思维导图保存在各个文件的结果目录中。每个文件都有独立的思维导图可视化文件。"
                                )
                            
                            with gr.TabItem("📄 批量报告"):
                                batch_report_output = gr.Textbox(
                                    label="批量处理报告",
                                    lines=15,
                                    max_lines=20,
                                    interactive=False
                                )
                
                # 实时日志和帮助标签页
                with gr.TabItem("📋 实时日志", id="logs"):
                    log_output = gr.Textbox(
                        label="📋 处理日志",
                        lines=20,
                        max_lines=25,
                        interactive=False,
                        autoscroll=True
                    )
                    
                    with gr.Row():
                        clear_logs_btn = gr.Button("🗑️ 清空日志")
                        refresh_logs_btn = gr.Button("🔄 刷新日志", size="sm")
                        download_logs_btn = gr.Button("💾 下载日志")
                
                # 帮助和设置标签页
                with gr.TabItem("❓ 帮助与设置", id="help"):
                    gr.Markdown("""
                    ## 📖 使用指南
                    
                    ### 🔧 准备工作
                    1. **API配置**: 确保已正确配置MinerU和O3 API密钥
                    2. **文件准备**: 将PDF文件准备好，单文件≤200MB
                    3. **需求描述**: 明确要提取的信息类型和格式
                    
                    ### 🚀 快速开始
                    1. **单文件处理**: 上传单个PDF，描述提取需求，点击处理
                    2. **批量处理**: 选择多个PDF文件，统一设置提取需求
                    3. **查看结果**: 在对应标签页查看提取信息、思维导图和报告
                    
                    ### 💡 提取需求建议
                    - **具体明确**: 详细说明要提取的字段和格式
                    - **结构化**: 使用编号列表组织需求
                    - **专业术语**: 使用领域专业词汇提高准确性
                    
                    ### ⚠️ 注意事项
                    - PDF文件大小限制：200MB
                    - 需要稳定的网络连接
                    - 处理时间取决于文件大小和复杂度
                    - 批量处理建议一次不超过10个文件
                    
                    ### 🔗 技术支持
                    如遇问题请查看日志信息或联系技术支持。
                    """)
                    
                    # 思维导图演示
                    gr.Markdown("### 🧠 思维导图演示")
                    demo_mindmap_btn = gr.Button("🎯 生成演示思维导图", variant="secondary", size="lg")
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            demo_mindmap_code = gr.Textbox(
                                label="演示思维导图代码",
                                lines=10,
                                max_lines=15,
                                interactive=False
                            )
                        with gr.Column(scale=1):
                            demo_mindmap_visual = gr.HTML(
                                label="演示思维导图可视化",
                                value="<div style='text-align:center; padding:40px; color:#666; border: 1px solid #ddd; border-radius: 8px;'>点击上方按钮生成演示思维导图</div>"
                            )
                    
                    # 系统状态
                    with gr.Row():
                        system_status = gr.Textbox(
                            label="🔧 系统状态",
                            value="✅ 系统就绪",
                            interactive=False
                        )
            
            # 预设需求变更事件处理
            def update_requirements(preset_choice):
                presets = self.get_preset_requirements()
                return presets.get(preset_choice, "")
            
            preset_dropdown.change(
                fn=update_requirements,
                inputs=[preset_dropdown],
                outputs=[single_requirements]
            )
            
            batch_preset_dropdown.change(
                fn=update_requirements,
                inputs=[batch_preset_dropdown],
                outputs=[batch_requirements]
            )
            
            # 处理按钮事件
            single_process_btn.click(
                fn=self.process_single_file,
                inputs=[single_file, single_requirements],
                outputs=[single_status, single_info_output, single_mindmap_output, single_mindmap_visual, single_report_output]
            )
            
            batch_process_btn.click(
                fn=self.process_batch_files,
                inputs=[batch_files, batch_requirements],
                outputs=[batch_status, batch_info_output, batch_mindmap_output, batch_report_output]
            )
            
            # 日志管理
            def clear_logs():
                self.log_messages = []
                return ""
            
            clear_logs_btn.click(
                fn=clear_logs,
                outputs=[log_output]
            )
            
            # 定期更新日志显示
            def update_logs():
                return "\n".join(self.log_messages)
            
            # 刷新日志按钮事件
            refresh_logs_btn.click(
                fn=update_logs,
                outputs=[log_output]
            )
            
            # 演示思维导图按钮事件
            demo_mindmap_btn.click(
                fn=self.generate_demo_mindmap,
                outputs=[demo_mindmap_code, demo_mindmap_visual]
            )
        
        return interface
    
    def launch(self, **kwargs):
        """启动Gradio应用"""
        interface = self.create_interface()
        
        # 默认启动参数
        launch_params = {
            "server_name": "0.0.0.0",
            "server_port": 7860,
            "share": False,
            "debug": False,
            "quiet": False,
            "inbrowser": True
        }
        
        # 更新用户提供的参数
        launch_params.update(kwargs)
        
        # 启动界面
        print("🚀 启动文献处理Agent Gradio界面...")
        print(f"🌐 访问地址: http://localhost:{launch_params['server_port']}")
        
        interface.launch(**launch_params)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="文献处理Agent - Gradio界面")
    parser.add_argument("--port", type=int, default=7860, help="服务器端口")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机")
    parser.add_argument("--share", action="store_true", help="生成公共链接")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    
    args = parser.parse_args()
    
    # 创建并启动应用
    app = LiteratureAgentGradio()
    app.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        debug=args.debug
    )


if __name__ == "__main__":
    main()