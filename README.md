# PaperWhale

AI驱动的学术论文阅读与分析工具，支持多模型、多模态（文本+图表）分析。

## 功能特性

- **多模型支持**: OpenAI GPT-4o、Anthropic Claude、DeepSeek、通义千问等
- **多模态分析**: 支持从PDF中提取图表图片，发送给视觉模型分析
- **上下文管理**: 自动检测文本长度，超限时主动报错并提供解决方案
- **灵活Prompt**: 内置多种分析模板，支持完全自定义
- **批量处理**: 支持整个文件夹批量分析，自动生成汇总文档

## 支持的模型

| 模型 | 视觉支持 | 上下文限制 |
|------|----------|------------|
| GPT-4o | ✓ | ~100k字符 |
| Claude 3.5 Sonnet | ✓ | ~100k字符 |
| 通义千问VL | ✓ | ~30k字符 |
| DeepSeek | ✗ | ~30k字符 |
| 智谱GLM | ✗ | ~30k字符 |

## 安装

```bash
pip install pdfplumber pymupdf requests

# 或一次性安装所有依赖
pip install -r requirements.txt
```

## 配置

复制并编辑 `config.json`：

```json
{
  "active_provider": "openai",
  "model_providers": {
    "openai": {
      "api_key_env": "OPENAI_API_KEY"
    }
  }
}
```

设置环境变量：
```bash
export OPENAI_API_KEY="your-api-key"
export ANTHROPIC_API_KEY="your-api-key"
export DEEPSEEK_API_KEY="your-api-key"
export QWEN_API_KEY="your-api-key"
```

## 使用

### 命令行

```bash
# 默认分析
python main.py --input ./input_pdfs

# 使用指定模型
python main.py --input ./input_pdfs --provider openai

# 使用指定模板
python main.py --input ./input_pdfs --prompt abm_modeling

# 自定义Prompt
python main.py --input ./input_pdfs --custom-prompt "你的分析要求"

# 列出所有模板
python --list-prompts
```

### Python API

```python
from doc_generator import DocGenerator

generator = DocGenerator()
result = generator.analyze_single_paper("path/to/paper.pdf")

if result.success:
    print(result.full_analysis)
    generator.save_single_analysis(result)
```

## 分析模板

| 模板 | 说明 |
|------|------|
| `default` | 深度分析：工作讲解、研究总结、图表讲解、核心贡献 |
| `quick_scan` | 快速扫描，简洁输出 |
| `methodology` | 方法论聚焦 |
| `critical_review` | 批判性评审 |
| `abm_modeling` | 多主体建模专项 |
| `climate_modeling` | 气候模型专项 |

## 测试

```bash
# 运行所有测试
python -m unittest discover -s tests -v

# 运行指定模块测试
python -m unittest tests.test_pdf_reader -v
python -m unittest tests.test_api_client -v
python -m unittest tests.test_doc_generator -v
```

## 项目结构

```
ai_pdf_reader/
├── api_client.py          # API客户端模块
├── config.json            # 配置文件
├── custom_prompts.py      # 自定义Prompt配置
├── doc_generator.py       # 文档生成器
├── main.py                # 主入口
├── pdf_reader.py          # PDF读取模块
├── prompts.py             # 内置Prompt模板
├── requirements.txt       # 依赖列表
├── tests/                 # 测试套件
│   ├── test_pdf_reader.py
│   ├── test_api_client.py
│   └── test_doc_generator.py
├── input_pdfs/            # 输入PDF文件夹
├── output_docs/           # 输出文档文件夹
└── summary_docs/          # 汇总文档文件夹
```

## License

MIT
