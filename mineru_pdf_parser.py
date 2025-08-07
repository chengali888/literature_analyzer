#!/usr/bin/env python3
"""
MinerU PDF解析工具
支持单个PDF文件和批量PDF文件解析
严格按照MinerU API文档实现

使用方法:
1. 单个PDF解析: python mineru_pdf_parser.py single
2. 批量PDF解析: python mineru_pdf_parser.py batch
3. 自动模式: python mineru_pdf_parser.py (自动检测当前目录PDF文件)

作者: AI Assistant
日期: 2025年1月
"""

import requests
import json
import time
import os
import zipfile
import sys
from pathlib import Path

# API配置
API_TOKEN = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI5MTkwNDMwNSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc1NDMwNzc1MiwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiMTg1NDk5ODg3MjMiLCJvcGVuSWQiOm51bGwsInV1aWQiOiI0YTgwYTA5Yy03MWE0LTQwZjktODA3Yy00NWJmYjliYmViZDEiLCJlbWFpbCI6IiIsImV4cCI6MTc1NTUxNzM1Mn0.7Ls_xzWyTPhOEQwZIRDVasbZxwjoTxfWxJVhIDLlQvqVfLySXp6R7yY1elAxHbxUUtdWioyYAP2Rck0R69MOmA"
BASE_URL = "https://mineru.net/api/v4"

class MinerUParser:
    """MinerU PDF解析器"""
    
    def __init__(self, api_token=API_TOKEN):
        self.api_token = api_token
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_token}'
        }
    
    def upload_file_with_retry(self, file_path, upload_url, max_retries=3):
        """带重试机制的文件上传"""
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        print(f"📄 文件: {filename}")
        print(f"📊 大小: {file_size / (1024*1024):.2f} MB")
        
        for attempt in range(max_retries):
            print(f"🔄 尝试上传 (第{attempt + 1}/{max_retries}次)...")
            
            try:
                with open(file_path, 'rb') as f:
                    response = requests.put(
                        upload_url,
                        data=f,
                        timeout=(30, 300)  # 连接30秒，读取300秒
                    )
                
                if response.status_code == 200:
                    print(f"✅ {filename} 上传成功!")
                    return True
                else:
                    print(f"❌ 上传失败 - 状态码: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"⏱️ 上传超时 (尝试 {attempt + 1})")
            except Exception as e:
                print(f"❌ 上传错误: {e}")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                print(f"⏳ 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        print(f"❌ {filename} 上传失败")
        return False
    
    def parse_single_pdf(self, pdf_file):
        """解析单个PDF文件"""
        if not os.path.exists(pdf_file):
            print(f"❌ 文件不存在: {pdf_file}")
            return None
        
        file_size = os.path.getsize(pdf_file)
        if file_size > 200 * 1024 * 1024:  # 200MB限制
            print(f"❌ 文件大小 {file_size/(1024*1024):.1f}MB 超过200MB限制")
            return None
        
        print(f"🚀 开始解析单个PDF文件")
        print("=" * 60)
        
        # 步骤1: 申请上传链接
        print("步骤1: 申请上传链接")
        url = f'{BASE_URL}/file-urls/batch'
        
        data = {
            "enable_formula": True,
            "language": "ch",
            "enable_table": True,
            "model_version": "v2",
            "files": [{
                "name": os.path.basename(pdf_file),
                "is_ocr": True,
                "data_id": f"single_{int(time.time())}"
            }]
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code != 200 or response.json()["code"] != 0:
                print(f"❌ 申请上传链接失败")
                return None
            
            result = response.json()
            batch_id = result["data"]["batch_id"]
            upload_url = result["data"]["file_urls"][0]
            
            print(f"✅ 获取上传链接成功")
            print(f"📋 批次ID: {batch_id}")
            
        except Exception as e:
            print(f"❌ 申请上传链接出错: {e}")
            return None
        
        # 步骤2: 上传文件
        print("\n步骤2: 上传文件")
        if not self.upload_file_with_retry(pdf_file, upload_url):
            return None
        
        # 步骤3: 等待解析
        print("\n步骤3: 等待解析完成")
        return self.wait_for_result(batch_id)
    
    def parse_batch_pdfs(self, pdf_files):
        """批量解析PDF文件"""
        valid_files = []
        for pdf_file in pdf_files:
            if os.path.exists(pdf_file):
                file_size = os.path.getsize(pdf_file)
                if file_size <= 200 * 1024 * 1024:  # 200MB限制
                    valid_files.append(pdf_file)
                else:
                    print(f"⚠️ 跳过大文件: {pdf_file} ({file_size/(1024*1024):.1f}MB)")
            else:
                print(f"⚠️ 文件不存在: {pdf_file}")
        
        if not valid_files:
            print("❌ 没有有效的PDF文件可以处理")
            return None
        
        print(f"🚀 开始批量解析 {len(valid_files)} 个PDF文件")
        print("=" * 60)
        
        # 步骤1: 申请批量上传链接
        print("步骤1: 申请批量上传链接")
        url = f'{BASE_URL}/file-urls/batch'
        
        files_data = []
        for i, pdf_file in enumerate(valid_files):
            files_data.append({
                "name": os.path.basename(pdf_file),
                "is_ocr": True,
                "data_id": f"batch_{i}_{int(time.time())}"
            })
        
        data = {
            "enable_formula": True,
            "language": "ch",
            "enable_table": True,
            "model_version": "v2",
            "files": files_data
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code != 200 or response.json()["code"] != 0:
                print(f"❌ 申请批量上传链接失败")
                return None
            
            result = response.json()
            batch_id = result["data"]["batch_id"]
            upload_urls = result["data"]["file_urls"]
            
            print(f"✅ 获取批量上传链接成功")
            print(f"📋 批次ID: {batch_id}")
            
        except Exception as e:
            print(f"❌ 申请批量上传链接出错: {e}")
            return None
        
        # 步骤2: 批量上传文件
        print("\n步骤2: 批量上传文件")
        upload_success = 0
        for pdf_file, upload_url in zip(valid_files, upload_urls):
            if self.upload_file_with_retry(pdf_file, upload_url):
                upload_success += 1
            print()  # 空行分隔
        
        print(f"📊 上传结果: {upload_success}/{len(valid_files)} 个文件上传成功")
        
        if upload_success == 0:
            print("❌ 没有文件上传成功")
            return None
        
        # 步骤3: 等待批量解析
        print("\n步骤3: 等待批量解析完成")
        return self.wait_for_batch_result(batch_id)
    
    def wait_for_result(self, batch_id, max_wait=2400):
        """等待单个文件解析结果"""
        url = f'{BASE_URL}/extract-results/batch/{batch_id}'
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if result['code'] == 0:
                        extract_results = result['data']['extract_result']
                        if extract_results:
                            file_result = extract_results[0]
                            state = file_result['state']
                            
                            elapsed = int(time.time() - start_time)
                            
                            if state == 'done':
                                print(f"[{elapsed}s] 🎉 解析完成!")
                                return file_result
                            elif state == 'failed':
                                error_msg = file_result.get('err_msg', '未知错误')
                                print(f"[{elapsed}s] ❌ 解析失败: {error_msg}")
                                return None
                            elif state == 'running':
                                progress = file_result.get('extract_progress', {})
                                if progress:
                                    extracted = progress.get('extracted_pages', 0)
                                    total = progress.get('total_pages', 0)
                                    print(f"[{elapsed}s] 📊 解析进度: {extracted}/{total} 页")
                                else:
                                    print(f"[{elapsed}s] 🔄 正在解析...")
                            else:
                                print(f"[{elapsed}s] ⏳ 状态: {state}")
                
            except Exception as e:
                elapsed = int(time.time() - start_time)
                print(f"[{elapsed}s] ❌ 查询出错: {e}")
            
            time.sleep(10)
        
        print("❌ 等待超时")
        return None
    
    def wait_for_batch_result(self, batch_id, max_wait=3600):
        """等待批量解析结果"""
        url = f'{BASE_URL}/extract-results/batch/{batch_id}'
        start_time = time.time()
        
        print(f"📋 批次ID: {batch_id}")
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if result['code'] == 0:
                        extract_results = result['data']['extract_result']
                        if extract_results:
                            elapsed = int(time.time() - start_time)
                            
                            # 检查所有文件状态
                            all_done = True
                            done_count = 0
                            failed_count = 0
                            
                            for file_result in extract_results:
                                state = file_result['state']
                                if state == 'done':
                                    done_count += 1
                                elif state == 'failed':
                                    failed_count += 1
                                elif state not in ['done', 'failed']:
                                    all_done = False
                            
                            total_files = len(extract_results)
                            print(f"[{elapsed}s] 📊 进度: {done_count}✅ {failed_count}❌ / {total_files} 文件")
                            
                            if all_done:
                                print(f"[{elapsed}s] 🎉 批量解析完成!")
                                return extract_results
                
            except Exception as e:
                elapsed = int(time.time() - start_time)
                print(f"[{elapsed}s] ❌ 查询出错: {e}")
            
            time.sleep(15)
        
        print("❌ 批量等待超时")
        return None
    
    def download_result(self, result_data, output_dir="parsed_results"):
        """下载单个解析结果"""
        if 'full_zip_url' not in result_data:
            print("❌ 没有找到下载链接")
            return None
        
        zip_url = result_data['full_zip_url']
        filename = result_data.get('file_name', 'result')
        
        print(f"📥 下载解析结果: {filename}")
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # 下载ZIP
            response = requests.get(zip_url, timeout=300, stream=True)
            if response.status_code != 200:
                print(f"❌ 下载失败: {response.status_code}")
                return None
            
            # 保存和解压
            timestamp = int(time.time())
            safe_name = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
            extract_dir = os.path.join(output_dir, f"{safe_name}_{timestamp}")
            os.makedirs(extract_dir, exist_ok=True)
            
            zip_path = os.path.join(output_dir, f"temp_{timestamp}.zip")
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # 解压
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            os.remove(zip_path)  # 删除临时ZIP文件
            
            print(f"✅ 结果已保存到: {extract_dir}")
            self.show_result_summary(extract_dir)
            
            return extract_dir
            
        except Exception as e:
            print(f"❌ 下载处理出错: {e}")
            return None
    
    def download_batch_results(self, results_list, output_dir="batch_parsed_results"):
        """下载批量解析结果"""
        if not results_list:
            print("❌ 没有解析结果")
            return []
        
        os.makedirs(output_dir, exist_ok=True)
        downloaded_dirs = []
        
        print(f"📥 开始下载 {len(results_list)} 个文件的解析结果")
        
        for i, file_result in enumerate(results_list, 1):
            if file_result['state'] != 'done' or 'full_zip_url' not in file_result:
                filename = file_result.get('file_name', f'文件{i}')
                print(f"⏭️ [{i}] 跳过 {filename}: 状态 {file_result['state']}")
                continue
            
            print(f"📥 [{i}] 下载: {file_result.get('file_name', f'文件{i}')}")
            result_dir = self.download_result(file_result, output_dir)
            if result_dir:
                downloaded_dirs.append(result_dir)
        
        print(f"🎊 批量下载完成! 成功下载: {len(downloaded_dirs)} 个文件")
        return downloaded_dirs
    
    def show_result_summary(self, extract_dir):
        """显示解析结果摘要"""
        # 查找并显示主要文件
        md_files = list(Path(extract_dir).glob('*.md'))
        if md_files:
            md_file = md_files[0]
            print(f"📄 Markdown文件: {md_file.name}")
            
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    print(f"📊 总行数: {len(lines)}")
                    print(f"📏 文件大小: {len(content):,} 字符")
                    
                    # 显示前几行
                    print("\n📖 内容预览:")
                    print("-" * 40)
                    for i, line in enumerate(lines[:5], 1):
                        if line.strip():
                            print(f"{i:2d}| {line[:80]}{'...' if len(line) > 80 else ''}")
                    if len(lines) > 5:
                        print(f"   | ... (还有{len(lines)-5}行)")
                    print("-" * 40)
                    
            except Exception as e:
                print(f"❌ 读取文件失败: {e}")


def main():
    """主函数"""
    parser = MinerUParser()
    
    print("=" * 80)
    print("🔍 MinerU PDF解析工具")
    print("=" * 80)
    
    # 获取命令行参数
    mode = sys.argv[1] if len(sys.argv) > 1 else "auto"
    
    # 查找当前目录的PDF文件
    pdf_files = list(Path('.').glob('*.pdf'))
    
    if not pdf_files:
        print("❌ 当前目录没有找到PDF文件")
        return
    
    print(f"📂 找到 {len(pdf_files)} 个PDF文件:")
    for i, pdf_file in enumerate(pdf_files, 1):
        size = os.path.getsize(pdf_file) / (1024*1024)
        print(f"  {i}. {pdf_file.name} ({size:.1f} MB)")
    
    print("\n" + "=" * 80)
    
    if mode == "single" or (mode == "auto" and len(pdf_files) == 1):
        # 单个文件模式
        if len(pdf_files) == 1:
            selected_file = pdf_files[0]
        else:
            try:
                choice = int(input(f"请选择要解析的文件 (1-{len(pdf_files)}): ")) - 1
                if 0 <= choice < len(pdf_files):
                    selected_file = pdf_files[choice]
                else:
                    print("❌ 无效选择")
                    return
            except (ValueError, KeyboardInterrupt):
                print("❌ 输入无效或用户取消")
                return
        
        print(f"📄 选择文件: {selected_file.name}")
        
        # 解析单个文件
        result = parser.parse_single_pdf(str(selected_file))
        
        if result:
            print("\n" + "=" * 80)
            print("📥 下载解析结果")
            extract_dir = parser.download_result(result)
            if extract_dir:
                print(f"\n🎉 解析完成! 结果保存在: {extract_dir}")
        else:
            print("\n❌ 解析失败")
    
    elif mode == "batch" or (mode == "auto" and len(pdf_files) > 1):
        # 批量文件模式
        if mode == "auto":
            confirm = input(f"发现多个PDF文件，是否批量解析? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ 用户取消")
                return
        
        # 批量解析
        results = parser.parse_batch_pdfs([str(f) for f in pdf_files])
        
        if results:
            print("\n" + "=" * 80)
            print("📥 批量下载解析结果")
            downloaded_dirs = parser.download_batch_results(results)
            if downloaded_dirs:
                print(f"\n🎉 批量解析完成! 结果保存在:")
                for i, dir_path in enumerate(downloaded_dirs, 1):
                    print(f"  {i}. {dir_path}")
        else:
            print("\n❌ 批量解析失败")
    
    else:
        print("❌ 无效的模式参数")
        print("使用方法:")
        print("  python mineru_pdf_parser.py single   # 单个文件解析")
        print("  python mineru_pdf_parser.py batch    # 批量文件解析")
        print("  python mineru_pdf_parser.py          # 自动检测模式")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")
        import traceback
        traceback.print_exc()