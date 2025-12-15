# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

FRAG (Flexible Retrieval-Augmented Generation based on Knowledge Graphs) 是一个基于知识图谱的检索增强生成框架。该项目支持复杂查询推理，通过模块化设计实现灵活的检索-推理管道。

## 核心架构

### 模块化管道架构 (RecordPipeline)
FRAG 采用三阶段管道式处理架构：

1. **PreRetrievalModule**: 预检索模块，使用 BGE 等嵌入模型进行实体扩展和子图构建
   - `PreRetrievalModuleBGE`: 基于 BGE 嵌入的预检索
   - 支持配置扩展实体数量 (如 64 个)

2. **RetrievalModule**: 检索模块，在子图中进行推理路径发现
   - `RetrievalModuleBFS`: 广度优先搜索路径检索 (用于简单查询)
   - `RetrievalModuleDij`: Dijkstra 算法路径检索 (用于复杂查询)
   - 支持配置跳数限制 (如 2-4 跳)

3. **PostRetrievalModule**: 后检索模块，对路径进行重排序和筛选
   - `PostRetrievalModuleBGE`: 基于 BGE 的路径重排序
   - 支持配置最大路径数 (如 32 条)

### 核心类和组件

- **Query**: 查询表示类，包含问题、答案、实体和子图
- **ReasoningPath**: 推理路径表示，支持多跳推理路径
- **LLM**: 大语言模型封装，支持 Ollama 本地模型和商业 API (OpenAI, Moonshot)
- **SentenceModel**: 句子嵌入模型，基于 sentence-transformers

## 常用开发命令

### 环境设置

**方案1: 使用 uv (推荐的现代包管理器)**
```bash
# 安装项目依赖
uv sync

# 运行项目脚本 (使用 uv run)
uv run python FRAG/src/getPaths.py

# 或进入 shell 环境
uv shell
```

**方案2: 使用传统方式**
```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装项目依赖
pip install -e .

# 直接运行脚本
python FRAG/src/getPaths.py
```

### 核心运行流程

#### 步骤 0: 数据预处理 (可选)
如果需要从原始 Freebase 数据开始：

**使用 uv:**
```bash
cd data_preprocess
uv run python get_id2name.py          # 获取实体ID到名称映射
uv run python manual_filter_rel.py    # 手动过滤关系
uv run python filter_rel.py           # 过滤关系
uv run python preprocess_step0.py     # 预处理数据集
uv run python PPRmultithread.py       # 使用 PPR 算法获取查询特定子图
```

**使用传统方式:**
```bash
cd data_preprocess
source ../.venv/bin/activate  # 如果尚未激活
python get_id2name.py          # 获取实体ID到名称映射
python manual_filter_rel.py    # 手动过滤关系
python filter_rel.py           # 过滤关系
python preprocess_step0.py     # 预处理数据集
python PPRmultithread.py       # 使用 PPR 算法获取查询特定子图
```

#### 步骤 1: 获取推理路径

**使用 uv:**
```bash
cd FRAG/src
uv run python getPaths.py
```

**使用传统方式:**
```bash
cd FRAG/src
source ../../.venv/bin/activate  # 如果尚未激活
python getPaths.py
```
- 生成 `CWQ_paths.json` 或 `webqsp_paths.json`
- 简单查询使用: `PreRetrievalModuleBGE(64) + RetrievalModuleBFS(2) + PostRetrievalModuleBGE(32)`
- 复杂查询使用: `PreRetrievalModuleBGE(64) + RetrievalModuleDij(4) + PostRetrievalModuleBGE(32)`

#### 步骤 2: LLM 推理

**使用 uv:**
```bash
cd FRAG/src
uv run python Reason.py
```

**使用传统方式:**
```bash
cd FRAG/src
source ../../.venv/bin/activate  # 如果尚未激活
python Reason.py
```

#### 步骤 3: FRAG 主框架

**使用 uv:**
```bash
# 下载 ReasoningAwareModule 模型到 text-classification-model/
cd FRAG/src
uv run python FRAG.py
```

**使用传统方式:**
```bash
# 下载 ReasoningAwareModule 模型到 text-classification-model/
cd FRAG/src
source ../../.venv/bin/activate  # 如果尚未激活
python FRAG.py
```

#### 步骤 4: FRAG_F (反馈版本)

**使用 uv:**
```bash
cd FRAG/src
# 首先获取跳数预测
uv run python getHopPred.py
# 然后运行 FRAG_F
uv run python FRAG_F.py
```

**使用传统方式:**
```bash
cd FRAG/src
source ../../.venv/bin/activate  # 如果尚未激活
# 首先获取跳数预测
python getHopPred.py
# 然后运行 FRAG_F
python FRAG_F.py
```

## 配置说明

### 环境变量配置
创建 `.env` 文件设置 API 密钥：
```
OPENAI_API_KEY=your_openai_key
MOONSHOT_API_KEY=your_moonshot_key
```

### 主要配置文件
- `FRAG/src/config.py`: 核心配置文件
  - 模型配置 (Ollama 本地模型、商业 API 模型)
  - 数据集配置 (CWQ, WebQSP)
  - 嵌入模型配置 (BGE, reranker)
  - 评估参数配置

### 数据集路径约定
- 数据根目录: `dataset/AAAI/{experiment_type}/{dataset}/{reasoning_type}/`
- 测试文件: `{dataset_dir}/test_name.jsonl`
- 结果文件: `{dataset_dir}/{model}_answers.json`

## 模型和数据

### 支持的模型
- **本地 Ollama 模型**: llama2, llama3 系列 (7B, 8B, 70B)
- **商业 API**: GPT-3.5/4, Moonshot
- **嵌入模型**: BGE 系列嵌入和重排序模型

### 支持的数据集
- **CWQ** (ComplexWebQuestions): 复杂查询数据集
- **WebQSP** (WebQuestionsSP): 简单查询数据集

## 代码结构说明

```
FRAG/
├── src/
│   ├── config.py                 # 全局配置
│   ├── getPaths.py              # 路径获取入口
│   ├── Reason.py                # LLM 推理入口
│   ├── FRAG.py                  # FRAG 主框架入口
│   ├── FRAG_F.py                # FRAG_F 反馈版本入口
│   ├── getHopPred.py            # 跳数预测入口
│   ├── pipeline/                # 管道模块
│   │   └── RecordPipeline.py    # 三阶段管道实现
│   ├── utils/                   # 工具类
│   │   ├── LLM.py              # LLM 封装
│   │   ├── Query.py            # 查询类
│   │   ├── ReasoningPath.py    # 推理路径类
│   │   ├── SentenceModel.py    # 句子嵌入模型
│   │   ├── Evaluation.py       # 评估指标
│   │   └── Tools.py            # 辅助工具
│   ├── pre_retrieval/          # 预检索模块
│   ├── retrieval/              # 检索模块
│   └── post_retrieval/         # 后检索模块
└── data_preprocess/            # 数据预处理脚本
```

## 开发注意事项

1. **内存管理**: 大规模知识图谱处理时注意内存使用，建议使用流式处理
2. **模型路径**: 确保下载的模型文件路径正确 (如 `text-classification-model/`)
3. **数据格式**: 严格按照 JSON 格式准备输入数据，包含 id, question, answers, entities, subgraph 字段
4. **并行处理**: `PPRmultithread.py` 支持多线程 PPR 计算，可调整线程数优化性能
5. **评估指标**: 使用 ACC, F1, Hit@K 等指标评估推理质量

## 常见问题排查

- **导入错误**: 确保在正确目录下运行脚本，或使用 `PYTHONPATH` 环境变量
- **模型加载失败**: 检查 `.env` 文件中的 API 密钥配置
- **内存不足**: 减少批处理大小或使用更小的嵌入模型
- **路径格式错误**: 检查 JSON 文件格式，确保子图和实体格式正确