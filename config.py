"""
配置管理模块
管理API密钥和其他配置项
"""

import os
import json
from typing import Optional, Dict, Any
from pathlib import Path

class Config:
    """配置管理类"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        初始化配置管理
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.config_data = {}
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        # 首先尝试从环境变量读取
        self.config_data = {
            'o3_api_key': os.getenv('O3_API_KEY'),
            'o3_base_url': os.getenv('O3_BASE_URL', 'https://api.o3.fan/v1'),
            'o3_model': os.getenv('O3_MODEL', 'claude-sonnet-4-20250514'),
            'mineru_api_key': os.getenv('MINERU_API_KEY'),
            'mineru_base_url': os.getenv('MINERU_BASE_URL', 'https://api.mineru.com'),
        }
        
        # 然后尝试从配置文件读取（会覆盖环境变量）
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # 只更新非空值
                    for key, value in file_config.items():
                        if value:
                            self.config_data[key] = value
            except Exception as e:
                print(f"⚠️  读取配置文件失败: {e}")
                print(f"将使用默认配置和环境变量")
    
    def save_config(self):
        """保存配置到文件（不保存空值）"""
        # 只保存非空的配置项
        save_data = {k: v for k, v in self.config_data.items() if v}
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            print(f"✅ 配置已保存到 {self.config_file}")
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config_data.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        self.config_data[key] = value
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """验证API密钥配置"""
        validation = {
            'o3_api_key': bool(self.get('o3_api_key')),
            'mineru_api_key': bool(self.get('mineru_api_key')),
        }
        return validation
    
    def get_missing_keys(self) -> list:
        """获取缺失的API密钥"""
        validation = self.validate_api_keys()
        return [key for key, is_valid in validation.items() if not is_valid]
    
    def print_status(self):
        """打印配置状态"""
        print("📋 当前配置状态:")
        print("-" * 40)
        
        # O3 API配置
        o3_key = self.get('o3_api_key')
        if o3_key:
            print(f"✅ O3 API Key: {o3_key[:20]}...")
        else:
            print("❌ O3 API Key: 未配置")
        
        print(f"🔗 O3 Base URL: {self.get('o3_base_url')}")
        print(f"🤖 O3 Model: {self.get('o3_model')}")
        
        # MinerU API配置
        mineru_key = self.get('mineru_api_key')
        if mineru_key:
            print(f"✅ MinerU API Key: {mineru_key[:20]}...")
        else:
            print("❌ MinerU API Key: 未配置")
        
        print(f"🔗 MinerU Base URL: {self.get('mineru_base_url')}")
        
        # 检查缺失项
        missing = self.get_missing_keys()
        if missing:
            print(f"\n⚠️  缺失的配置项: {', '.join(missing)}")
        else:
            print(f"\n🎉 所有API密钥配置完成！")

def create_config_template():
    """创建配置文件模板"""
    template = {
        "o3_api_key": "",
        "o3_base_url": "https://api.o3.fan/v1",
        "o3_model": "claude-sonnet-4-20250514",
        "mineru_api_key": "",
        "mineru_base_url": "https://api.mineru.com"
    }
    
    config_file = Path("config.json")
    if not config_file.exists():
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        print(f"✅ 已创建配置文件模板: {config_file}")
        print("请编辑此文件填入您的API密钥")
    else:
        print(f"⚠️  配置文件已存在: {config_file}")

def setup_config_interactive():
    """交互式配置设置"""
    print("🔧 交互式API配置")
    print("=" * 50)
    
    config = Config()
    
    # O3 API配置
    print("\n1️⃣ O3 API配置 (用于智能信息提取)")
    print("   平台: O3.fan")
    print("   模型: Claude Sonnet 4")
    
    current_o3 = config.get('o3_api_key')
    if current_o3:
        print(f"   当前密钥: {current_o3[:20]}...")
        if input("   是否要更新O3 API密钥? (y/N): ").lower() == 'y':
            o3_key = input("   请输入新的O3 API密钥: ").strip()
            if o3_key:
                config.set('o3_api_key', o3_key)
    else:
        o3_key = input("   请输入O3 API密钥: ").strip()
        if o3_key:
            config.set('o3_api_key', o3_key)
    
    # MinerU API配置
    print("\n2️⃣ MinerU API配置 (用于PDF解析)")
    print("   平台: MinerU")
    
    current_mineru = config.get('mineru_api_key')
    if current_mineru:
        print(f"   当前密钥: {current_mineru[:20]}...")
        if input("   是否要更新MinerU API密钥? (y/N): ").lower() == 'y':
            mineru_key = input("   请输入新的MinerU API密钥: ").strip()
            if mineru_key:
                config.set('mineru_api_key', mineru_key)
    else:
        mineru_key = input("   请输入MinerU API密钥: ").strip()
        if mineru_key:
            config.set('mineru_api_key', mineru_key)
    
    # 保存配置
    config.save_config()
    print("\n🎉 配置完成！")
    config.print_status()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "template":
            create_config_template()
        elif sys.argv[1] == "setup":
            setup_config_interactive()
        elif sys.argv[1] == "status":
            config = Config()
            config.print_status()
        else:
            print("用法:")
            print("  python config.py template  # 创建配置模板")
            print("  python config.py setup     # 交互式设置")
            print("  python config.py status    # 查看配置状态")
    else:
        print("🔧 配置管理工具")
        print("用法:")
        print("  python config.py template  # 创建配置模板")
        print("  python config.py setup     # 交互式设置")
        print("  python config.py status    # 查看配置状态")