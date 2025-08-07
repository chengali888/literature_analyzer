# 安装和使用指南

## 🚀 快速开始

### 1. 检查环境
```bash
# 检查Python版本 (需要 3.7+)
python --version

# 检查是否有tkinter (GUI界面需要)
python -c "import tkinter; print('tkinter可用')"
```

### 2. 安装依赖
```bash
# 安装必要的Python包
pip install requests openai tqdm python-dotenv

# 或使用requirements.txt
pip install -r requirements.txt
```

### 3. 配置API密钥

编辑以下文件中的API配置：

**在 `literature_processing_agent.py` 中:**
```python
# 第11行，修改为您的O3 API密钥
API_KEY = 'your-o3-api-key-here'
```

**在 `mineru_pdf_parser.py` 中:**
```python
# 第25行，修改为您的MinerU API令牌
API_TOKEN = "your-mineru-api-token-here"
```

### 4. 开始使用

#### 方式1: 图形界面 (推荐)
```bash
python run_agent.py gui
```

#### 方式2: 命令行界面
```bash
python run_agent.py cli
```

#### 方式3: 运行演示
```bash
python run_agent.py demo
```

## 📋 详细安装步骤

### Windows用户

1. **安装Python 3.7+**
   - 从 [python.org](https://python.org) 下载并安装
   - 确保勾选"Add Python to PATH"

2. **安装依赖**
   ```cmd
   pip install requests openai tqdm python-dotenv
   ```

3. **检查tkinter**
   ```cmd
   python -c "import tkinter; print('tkinter可用')"
   ```
   如果报错，重新安装Python时选择完整安装。

### macOS用户

1. **安装Python 3.7+**
   ```bash
   # 使用Homebrew
   brew install python3
   
   # 或使用pyenv
   pyenv install 3.9.0
   pyenv global 3.9.0
   ```

2. **安装依赖**
   ```bash
   pip3 install requests openai tqdm python-dotenv
   ```

3. **检查tkinter**
   ```bash
   python3 -c "import tkinter; print('tkinter可用')"
   ```

### Linux用户

1. **安装Python和tkinter**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip python3-tk
   
   # CentOS/RHEL
   sudo yum install python3 python3-pip tkinter
   
   # Fedora
   sudo dnf install python3 python3-pip python3-tkinter
   ```

2. **安装依赖**
   ```bash
   pip3 install requests openai tqdm python-dotenv
   ```

## ⚙️ API配置详细说明

### MinerU API
1. 注册账号: [https://mineru.net](https://mineru.net)
2. 获取API Token
3. 修改 `mineru_pdf_parser.py` 中的 `API_TOKEN`

### O3 API  
1. 获取O3 API密钥
2. 修改 `literature_processing_agent.py` 中的 `API_KEY`

## 🧪 测试安装

### 1. 依赖测试
```bash
python run_agent.py
```
程序会自动检查依赖项并报告问题。

### 2. 功能测试
```bash
# 运行演示模式
python run_agent.py demo
```

### 3. GUI测试
```bash
# 启动图形界面
python run_agent.py gui
```

## 🐛 故障排除

### 常见问题

**Q: ImportError: No module named 'tkinter'**
```bash
# Ubuntu/Debian
sudo apt install python3-tk

# macOS (如果使用Homebrew)
brew install python-tk

# Windows: 重新安装Python并选择完整安装
```

**Q: API调用失败**
```bash
# 检查网络连接
ping api.o3.fan

# 检查API密钥是否正确配置
# 查看代码中的API_KEY和API_TOKEN设置
```

**Q: 文件权限错误**
```bash
# 确保有当前目录的写权限
chmod 755 .

# 创建输出目录
mkdir -p processed_results
```

**Q: 内存不足**
```bash
# 减少批量处理的文件数量
# 或增加系统内存/虚拟内存
```

### 日志和调试

启用详细日志：
```bash
# 设置环境变量
export PYTHONUNBUFFERED=1

# 运行程序
python run_agent.py gui 2>&1 | tee debug.log
```

## 📁 项目文件说明

```
literature_analyzer/
├── literature_processing_agent.py    # 主控制器
├── literature_agent_gui.py          # GUI界面
├── mineru_pdf_parser.py              # PDF解析模块
├── full_structure_property_extraction.py  # 信息提取模块
├── run_agent.py                      # 启动脚本
├── example_usage.py                  # 使用示例
├── requirements.txt                  # 依赖列表
├── README.md                         # 项目说明
├── INSTALL.md                        # 安装指南
└── parsed_results/                   # 解析结果目录
```

## 🔧 高级配置

### 自定义输出目录
在代码中修改输出路径：
```python
# 修改默认输出目录
output_dir = "custom_results"
```

### 性能优化
```python
# 调整API调用间隔
time.sleep(5)  # 在批量处理中增加延迟

# 限制图片数量
max_images = 5  # 减少单次处理的图片数量
```

### 错误重试配置
```python
# 增加重试次数
retries = 5

# 调整超时设置
timeout = 60
```

## 📞 技术支持

如遇到问题：
1. 查看本安装指南
2. 检查README.md中的常见问题
3. 运行 `python run_agent.py demo` 测试基本功能
4. 查看错误日志定位问题
5. 联系技术支持

---

*安装完成后，建议先运行demo模式熟悉功能。*