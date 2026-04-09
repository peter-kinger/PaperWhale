# 🐋 PaperWhale

> **像鲸鱼一样快速吞遍文献，同时按照你的胃口吃饱**
>
> Swallow academic papers like a whale — fast, thorough, and perfectly sized for your appetite.

[![GitHub stars](https://img.shields.io/github/stars/peter-kinger/PaperWhale?style=for-the-badge&logo=github)](https://github.com/peter-kinger/PaperWhale/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/peter-kinger/PaperWhale?style=for-the-badge&logo=github)](https://github.com/peter-kinger/PaperWhale/network/members)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)](https://www.python.org/)
[![Last Commit](https://img.shields.io/github/last-commit/peter-kinger/PaperWhale/main?style=for-the-badge&logo=github)](https://github.com/peter-kinger/PaperWhale/commits/main)

---

## ✨ 核心特性

| 特性 | 说明 |
|:---|:---|
| 🧠 **多模型支持** | GPT-4o、Claude 3.5 Sonnet、DeepSeek、通义千问VL、智谱GLM |
| 👁️ **多模态分析** | 从 PDF 提取图表图片，发送给视觉模型深度理解 |
| 📏 **上下文管理** | 自动检测文本长度，超限时主动报错，防止截断 |
| 🎯 **6种分析模板** | 默认深度分析 / 快速扫描 / 方法论 / 批判评审 / ABM / 气候模型 |
| 📚 **批量处理** | 文件夹批量分析，自动生成汇总文档 |
| 🔧 **完全可定制** | 自定义 Prompt 模板，按你的需求打造专属分析流程 |

---

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/peter-kinger/PaperWhale.git
cd PaperWhale
pip install -r requirements.txt
```

### 配置

编辑 `config.json` 设置你的 API Key：

```json
{
  "active_provider": "openai",
  "model_providers": {
    "openai": { "api_key_env": "OPENAI_API_KEY" },
    "anthropic": { "api_key_env": "ANTHROPIC_API_KEY" },
    "deepseek": { "api_key_env": "DEEPSEEK_API_KEY" }
  }
}
```

设置环境变量：

```bash
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

### 使用

```bash
# 默认分析（深度分析）
python main.py --input ./input_pdfs

# 快速扫描
python main.py --input ./input_pdfs --prompt quick_scan

# 指定模型
python main.py --input ./input_pdfs --provider anthropic

# 自定义分析要求
python main.py --input ./input_pdfs --custom-prompt "重点分析方法的创新性"

# 列出所有模板
python main.py --list-prompts
```

---

## 📊 支持的模型

| 模型 | 视觉支持 | 上下文限制 | 特点 |
|:---|:---:|:---:|:---|
| GPT-4o | 👁️ | ~100k | 综合最强 |
| Claude 3.5 Sonnet | 👁️ | ~100k | 长文本优秀 |
| 通义千问VL | 👁️ | ~30k | 中文友好 |
| DeepSeek | — | ~30k | 性价比高 |
| 智谱GLM | — | ~30k | 中文优化 |

---

## 🎨 分析模板

| 模板 | 适用场景 |
|:---|:---|
| `default` | 深度论文精读 — 工作讲解 / 研究总结 / 图表分析 / 核心贡献 |
| `quick_scan` | 快速了解论文大意 |
| `methodology` | 方法论专项分析 |
| `critical_review` | 批判性评审与挑错 |
| `abm_modeling` | 多主体建模研究专项 |
| `climate_modeling` | 气候模型研究专项 |

---

## 🔬 项目架构

```
PaperWhale/
├── api_client.py        # 🤖 多模型 API 客户端（视觉多模态支持）
├── pdf_reader.py        # 📄 PDF 文本与图表提取
├── doc_generator.py     # 📝 分析结果生成与 Prompt 管理
├── main.py              # 🚪 命令行入口
├── config.json          # ⚙️ 配置文件
├── custom_prompts.py    # 📋 自定义 Prompt 模板
├── prompts.py           # 📚 内置分析模板
├── requirements.txt     # 📦 依赖清单
├── tests/               # 🧪 单元测试（46 个用例）
│   ├── test_pdf_reader.py
│   ├── test_api_client.py
│   └── test_doc_generator.py
├── input_pdfs/          # 📥 输入 PDF 文件夹
├── output_docs/         # 📤 单篇分析输出
└── summary_docs/        # 📑 批量汇总文档
```

---

## 🧪 测试

```bash
# 运行所有测试
python -m unittest discover -s tests -v

# 分模块运行
python -m unittest tests.test_pdf_reader -v
python -m unittest tests.test_api_client -v
python -m unittest tests.test_doc_generator -v
```

---

## 🌟 与鲸鱼共游

```
     _
    ( )   PaperWhale 🐋
   _| |__   "海量文献，一口鲸吞"
  (_) (_)
```

**为什么叫 PaperWhale？**

- 🐋 **鲸吞** — 像鲸鱼一样快速吞下海量文献
- 🎯 **精准** — 按照你的胃口（需求）精准分析
- 📈 **成长** — 吃得越多，积累越深（批量分析 + 汇总）

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

<p align="center">
  <strong>如果对你有帮助，欢迎 star ⭐ 和 fork 🍴</strong>
</p>
