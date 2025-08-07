#!/usr/bin/env python3
"""
文献处理Agent图形用户界面
提供友好的GUI界面来使用全流程文献处理功能

功能包括：
1. 文件选择和拖拽支持
2. 用户需求输入
3. 实时处理进度显示
4. 结果查看和导出
5. 思维导图预览

作者: AI Assistant
日期: 2025年1月
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import json
import webbrowser
from pathlib import Path
from datetime import datetime

# 导入我们的文献处理Agent
from literature_processing_agent import LiteratureProcessingAgent

class LiteratureAgentGUI:
    """文献处理Agent图形用户界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("文献处理Agent - 全流程PDF文献分析工具")
        self.root.geometry("1200x800")
        
        # 初始化Agent
        self.agent = LiteratureProcessingAgent()
        
        # 状态变量
        self.selected_files = []
        self.processing = False
        self.current_results = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="文献处理Agent", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 文件选择区域
        self.setup_file_selection(main_frame)
        
        # 需求输入区域
        self.setup_requirements_input(main_frame)
        
        # 控制按钮区域
        self.setup_control_buttons(main_frame)
        
        # 进度显示区域
        self.setup_progress_area(main_frame)
        
        # 结果显示区域
        self.setup_results_area(main_frame)
        
    def setup_file_selection(self, parent):
        """设置文件选择区域"""
        # 文件选择框架
        file_frame = ttk.LabelFrame(parent, text="📁 选择PDF文件", padding="10")
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        
        # 文件列表
        self.file_listbox = tk.Listbox(file_frame, height=6, selectmode=tk.EXTENDED)
        self.file_listbox.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 文件操作按钮
        ttk.Button(file_frame, text="选择单个文件", command=self.select_single_file).grid(row=1, column=0, padx=(0, 5))
        ttk.Button(file_frame, text="选择多个文件", command=self.select_multiple_files).grid(row=1, column=1, padx=5)
        ttk.Button(file_frame, text="清空列表", command=self.clear_file_list).grid(row=1, column=2, padx=(5, 0))
        
        # 文件信息标签
        self.file_info_label = ttk.Label(file_frame, text="尚未选择文件")
        self.file_info_label.grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
    def setup_requirements_input(self, parent):
        """设置需求输入区域"""
        req_frame = ttk.LabelFrame(parent, text="🎯 提取需求", padding="10")
        req_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        req_frame.columnconfigure(0, weight=1)
        
        # 需求输入框
        ttk.Label(req_frame, text="请描述您想从文献中提取的信息：").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.requirements_text = scrolledtext.ScrolledText(req_frame, height=4, wrap=tk.WORD)
        self.requirements_text.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 预设需求按钮
        preset_frame = ttk.Frame(req_frame)
        preset_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(preset_frame, text="快速选择：").grid(row=0, column=0, sticky=tk.W)
        
        presets = [
            ("材料性质", "提取材料的化学结构、物理性质、合成方法和应用信息"),
            ("实验数据", "提取实验条件、测量数据、性能参数和实验结果"),
            ("文献综述", "提取主要观点、研究趋势、技术对比和未来展望"),
            ("化学反应", "提取反应机理、催化剂、反应条件和产物信息")
        ]
        
        for i, (name, req) in enumerate(presets):
            ttk.Button(preset_frame, text=name, 
                      command=lambda r=req: self.set_preset_requirement(r)).grid(row=0, column=i+1, padx=(10, 0))
    
    def setup_control_buttons(self, parent):
        """设置控制按钮区域"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        # 处理模式选择
        self.mode_var = tk.StringVar(value="single")
        ttk.Radiobutton(control_frame, text="单个文件处理", variable=self.mode_var, 
                       value="single").grid(row=0, column=0, padx=(0, 20))
        ttk.Radiobutton(control_frame, text="批量处理", variable=self.mode_var, 
                       value="batch").grid(row=0, column=1, padx=(0, 20))
        
        # 主要按钮
        self.start_button = ttk.Button(control_frame, text="🚀 开始处理", 
                                      command=self.start_processing, style="Accent.TButton")
        self.start_button.grid(row=0, column=2, padx=(20, 10))
        
        self.stop_button = ttk.Button(control_frame, text="⏹️ 停止", 
                                     command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=3, padx=(0, 10))
        
        ttk.Button(control_frame, text="📁 打开结果目录", 
                  command=self.open_results_folder).grid(row=0, column=4, padx=(0, 10))
        
    def setup_progress_area(self, parent):
        """设置进度显示区域"""
        progress_frame = ttk.LabelFrame(parent, text="📊 处理进度", padding="10")
        progress_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           mode='indeterminate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 状态标签
        self.status_label = ttk.Label(progress_frame, text="就绪")
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        
        # 日志输出
        self.log_text = scrolledtext.ScrolledText(progress_frame, height=8, wrap=tk.WORD)
        self.log_text.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def setup_results_area(self, parent):
        """设置结果显示区域"""
        results_frame = ttk.LabelFrame(parent, text="📋 处理结果", padding="10")
        results_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # 创建标签页
        self.results_notebook = ttk.Notebook(results_frame)
        self.results_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 提取信息标签页
        self.info_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.info_frame, text="📄 提取信息")
        
        self.info_text = scrolledtext.ScrolledText(self.info_frame, wrap=tk.WORD)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 思维导图标签页
        self.mindmap_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.mindmap_frame, text="🧠 思维导图")
        
        self.mindmap_text = scrolledtext.ScrolledText(self.mindmap_frame, wrap=tk.WORD)
        self.mindmap_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 导出按钮
        export_frame = ttk.Frame(results_frame)
        export_frame.grid(row=1, column=0, pady=(10, 0))
        
        ttk.Button(export_frame, text="💾 导出JSON", command=self.export_json).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="🧠 导出思维导图", command=self.export_mindmap).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="📄 生成报告", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        
        # 配置行权重
        parent.rowconfigure(5, weight=1)
    
    def select_single_file(self):
        """选择单个文件"""
        file_path = filedialog.askopenfilename(
            title="选择PDF文件",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_path:
            self.selected_files = [file_path]
            self.update_file_list()
            self.mode_var.set("single")
    
    def select_multiple_files(self):
        """选择多个文件"""
        file_paths = filedialog.askopenfilenames(
            title="选择PDF文件",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_paths:
            self.selected_files = list(file_paths)
            self.update_file_list()
            self.mode_var.set("batch")
    
    def clear_file_list(self):
        """清空文件列表"""
        self.selected_files = []
        self.update_file_list()
    
    def update_file_list(self):
        """更新文件列表显示"""
        self.file_listbox.delete(0, tk.END)
        for file_path in self.selected_files:
            filename = os.path.basename(file_path)
            self.file_listbox.insert(tk.END, filename)
        
        # 更新信息标签
        if not self.selected_files:
            self.file_info_label.config(text="尚未选择文件")
        else:
            total_size = sum(os.path.getsize(f) for f in self.selected_files if os.path.exists(f))
            size_mb = total_size / (1024 * 1024)
            self.file_info_label.config(text=f"已选择 {len(self.selected_files)} 个文件，总大小: {size_mb:.1f} MB")
    
    def set_preset_requirement(self, requirement):
        """设置预设需求"""
        self.requirements_text.delete(1.0, tk.END)
        self.requirements_text.insert(1.0, requirement)
    
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_status(self, status):
        """更新状态显示"""
        self.status_label.config(text=status)
        self.root.update_idletasks()
    
    def start_processing(self):
        """开始处理"""
        # 验证输入
        if not self.selected_files:
            messagebox.showerror("错误", "请先选择PDF文件")
            return
        
        requirements = self.requirements_text.get(1.0, tk.END).strip()
        if not requirements:
            messagebox.showerror("错误", "请输入提取需求")
            return
        
        # 检查文件是否存在
        missing_files = [f for f in self.selected_files if not os.path.exists(f)]
        if missing_files:
            messagebox.showerror("错误", f"以下文件不存在:\n" + "\n".join(missing_files))
            return
        
        # 启动处理线程
        self.processing = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start()
        
        # 清空结果区域
        self.info_text.delete(1.0, tk.END)
        self.mindmap_text.delete(1.0, tk.END)
        self.log_text.delete(1.0, tk.END)
        
        # 在后台线程中执行处理
        processing_thread = threading.Thread(
            target=self.process_files_thread,
            args=(self.selected_files.copy(), requirements, self.mode_var.get())
        )
        processing_thread.daemon = True
        processing_thread.start()
    
    def process_files_thread(self, files, requirements, mode):
        """在后台线程中处理文件"""
        try:
            self.log_message("开始处理文件...")
            self.update_status("正在处理...")
            
            if mode == "single" or len(files) == 1:
                # 单文件处理
                self.log_message(f"处理单个文件: {os.path.basename(files[0])}")
                result = self.agent.process_single_pdf(files[0], requirements)
                
                if result:
                    self.current_results = result
                    self.log_message("✅ 处理完成!")
                    self.display_single_result(result)
                else:
                    self.log_message("❌ 处理失败")
                    
            else:
                # 批量处理
                self.log_message(f"批量处理 {len(files)} 个文件")
                result = self.agent.process_batch_pdfs(files, requirements)
                
                if result:
                    self.current_results = result
                    self.log_message(f"✅ 批量处理完成! 成功处理 {result['total_processed']}/{result['total_files']} 个文件")
                    self.display_batch_results(result)
                else:
                    self.log_message("❌ 批量处理失败")
        
        except Exception as e:
            self.log_message(f"❌ 处理过程中出错: {str(e)}")
        
        finally:
            # 重置UI状态
            self.root.after(0, self.processing_finished)
    
    def display_single_result(self, result):
        """显示单文件处理结果"""
        def update_ui():
            # 显示提取信息
            if result['extracted_info']:
                info_json = json.dumps(result['extracted_info'], ensure_ascii=False, indent=2)
                self.info_text.insert(1.0, info_json)
            else:
                self.info_text.insert(1.0, "无法提取信息")
            
            # 显示思维导图
            if result['mermaid_code']:
                mindmap_content = f"Mermaid思维导图代码:\n\n{result['mermaid_code']}\n\n"
                if result['mindmap_data']:
                    mindmap_content += f"思维导图数据:\n{json.dumps(result['mindmap_data'], ensure_ascii=False, indent=2)}"
                self.mindmap_text.insert(1.0, mindmap_content)
            else:
                self.mindmap_text.insert(1.0, "无法生成思维导图")
        
        self.root.after(0, update_ui)
    
    def display_batch_results(self, result):
        """显示批量处理结果"""
        def update_ui():
            # 显示批量信息概览
            batch_info = f"批量处理结果概览:\n"
            batch_info += f"总文件数: {result['total_files']}\n"
            batch_info += f"成功处理: {result['total_processed']}\n\n"
            
            # 显示每个文件的简要结果
            for i, file_result in enumerate(result['results'], 1):
                extract_dir = file_result['processing_info']['extract_dir']
                filename = os.path.basename(extract_dir)
                batch_info += f"文件 {i}: {filename}\n"
                
                if file_result['extracted_data']:
                    batch_info += "  ✅ 信息提取成功\n"
                else:
                    batch_info += "  ❌ 信息提取失败\n"
                
                if file_result['mindmap_data']:
                    batch_info += "  ✅ 思维导图生成成功\n"
                else:
                    batch_info += "  ❌ 思维导图生成失败\n"
                
                batch_info += "\n"
            
            self.info_text.insert(1.0, batch_info)
            
            # 在思维导图标签页显示说明
            mindmap_info = "批量处理结果包含多个文件的思维导图。\n"
            mindmap_info += "请查看各个文件的结果目录获取详细的思维导图文件。\n\n"
            mindmap_info += f"批量报告目录: {result['batch_report_dir']}"
            self.mindmap_text.insert(1.0, mindmap_info)
        
        self.root.after(0, update_ui)
    
    def processing_finished(self):
        """处理完成后的UI重置"""
        self.processing = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')
        self.progress_var.set(100)
        self.update_status("处理完成")
    
    def stop_processing(self):
        """停止处理"""
        self.processing = False
        self.log_message("用户停止处理")
        self.processing_finished()
    
    def export_json(self):
        """导出JSON结果"""
        if not self.current_results:
            messagebox.showinfo("提示", "没有可导出的结果")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存JSON文件",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_results, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", f"结果已导出到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def export_mindmap(self):
        """导出思维导图"""
        if not self.current_results:
            messagebox.showinfo("提示", "没有可导出的思维导图")
            return
        
        # 检查是否有思维导图数据
        mermaid_code = None
        if isinstance(self.current_results, dict):
            mermaid_code = self.current_results.get('mermaid_code')
        
        if not mermaid_code:
            messagebox.showinfo("提示", "没有可导出的思维导图代码")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存思维导图文件",
            defaultextension=".mmd",
            filetypes=[("Mermaid files", "*.mmd"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(mermaid_code)
                messagebox.showinfo("成功", f"思维导图已导出到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def generate_report(self):
        """生成处理报告"""
        if not self.current_results:
            messagebox.showinfo("提示", "没有可生成报告的结果")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存处理报告",
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # 生成报告内容
                report_content = self.generate_report_content()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                messagebox.showinfo("成功", f"处理报告已生成: {file_path}")
                
                # 询问是否打开文件
                if messagebox.askyesno("打开文件", "是否打开生成的报告文件?"):
                    webbrowser.open(file_path)
                    
            except Exception as e:
                messagebox.showerror("错误", f"生成报告失败: {str(e)}")
    
    def generate_report_content(self):
        """生成报告内容"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# 文献处理Agent - 处理报告

**生成时间**: {timestamp}

## 处理概览

"""
        
        if isinstance(self.current_results, dict):
            if 'total_files' in self.current_results:
                # 批量处理结果
                report += f"- **处理模式**: 批量处理\n"
                report += f"- **总文件数**: {self.current_results['total_files']}\n"
                report += f"- **成功处理**: {self.current_results['total_processed']}\n"
                report += f"- **报告目录**: {self.current_results.get('batch_report_dir', 'N/A')}\n\n"
                
                report += "## 文件处理详情\n\n"
                for i, result in enumerate(self.current_results.get('results', []), 1):
                    extract_dir = result['processing_info']['extract_dir']
                    filename = os.path.basename(extract_dir)
                    
                    report += f"### {i}. {filename}\n\n"
                    report += f"- **状态**: {'✅ 成功' if result['extracted_data'] else '❌ 失败'}\n"
                    report += f"- **思维导图**: {'✅ 已生成' if result['mindmap_data'] else '❌ 生成失败'}\n"
                    
                    if result['extracted_data']:
                        report += f"- **提取信息**: 已成功提取结构化数据\n"
                    
                    report += "\n"
            else:
                # 单文件处理结果
                report += f"- **处理模式**: 单文件处理\n"
                report += f"- **结果目录**: {self.current_results.get('result_dir', 'N/A')}\n"
                report += f"- **信息提取**: {'✅ 成功' if self.current_results.get('extracted_info') else '❌ 失败'}\n"
                report += f"- **思维导图**: {'✅ 已生成' if self.current_results.get('mindmap_data') else '❌ 生成失败'}\n\n"
                
                if self.current_results.get('extracted_info'):
                    report += "## 提取信息概览\n\n"
                    report += "```json\n"
                    report += json.dumps(self.current_results['extracted_info'], ensure_ascii=False, indent=2)[:1000]
                    report += "\n...\n```\n\n"
                
                if self.current_results.get('mermaid_code'):
                    report += "## 思维导图\n\n"
                    report += "```mermaid\n"
                    report += self.current_results['mermaid_code']
                    report += "\n```\n\n"
        
        report += "## 使用说明\n\n"
        report += "本报告由文献处理Agent自动生成。如需查看详细结果，请访问相应的结果目录。\n\n"
        report += "---\n"
        report += "*由文献处理Agent生成*\n"
        
        return report
    
    def open_results_folder(self):
        """打开结果文件夹"""
        if not self.current_results:
            messagebox.showinfo("提示", "没有处理结果")
            return
        
        result_dir = None
        if isinstance(self.current_results, dict):
            result_dir = self.current_results.get('result_dir') or self.current_results.get('batch_report_dir')
        
        if result_dir and os.path.exists(result_dir):
            # 在文件管理器中打开目录
            if os.name == 'nt':  # Windows
                os.startfile(result_dir)
            elif os.name == 'posix':  # macOS and Linux
                os.system(f'xdg-open "{result_dir}"')
        else:
            messagebox.showinfo("提示", "结果目录不存在")
    
    def run(self):
        """运行GUI"""
        # 设置窗口图标（如果有的话）
        try:
            # self.root.iconbitmap("icon.ico")  # 如果有图标文件
            pass
        except:
            pass
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 运行主循环
        self.root.mainloop()
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.processing:
            if messagebox.askokcancel("退出", "正在处理文件，确定要退出吗？"):
                self.processing = False
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """主函数"""
    # 创建并运行GUI
    app = LiteratureAgentGUI()
    app.run()


if __name__ == "__main__":
    main()