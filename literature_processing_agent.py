#!/usr/bin/env python3
"""
全流程文献处理Agent
支持根据用户输入的需求，自动调用MinerU解析PDF，动态生成提示词提取信息，并生成思维导图

功能包括：
1. 调用MinerU API解析PDF文献
2. 根据用户需求动态生成提示词
3. 调用O3 API提取所需信息
4. 生成文献思维导图
5. 支持单个PDF和批量处理

作者: AI Assistant
日期: 2025年1月
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from openai import OpenAI

# 导入现有模块
from mineru_pdf_parser import MinerUParser
import full_structure_property_extraction as extractor
from config import Config

class LiteratureProcessingAgent:
    """全流程文献处理Agent"""
    
    def __init__(self, config_file="config.json"):
        """初始化Agent"""
        # 加载配置
        self.config = Config(config_file)
        
        # 检查必要的API密钥
        missing_keys = self.config.get_missing_keys()
        if missing_keys:
            print("⚠️  缺失API密钥配置:")
            for key in missing_keys:
                print(f"   - {key}")
            print("\n请运行以下命令进行配置:")
            print("   python config.py setup")
            print("或手动编辑 config.json 文件")
        
        self.mineru_parser = MinerUParser()
        
        # O3 API配置
        self.o3_api_key = self.config.get('o3_api_key')
        if not self.o3_api_key:
            raise ValueError("O3 API密钥未配置，请运行 'python config.py setup' 进行配置")
        
        self.o3_client = OpenAI(
            api_key=self.o3_api_key,
            base_url=self.config.get('o3_base_url', 'https://api.o3.fan/v1')
        )
        self.o3_model = self.config.get('o3_model', 'claude-sonnet-4-20250514')
        
        # 思维导图API配置（使用Whimsical或其他思维导图服务）
        self.mindmap_api_base = "https://whimsical.com/api/v1"
        
    def call_o3(self, prompt, temperature=0.2, retries=3):
        """调用O3 API"""
        for attempt in range(retries):
            try:
                response = self.o3_client.chat.completions.create(
                    model=self.o3_model,
                    messages=[
                        {"role": "system", "content": "You are a precise extractor for academic literature and an expert assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"[Retry {attempt+1}] O3 API call failed: {e}")
                if attempt < retries - 1:
                    time.sleep(5)
        return ""
    
    def generate_dynamic_prompts(self, user_requirements):
        """根据用户需求动态生成提示词"""
        prompt_generator = f"""
你是一个专业的提示词工程师，需要根据用户的需求生成用于文献信息提取的提示词。

用户需求：
{user_requirements}

请生成一个详细的JSON格式提示词模板，用于从学术文献中提取用户所需的信息。

要求：
1. 提示词应该清晰、具体、结构化
2. 返回的JSON结构应该包含用户关心的所有信息字段
3. 考虑不同类型的文献（研究论文、综述等）
4. 包含适当的数据验证和格式要求
5. 提示词应该指导AI提取准确、完整的信息

请生成一个完整的提示词模板，格式如下：
{{
  "extraction_prompt": "详细的提取指令...",
  "target_json_structure": {{
    // 目标JSON结构
  }},
  "validation_criteria": [
    "验证标准1",
    "验证标准2"
  ],
  "special_instructions": [
    "特殊指令1",
    "特殊指令2"
  ]
}}

只返回JSON格式的结果，不要其他解释。
"""
        
        response = self.call_o3(prompt_generator, temperature=0.3)
        
        try:
            # 清理响应，提取JSON
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].strip()
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"❌ 生成提示词失败: {e}")
            return None
    
    def extract_information_with_dynamic_prompt(self, content, dynamic_prompts, images=None):
        """使用动态生成的提示词提取信息"""
        if not dynamic_prompts:
            print("❌ 没有有效的提示词模板")
            return None
        
        extraction_prompt = dynamic_prompts.get("extraction_prompt", "")
        target_structure = dynamic_prompts.get("target_json_structure", {})
        
        # 构建完整的提取提示词
        full_prompt = f"""
{extraction_prompt}

目标JSON结构：
{json.dumps(target_structure, indent=2, ensure_ascii=False)}

文献内容：
\"\"\"{content}\"\"\"

请严格按照上述JSON结构提取信息。如果某个字段在文献中没有提及，请使用"N/A"作为值。
只返回JSON格式的结果，不要其他解释。
"""
        
        # 调用O3 API进行信息提取
        if images:
            # 如果有图片，使用图片增强的提取
            return self.extract_with_images(full_prompt, images)
        else:
            # 纯文本提取
            raw = self.call_o3(full_prompt)
            
            # 清理响应
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].strip()
            
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                print("❌ 解析提取结果失败")
                return None
    
    def extract_with_images(self, prompt, image_paths):
        """结合图片进行信息提取"""
        # 编码图片（限制数量）
        selected_images = image_paths[:5]  # 最多5张图片
        image_base64_list = []
        
        for img_path in selected_images:
            base64_data = extractor.encode_image_to_base64(img_path)
            if base64_data:
                image_base64_list.append(base64_data)
        
        if not image_base64_list:
            return self.call_o3(prompt)
        
        try:
            messages = [
                {"role": "system", "content": "You are a precise extractor for academic literature with image analysis capabilities."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt}
                ] + [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
                    }
                    for img_base64 in image_base64_list
                ]}
            ]
            
            response = self.o3_client.chat.completions.create(
                model=self.o3_model,
                messages=messages,
                temperature=0.2
            )
            
            raw = response.choices[0].message.content
            
            # 清理响应
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].strip()
            
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                print("❌ 解析图片增强提取结果失败")
                return None
                
        except Exception as e:
            print(f"❌ 图片增强提取失败: {e}")
            return None
    
    def generate_mindmap(self, literature_data, title="文献思维导图"):
        """生成文献思维导图"""
        # 准备思维导图数据
        mindmap_prompt = f"""
基于以下文献提取的信息，生成一个结构化的思维导图数据：

文献数据：
{json.dumps(literature_data, indent=2, ensure_ascii=False)}

请生成一个思维导图的JSON结构，包含以下要素：
1. 中心主题（文献标题或主要研究内容）
2. 主要分支（研究方法、关键发现、应用等）
3. 子分支（具体细节）
4. 颜色和样式建议

输出格式：
{{
  "central_topic": "中心主题",
  "branches": [
    {{
      "name": "分支名称",
      "color": "#颜色代码",
      "children": [
        {{
          "name": "子分支名称",
          "details": ["详细信息1", "详细信息2"]
        }}
      ]
    }}
  ],
  "summary": "思维导图总结"
}}

只返回JSON格式的结果。
"""
        
        mindmap_data = self.call_o3(mindmap_prompt, temperature=0.3)
        
        try:
            if "```json" in mindmap_data:
                mindmap_data = mindmap_data.split("```json")[1].split("```")[0].strip()
            elif "```" in mindmap_data:
                mindmap_data = mindmap_data.split("```")[1].strip()
            
            mindmap_json = json.loads(mindmap_data)
            
            # 生成思维导图的可视化代码（使用Mermaid格式）
            mermaid_code = self.convert_to_mermaid(mindmap_json)
            
            return {
                "mindmap_data": mindmap_json,
                "mermaid_code": mermaid_code
            }
            
        except json.JSONDecodeError as e:
            print(f"❌ 生成思维导图失败: {e}")
            return None
    
    def convert_to_mermaid(self, mindmap_data):
        """将思维导图数据转换为Mermaid格式"""
        mermaid_lines = ["mindmap"]
        mermaid_lines.append(f"  root(({mindmap_data.get('central_topic', '文献分析')}))")
        
        for i, branch in enumerate(mindmap_data.get('branches', [])):
            branch_name = branch.get('name', f'分支{i+1}')
            mermaid_lines.append(f"    {branch_name}")
            
            for j, child in enumerate(branch.get('children', [])):
                child_name = child.get('name', f'子分支{j+1}')
                mermaid_lines.append(f"      {child_name}")
                
                for detail in child.get('details', []):
                    if len(detail) < 20:  # 只显示短的详细信息
                        mermaid_lines.append(f"        {detail}")
        
        return "\n".join(mermaid_lines)
    
    def process_single_pdf(self, pdf_path, user_requirements, output_dir="processed_results"):
        """处理单个PDF文件的完整流程"""
        print(f"🚀 开始处理PDF文件: {os.path.basename(pdf_path)}")
        print("=" * 80)
        
        # 步骤1: 使用MinerU解析PDF
        print("📄 步骤1: 解析PDF文件...")
        parsed_result = self.mineru_parser.parse_single_pdf(pdf_path)
        
        if not parsed_result:
            print("❌ PDF解析失败")
            return None
        
        # 下载解析结果
        print("📥 下载解析结果...")
        extract_dir = self.mineru_parser.download_result(parsed_result, output_dir)
        
        if not extract_dir:
            print("❌ 下载解析结果失败")
            return None
        
        # 步骤2: 根据用户需求生成提示词
        print("\n🧠 步骤2: 根据需求生成提取提示词...")
        dynamic_prompts = self.generate_dynamic_prompts(user_requirements)
        
        if not dynamic_prompts:
            print("❌ 生成提示词失败")
            return None
        
        print("✅ 提示词生成成功")
        
        # 步骤3: 读取解析后的内容
        print("\n📖 步骤3: 读取文档内容...")
        md_file = os.path.join(extract_dir, "full.md")
        
        if not os.path.exists(md_file):
            print("❌ 找不到解析后的markdown文件")
            return None
        
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 查找图片
        images_dir = os.path.join(extract_dir, "images")
        image_paths = []
        if os.path.exists(images_dir):
            for img_file in os.listdir(images_dir):
                if img_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_paths.append(os.path.join(images_dir, img_file))
        
        print(f"📄 文档长度: {len(content)} 字符")
        print(f"🖼️ 找到图片: {len(image_paths)} 张")
        
        # 步骤4: 提取信息
        print("\n🔍 步骤4: 提取文献信息...")
        extracted_info = self.extract_information_with_dynamic_prompt(
            content, dynamic_prompts, image_paths
        )
        
        if not extracted_info:
            print("❌ 信息提取失败")
            return None
        
        print("✅ 信息提取成功")
        
        # 步骤5: 生成思维导图
        print("\n🧠 步骤5: 生成思维导图...")
        mindmap_result = self.generate_mindmap(extracted_info, os.path.basename(pdf_path))
        
        if not mindmap_result:
            print("❌ 思维导图生成失败")
            mindmap_result = {"mindmap_data": None, "mermaid_code": None}
        else:
            print("✅ 思维导图生成成功")
        
        # 步骤6: 保存结果
        print("\n💾 步骤6: 保存处理结果...")
        
        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(c for c in os.path.basename(pdf_path) if c.isalnum() or c in (' ', '-', '_', '.')).strip()
        result_dir = os.path.join(output_dir, f"{safe_filename}_{timestamp}")
        os.makedirs(result_dir, exist_ok=True)
        
        # 保存提取的信息
        info_file = os.path.join(result_dir, "extracted_information.json")
        with open(info_file, "w", encoding="utf-8") as f:
            json.dump({
                "processing_info": {
                    "pdf_file": pdf_path,
                    "user_requirements": user_requirements,
                    "processing_time": datetime.now().isoformat(),
                    "dynamic_prompts": dynamic_prompts
                },
                "extracted_data": extracted_info
            }, f, ensure_ascii=False, indent=2)
        
        # 保存思维导图
        if mindmap_result["mindmap_data"]:
            mindmap_file = os.path.join(result_dir, "mindmap.json")
            with open(mindmap_file, "w", encoding="utf-8") as f:
                json.dump(mindmap_result["mindmap_data"], f, ensure_ascii=False, indent=2)
        
        if mindmap_result["mermaid_code"]:
            mermaid_file = os.path.join(result_dir, "mindmap.mmd")
            with open(mermaid_file, "w", encoding="utf-8") as f:
                f.write(mindmap_result["mermaid_code"])
        
        # 创建处理报告
        report_file = os.path.join(result_dir, "processing_report.md")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"""# 文献处理报告

## 基本信息
- **PDF文件**: {os.path.basename(pdf_path)}
- **处理时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **用户需求**: {user_requirements}

## 处理结果
- **原始PDF解析**: {'✅' if parsed_result else '❌'}
- **信息提取**: {'✅' if extracted_info else '❌'}
- **思维导图生成**: {'✅' if mindmap_result["mindmap_data"] else '❌'}

## 输出文件
- `extracted_information.json`: 提取的结构化信息
- `mindmap.json`: 思维导图数据
- `mindmap.mmd`: Mermaid格式思维导图代码

## 提取到的信息概览
{json.dumps(extracted_info, ensure_ascii=False, indent=2)[:500]}...

## 思维导图预览
```mermaid
{mindmap_result["mermaid_code"] or "思维导图生成失败"}
```
""")
        
        print(f"✅ 处理完成! 结果保存在: {result_dir}")
        
        return {
            "result_dir": result_dir,
            "extracted_info": extracted_info,
            "mindmap_data": mindmap_result["mindmap_data"],
            "mermaid_code": mindmap_result["mermaid_code"],
            "dynamic_prompts": dynamic_prompts
        }
    
    def process_batch_pdfs(self, pdf_files, user_requirements, output_dir="batch_processed_results"):
        """批量处理PDF文件"""
        print(f"🚀 开始批量处理 {len(pdf_files)} 个PDF文件")
        print("=" * 80)
        
        # 步骤1: 批量解析PDF
        print("📄 步骤1: 批量解析PDF文件...")
        parsed_results = self.mineru_parser.parse_batch_pdfs(pdf_files)
        
        if not parsed_results:
            print("❌ 批量PDF解析失败")
            return None
        
        # 下载批量解析结果
        print("📥 下载批量解析结果...")
        downloaded_dirs = self.mineru_parser.download_batch_results(parsed_results, output_dir)
        
        if not downloaded_dirs:
            print("❌ 下载批量解析结果失败")
            return None
        
        # 步骤2: 根据用户需求生成提示词（只生成一次）
        print("\n🧠 步骤2: 根据需求生成提取提示词...")
        dynamic_prompts = self.generate_dynamic_prompts(user_requirements)
        
        if not dynamic_prompts:
            print("❌ 生成提示词失败")
            return None
        
        print("✅ 提示词生成成功")
        
        # 步骤3: 处理每个解析后的文件
        all_results = []
        
        for i, extract_dir in enumerate(downloaded_dirs, 1):
            print(f"\n📖 处理文件 {i}/{len(downloaded_dirs)}: {os.path.basename(extract_dir)}")
            
            try:
                # 读取内容
                md_file = os.path.join(extract_dir, "full.md")
                if not os.path.exists(md_file):
                    print(f"⚠️ 跳过: 找不到markdown文件")
                    continue
                
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 查找图片
                images_dir = os.path.join(extract_dir, "images")
                image_paths = []
                if os.path.exists(images_dir):
                    for img_file in os.listdir(images_dir):
                        if img_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                            image_paths.append(os.path.join(images_dir, img_file))
                
                # 提取信息
                print(f"  🔍 提取信息...")
                extracted_info = self.extract_information_with_dynamic_prompt(
                    content, dynamic_prompts, image_paths
                )
                
                if not extracted_info:
                    print(f"  ❌ 信息提取失败")
                    continue
                
                # 生成思维导图
                print(f"  🧠 生成思维导图...")
                mindmap_result = self.generate_mindmap(extracted_info, os.path.basename(extract_dir))
                
                # 保存单个文件的结果
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                result_file = os.path.join(extract_dir, f"processing_result_{timestamp}.json")
                
                result_data = {
                    "processing_info": {
                        "extract_dir": extract_dir,
                        "user_requirements": user_requirements,
                        "processing_time": datetime.now().isoformat(),
                        "batch_index": i,
                        "dynamic_prompts": dynamic_prompts
                    },
                    "extracted_data": extracted_info,
                    "mindmap_data": mindmap_result["mindmap_data"] if mindmap_result else None,
                    "mermaid_code": mindmap_result["mermaid_code"] if mindmap_result else None
                }
                
                with open(result_file, "w", encoding="utf-8") as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                
                all_results.append(result_data)
                print(f"  ✅ 处理完成")
                
                # 每处理5个文件休息一下
                if i % 5 == 0:
                    print(f"  ⏸️ 已处理 {i} 个文件，休息片刻...")
                    time.sleep(10)
                    
            except Exception as e:
                print(f"  ❌ 处理文件时出错: {e}")
                continue
        
        # 步骤4: 生成批量处理报告
        print(f"\n📊 生成批量处理报告...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_report_dir = os.path.join(output_dir, f"batch_report_{timestamp}")
        os.makedirs(batch_report_dir, exist_ok=True)
        
        # 保存批量结果
        batch_results_file = os.path.join(batch_report_dir, "batch_results.json")
        with open(batch_results_file, "w", encoding="utf-8") as f:
            json.dump({
                "batch_info": {
                    "total_files": len(pdf_files),
                    "successfully_processed": len(all_results),
                    "user_requirements": user_requirements,
                    "processing_time": datetime.now().isoformat(),
                    "dynamic_prompts": dynamic_prompts
                },
                "results": all_results
            }, f, ensure_ascii=False, indent=2)
        
        # 生成批量报告
        report_file = os.path.join(batch_report_dir, "batch_report.md")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"""# 批量文献处理报告

## 基本信息
- **处理时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **用户需求**: {user_requirements}
- **总文件数**: {len(pdf_files)}
- **成功处理**: {len(all_results)}

## 处理结果概览
""")
            
            for i, result in enumerate(all_results, 1):
                extract_dir = result["processing_info"]["extract_dir"]
                f.write(f"\n### {i}. {os.path.basename(extract_dir)}\n")
                f.write(f"- **状态**: {'✅' if result['extracted_data'] else '❌'}\n")
                f.write(f"- **思维导图**: {'✅' if result['mindmap_data'] else '❌'}\n")
                
                # 简要展示提取的信息
                if result['extracted_data']:
                    data_str = json.dumps(result['extracted_data'], ensure_ascii=False, indent=2)
                    f.write(f"- **提取信息预览**: {data_str[:200]}...\n")
        
        print(f"✅ 批量处理完成! 处理了 {len(all_results)}/{len(pdf_files)} 个文件")
        print(f"📊 批量报告保存在: {batch_report_dir}")
        
        return {
            "batch_report_dir": batch_report_dir,
            "total_processed": len(all_results),
            "total_files": len(pdf_files),
            "results": all_results,
            "dynamic_prompts": dynamic_prompts
        }


def main():
    """主函数 - 命令行界面"""
    import argparse
    
    parser = argparse.ArgumentParser(description="全流程文献处理Agent")
    parser.add_argument("mode", choices=["single", "batch"], help="处理模式")
    parser.add_argument("--pdf", help="单个PDF文件路径")
    parser.add_argument("--dir", help="包含PDF文件的目录（批量处理）")
    parser.add_argument("--requirements", help="用户需求描述")
    parser.add_argument("--output", default="agent_results", help="输出目录")
    
    args = parser.parse_args()
    
    # 初始化Agent
    agent = LiteratureProcessingAgent()
    
    # 获取用户需求
    requirements = args.requirements
    if not requirements:
        print("请描述您想从文献中提取的信息：")
        requirements = input("> ")
    
    if args.mode == "single":
        # 单个文件处理
        pdf_file = args.pdf
        if not pdf_file:
            # 查找当前目录的PDF文件
            pdf_files = list(Path('.').glob('*.pdf'))
            if not pdf_files:
                print("❌ 未找到PDF文件")
                return
            elif len(pdf_files) == 1:
                pdf_file = str(pdf_files[0])
            else:
                print("发现多个PDF文件，请选择：")
                for i, pdf in enumerate(pdf_files, 1):
                    print(f"  {i}. {pdf.name}")
                try:
                    choice = int(input("请选择 (1-{}): ".format(len(pdf_files)))) - 1
                    pdf_file = str(pdf_files[choice])
                except (ValueError, IndexError):
                    print("❌ 无效选择")
                    return
        
        # 处理单个PDF
        result = agent.process_single_pdf(pdf_file, requirements, args.output)
        
        if result:
            print(f"\n🎉 处理成功!")
            print(f"📁 结果目录: {result['result_dir']}")
        else:
            print("\n❌ 处理失败")
    
    elif args.mode == "batch":
        # 批量处理
        pdf_dir = args.dir or "."
        pdf_files = list(Path(pdf_dir).glob('*.pdf'))
        
        if not pdf_files:
            print(f"❌ 在 {pdf_dir} 目录中未找到PDF文件")
            return
        
        print(f"发现 {len(pdf_files)} 个PDF文件")
        confirm = input("确认批量处理? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ 用户取消")
            return
        
        # 批量处理
        result = agent.process_batch_pdfs([str(f) for f in pdf_files], requirements, args.output)
        
        if result:
            print(f"\n🎉 批量处理成功!")
            print(f"📁 报告目录: {result['batch_report_dir']}")
            print(f"📊 成功处理: {result['total_processed']}/{result['total_files']} 个文件")
        else:
            print("\n❌ 批量处理失败")


if __name__ == "__main__":
    main()