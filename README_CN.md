# FRAG 流水线 (中文指南)

本文档对应英文版 `README.md`，提供 **FRAG: A Flexible Modular Framework for Retrieval-Augmented Generation based on Knowledge Graphs** 的中文使用说明。

> **论文链接**：[arXiv PDF](https://arxiv.org/abs/2501.09957)  
> Zengyi Gao, Yukun Cao, Hairu Wang, Ao Ke, Yuan Feng, Xike Xie, S Kevin Zhou  
> **ACL 2025**

<p align="center">
  <img src="FRAG.png" alt="FRAG 概览" width="100%" />
</p>

## 步骤 0：数据预处理

通过个性化 PageRank (PPR) 为每个查询生成子图 `test_name.jsonl`。

详细流程见 [`data_preprocess/README_CN.md`](data_preprocess/README_CN.md)。

## 步骤 1：推理路径生成
```bash
python getPaths.py
```
该脚本会为每个查询生成推理路径，默认配置：
- 简单查询：`RecordPipeline(PreRetrievalModuleBGE(64), RetrievalModuleBFS(2), PostRetrievalModuleBGE(32))`
- 复杂查询：`RecordPipeline(PreRetrievalModuleBGE(64), RetrievalModuleDij(4), PostRetrievalModuleBGE(32))`

## 步骤 2：使用推理路径 + LLM 推理
```bash
python Reason.py
```

## 步骤 3：FRAG 模型
1. 从 [Hugging Face](https://huggingface.co/gzy02/ReasoningAwareModule) 下载 Reasoning-aware 模型。
2. 运行：
```bash
python FRAG.py
```

## 步骤 4：FRAG_F（带跳数预测）
1. 将 `stop_tokens` 设置为 `["\n"]`。
2. 运行：
```bash
python getHopPred.py
```
3. 获得简单/复杂查询的 hop 预测结果后，执行：
```bash
python FRAG_F.py
```

---

## 引用
如果本项目对您的研究有帮助，请引用我们的论文：

```bibtex
@inproceedings{gao-FRAG-2025,
  title     = {FRAG: A Flexible Modular Framework for Retrieval-Augmented Generation based on Knowledge Graphs},
  author    = {Zengyi Gao and Yukun Cao and Hairu Wang and Ao Ke and Yuan Feng and Xike Xie and S Kevin Zhou},
  booktitle = {Findings of the Association for Computational Linguistics: ACL 2025},
  year      = {2025},
  publisher = {Association for Computational Linguistics}
}
```
