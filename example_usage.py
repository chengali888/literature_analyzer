#!/usr/bin/env python3
"""
文献处理Agent使用示例
展示如何通过代码直接调用Agent功能

作者: AI Assistant  
日期: 2025年1月
"""

import os
import json
from pathlib import Path
from literature_processing_agent import LiteratureProcessingAgent

def example_single_file():
    """示例1: 处理单个PDF文件"""
    print("🔬 示例1: 单文件处理")
    print("=" * 50)
    
    # 初始化Agent
    agent = LiteratureProcessingAgent()
    
    # 查找PDF文件
    pdf_files = list(Path('.').glob('*.pdf'))
    if not pdf_files:
        print("❌ 当前目录没有PDF文件，请添加PDF文件后重试")
        return
    
    pdf_file = str(pdf_files[0])
    print(f"📄 处理文件: {pdf_file}")
    
    # 定义提取需求
    requirements = """
    请从这篇文献中提取以下信息：
    1. 研究的主要目标和方法
    2. 关键实验结果和数据  
    3. 使用的材料和设备
    4. 主要结论和发现
    5. 实际应用价值
    """
    
    print(f"🎯 提取需求: {requirements.strip()}")
    
    # 执行处理
    try:
        result = agent.process_single_pdf(pdf_file, requirements)
        
        if result:
            print("\n✅ 处理成功!")
            print(f"📁 结果目录: {result['result_dir']}")
            
            # 显示提取信息的简要概览
            if result['extracted_info']:
                print("\n📊 提取信息概览:")
                info_str = json.dumps(result['extracted_info'], ensure_ascii=False, indent=2)
                print(info_str[:300] + "..." if len(info_str) > 300 else info_str)
            
            # 显示思维导图信息
            if result['mindmap_data']:
                print(f"\n🧠 思维导图: 已生成")
                print(f"   中心主题: {result['mindmap_data'].get('central_topic', 'N/A')}")
                print(f"   分支数量: {len(result['mindmap_data'].get('branches', []))}")
            
            return result
        else:
            print("❌ 处理失败")
            return None
            
    except Exception as e:
        print(f"❌ 处理出错: {e}")
        return None

def example_batch_files():
    """示例2: 批量处理PDF文件"""
    print("\n🔬 示例2: 批量处理")
    print("=" * 50)
    
    # 初始化Agent
    agent = LiteratureProcessingAgent()
    
    # 查找PDF文件
    pdf_files = list(Path('.').glob('*.pdf'))
    if len(pdf_files) < 2:
        print("❌ 需要至少2个PDF文件进行批量处理演示")
        return
    
    # 取前3个文件进行演示
    demo_files = [str(f) for f in pdf_files[:3]]
    print(f"📄 处理文件: {len(demo_files)} 个")
    for i, f in enumerate(demo_files, 1):
        print(f"   {i}. {os.path.basename(f)}")
    
    # 定义批量提取需求
    requirements = """
    对每篇文献提取以下标准化信息：
    1. 文献基本信息（标题、作者、期刊）
    2. 研究领域和关键词
    3. 主要研究方法和技术
    4. 核心发现和创新点
    5. 数据和实验结果
    """
    
    print(f"🎯 批量提取需求: {requirements.strip()}")
    
    # 执行批量处理
    try:
        result = agent.process_batch_pdfs(demo_files, requirements)
        
        if result:
            print("\n✅ 批量处理成功!")
            print(f"📊 成功处理: {result['total_processed']}/{result['total_files']} 个文件")
            print(f"📁 报告目录: {result['batch_report_dir']}")
            
            # 显示每个文件的处理结果
            print("\n📋 处理结果概览:")
            for i, file_result in enumerate(result['results'], 1):
                extract_dir = file_result['processing_info']['extract_dir']
                filename = os.path.basename(extract_dir)
                status = "✅" if file_result['extracted_data'] else "❌"
                mindmap_status = "✅" if file_result['mindmap_data'] else "❌"
                print(f"   {i}. {filename}: 信息提取{status} | 思维导图{mindmap_status}")
            
            return result
        else:
            print("❌ 批量处理失败")
            return None
            
    except Exception as e:
        print(f"❌ 批量处理出错: {e}")
        return None

def example_custom_requirements():
    """示例3: 自定义提取需求"""
    print("\n🔬 示例3: 自定义材料科学提取")
    print("=" * 50)
    
    # 初始化Agent
    agent = LiteratureProcessingAgent()
    
    # 查找PDF文件
    pdf_files = list(Path('.').glob('*.pdf'))
    if not pdf_files:
        print("❌ 当前目录没有PDF文件")
        return
    
    pdf_file = str(pdf_files[0])
    print(f"📄 处理文件: {pdf_file}")
    
    # 材料科学专用提取需求
    materials_requirements = """
    从这篇材料科学文献中提取以下专业信息：
    
    材料信息：
    - 材料名称和化学式
    - 晶体结构和空间群
    - 合成方法和条件
    - 物理化学性质
    
    性能数据：
    - 机械性能（强度、硬度、模量等）
    - 电学性能（电导率、介电常数等）
    - 热学性能（热导率、热膨胀系数等）
    - 光学性能（折射率、透光率等）
    
    实验信息：
    - 表征方法（XRD、SEM、TEM等）
    - 测试条件和参数
    - 实验数据和图表
    
    应用信息：
    - 应用领域和场景
    - 性能优势和局限性
    - 未来发展方向
    
    请以结构化JSON格式输出，包含数值、单位和测试条件。
    """
    
    print(f"🎯 材料科学专用提取需求")
    
    # 执行处理
    try:
        result = agent.process_single_pdf(pdf_file, materials_requirements)
        
        if result:
            print("\n✅ 材料科学信息提取成功!")
            print(f"📁 结果目录: {result['result_dir']}")
            
            # 保存专用提取结果
            if result['extracted_info']:
                materials_file = os.path.join(result['result_dir'], "materials_data.json")
                with open(materials_file, 'w', encoding='utf-8') as f:
                    json.dump(result['extracted_info'], f, ensure_ascii=False, indent=2)
                print(f"💾 材料数据已保存: {materials_file}")
            
            return result
        else:
            print("❌ 材料科学信息提取失败")
            return None
            
    except Exception as e:
        print(f"❌ 处理出错: {e}")
        return None

def example_analyze_results(result):
    """示例4: 分析处理结果"""
    if not result:
        print("❌ 没有结果可分析")
        return
    
    print("\n🔬 示例4: 结果分析")
    print("=" * 50)
    
    # 分析提取信息的完整性
    if result.get('extracted_info'):
        extracted_data = result['extracted_info']
        
        # 统计非空字段
        def count_non_empty_fields(data, prefix=""):
            count = 0
            total = 0
            
            if isinstance(data, dict):
                for key, value in data.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    
                    if isinstance(value, (dict, list)):
                        sub_count, sub_total = count_non_empty_fields(value, full_key)
                        count += sub_count
                        total += sub_total
                    else:
                        total += 1
                        if value and value != "N/A" and value != "":
                            count += 1
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    sub_count, sub_total = count_non_empty_fields(item, f"{prefix}[{i}]")
                    count += sub_count
                    total += sub_total
            
            return count, total
        
        filled_fields, total_fields = count_non_empty_fields(extracted_data)
        completion_rate = filled_fields / total_fields * 100 if total_fields > 0 else 0
        
        print(f"📊 信息提取分析:")
        print(f"   已填充字段: {filled_fields}")
        print(f"   总字段数: {total_fields}")
        print(f"   完整度: {completion_rate:.1f}%")
        
        # 检查关键字段
        key_fields = ['title', 'authors', 'abstract', 'keywords', 'conclusions']
        found_keys = []
        for key in key_fields:
            if key in str(extracted_data).lower():
                found_keys.append(key)
        
        print(f"   关键字段: {len(found_keys)}/{len(key_fields)} 找到")
    
    # 分析思维导图
    if result.get('mindmap_data'):
        mindmap = result['mindmap_data']
        print(f"\n🧠 思维导图分析:")
        print(f"   中心主题: {mindmap.get('central_topic', 'N/A')}")
        
        branches = mindmap.get('branches', [])
        print(f"   主分支数: {len(branches)}")
        
        total_nodes = 0
        for branch in branches:
            children = branch.get('children', [])
            total_nodes += len(children)
        
        print(f"   总节点数: {total_nodes}")
        print(f"   平均深度: {total_nodes/len(branches):.1f}" if branches else "   平均深度: 0")
    
    # 文件大小分析
    if result.get('result_dir'):
        result_dir = result['result_dir']
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(result_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
                    file_count += 1
        
        print(f"\n📁 输出文件分析:")
        print(f"   文件数量: {file_count}")
        print(f"   总大小: {total_size/1024:.1f} KB")

def main():
    """主函数 - 运行所有示例"""
    print("🚀 文献处理Agent使用示例")
    print("=" * 80)
    
    # 检查是否有PDF文件
    pdf_files = list(Path('.').glob('*.pdf'))
    if not pdf_files:
        print("❌ 当前目录没有PDF文件")
        print("请添加PDF文件到当前目录后重新运行示例")
        return
    
    print(f"📄 发现 {len(pdf_files)} 个PDF文件")
    for i, pdf in enumerate(pdf_files, 1):
        size = os.path.getsize(pdf) / (1024*1024)
        print(f"   {i}. {pdf.name} ({size:.1f} MB)")
    
    # 选择运行的示例
    print("\n请选择要运行的示例:")
    print("1. 单文件处理示例")
    print("2. 批量处理示例")
    print("3. 自定义材料科学提取")
    print("4. 运行所有示例")
    
    try:
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            result = example_single_file()
            example_analyze_results(result)
        elif choice == "2":
            example_batch_files()
        elif choice == "3":
            result = example_custom_requirements()
            example_analyze_results(result)
        elif choice == "4":
            print("\n🔄 运行所有示例...")
            result1 = example_single_file()
            if result1:
                example_analyze_results(result1)
            
            if len(pdf_files) >= 2:
                example_batch_files()
            
            result3 = example_custom_requirements()
            if result3:
                example_analyze_results(result3)
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n👋 用户取消")
    except Exception as e:
        print(f"❌ 示例运行出错: {e}")

if __name__ == "__main__":
    main()