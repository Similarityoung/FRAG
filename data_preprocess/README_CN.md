# 数据预处理模块 (Data Preprocess)

本模块包含 ComplexWebQuestions (CWQ) 数据集的完整预处理流程，用于从原始 Freebase 知识图谱和问题数据中提取和处理信息。

## 文件说明

### 1. `get_id2name.py` - 实体ID到名称映射提取
**功能**：从 Freebase 数据中提取实体ID到人类可读名称的映射。

**输入**：
- `data/fb_en.txt` - 原始 Freebase 数据文件（三元组格式：实体ID \t 关系 \t 值）

**输出**：
- `process_data/id2name.txt` - 实体ID到名称的映射文件（格式：实体ID \t type.object.name \t 实体名称）

**处理方式**：
- 筛选所有 `type.object.name` 关系的三元组
- 这些三元组包含实体的英文名称

**使用场景**：为后续步骤提供实体名称查询表，使输出结果更易读。

---

### 2. `manual_filter_rel.py` - 手动关系过滤
**功能**：基于黑名单过滤不需要的关系域，保留核心知识图谱关系。

**输入**：
- `data/fb_en.txt` - 原始 Freebase 数据文件

**输出**：
- `process_data/manual_fb_filter.txt` - 手动过滤后的关系文件

**过滤的关系域**：
- 音乐相关：`music.release`, `authority.musicbrainz`
- 书籍相关：`book.isbn`
- 电视相关：`tv.tv_series_episode`
- 系统相关：`type.namespace`, `type.content`, `type.permission`
- 其他：`common.licensed_object`, `topic_equivalent_webpage` 等

**处理方式**：
- 逐行读取原始数据
- 检查每个三元组的关系是否包含黑名单中的任何域
- 保留不在黑名单中的三元组

**输出统计**：打印总行数和保留的行数

---

### 3. `filter_rel.py` - 进一步关系过滤
**功能**：在手动过滤基础上，进一步移除不需要的关系类型。

**输入**：
- `manual_fb_filter.txt` - 手动过滤后的关系文件

**输出**：
- `rel_filter.txt` - 最终过滤后的关系文件

**过滤的关系类型**：
- `type.object.type` - 对象类型关系
- `type.object.name` - 对象名称关系（已在 get_id2name.py 中提取）
- `type.type.*` - 所有类型相关关系
- `common.*` - 所有通用关系
- `freebase.*` - 所有 Freebase 系统关系
- 包含 `sameAs` 或 `sameas` 的关系 - 同义关系

**处理方式**：
- 逐行读取手动过滤后的数据
- 使用 `abandon_rels()` 函数判断是否应该过滤
- 保留通过过滤的三元组

**输出统计**：打印总行数和保留的行数

---

### 4. `preprocess_step0.py` - 数据预处理第0步
**功能**：处理 ComplexWebQuestions 数据集，提取问题、答案和实体信息。

**输入**：
- `origin/Freebase/CWQ/ComplexWebQuestions_train.json` - 训练集
- `origin/Freebase/CWQ/ComplexWebQuestions_test_wans.json` - 测试集
- `origin/Freebase/CWQ/ComplexWebQuestions_dev.json` - 开发集
- `process_data/id2name.txt` - 实体ID到名称的映射

**输出**：
- `process_data/CWQ/CWQ_step0.json` - 处理后的问题数据（JSONL 格式）

**处理流程**：
1. 加载实体ID到名称的映射字典
2. 对每个数据文件进行处理：
   - 提取问题ID、问题文本、答案列表
   - 从 SPARQL 查询中提取实体ID
   - 将实体ID转换为实体名称
3. 构建标准化的输出对象：
   ```json
   {
     "id": "问题ID",
     "question": "问题文本",
     "answers": [
       {"kb_id": "答案ID", "text": "答案文本"},
       ...
     ],
     "entities": [
       {"kb_id": "实体ID", "text": "实体名称"},
       ...
     ]
   }
   ```

**统计信息**：打印实体覆盖率（有名称的实体数 vs 无名称的实体数）

**数据来源**：https://github.com/lanyunshi/KBQA-GST

---

### 5. `PPRmultithread.py` - 个性化 PageRank 多线程处理
**功能**：使用个性化 PageRank (PPR) 算法从知识图谱中提取与问题相关的子图。

**输入**：
- `rel_filter.txt` - 过滤后的知识图谱（三元组）
- `id2name.txt` - 实体ID到名称的映射
- `CWQ/CWQ_step0.jsonl` - 预处理后的问题数据

**输出**：
- `dataset/AAAI/MainExperiment/CWQ/PPR2/test_name.jsonl` - 包含子图的问题数据

**核心算法**：

#### 个性化 PageRank (PPR)
- 从问题中的实体（种子节点）出发
- 计算知识图谱中每个实体与种子节点的相关性
- 重启概率设置为 0.8（高概率回到种子节点）

#### 子图提取流程
1. **获取 k-hop 邻域**：从种子实体出发，扩展 2 跳，收集所有可达的实体
2. **PPR 排序**：使用 PPR 算法对邻域中的实体进行排序
3. **实体选择**：取 PPR 值最高的前 2000 个实体
4. **三元组提取**：从选中的实体中提取所有连接关系

**多线程处理**：
- 将输入数据分割成 64 个块
- 使用多进程池并行处理每个块
- 将结果写入临时文件，最后合并

**输出格式**：
```json
{
  "id": "问题ID",
  "question": "问题文本",
  "answers": ["答案文本1", "答案文本2", ...],
  "entities": ["实体名称1", "实体名称2", ...],
  "subgraph": [
    ["实体1", "关系", "实体2"],
    ["实体2", "关系", "实体3"],
    ...
  ]
}
```

**性能优化**：
- 使用 igraph 库进行高效的图操作
- 多线程并行处理提高吞吐量
- 优化的 k-hop 邻域获取算法

---

## 完整处理流程

```
原始 Freebase 数据 (fb_en.txt)
    ↓
[get_id2name.py] → id2name.txt (实体名称映射)
    ↓
[manual_filter_rel.py] → manual_fb_filter.txt (手动过滤)
    ↓
[filter_rel.py] → rel_filter.txt (进一步过滤)
    ↓
原始问题数据 (ComplexWebQuestions_*.json)
    ↓
[preprocess_step0.py] → CWQ_step0.json (问题预处理)
    ↓
[PPRmultithread.py] → test_name.jsonl (子图提取)
    ↓
最终处理数据（包含知识图谱子图）
```

## 运行顺序

1. **第一步**：准备 Freebase 数据
   ```bash
   python get_id2name.py
   python manual_filter_rel.py
   python filter_rel.py
   ```

2. **第二步**：预处理问题数据
   ```bash
   python preprocess_step0.py
   ```

3. **第三步**：提取子图（多线程）
   ```bash
   python PPRmultithread.py
   ```

## 关键参数说明

### PPRmultithread.py 中的参数
- `threads = 64` - 并行处理的线程数，可根据 CPU 核心数调整
- `max_ent = 2000` - 每个问题提取的最大实体数
- `hop = 2` - k-hop 邻域的跳数
- `restart_prob = 0.8` - PPR 重启概率

### preprocess_step0.py 中的参数
- 实体ID识别：以 `m.` 或 `g.` 开头的字符串

## 输出数据统计

处理完成后，各步骤会打印统计信息：
- **get_id2name.py**：提取的实体名称数
- **manual_filter_rel.py**：总三元组数和保留的三元组数
- **filter_rel.py**：总三元组数和保留的三元组数
- **preprocess_step0.py**：实体覆盖率（有名称的实体数 vs 无名称的实体数）
- **PPRmultithread.py**：各线程的处理时间

## 注意事项

1. **磁盘空间**：确保有足够的磁盘空间存储中间文件和最终结果
2. **内存使用**：PPRmultithread.py 会将整个知识图谱加载到内存，需要足够的 RAM
3. **处理时间**：完整处理可能需要数小时，具体取决于数据规模和硬件性能
4. **文件路径**：所有脚本假设在特定的目录结构下运行，需要根据实际情况调整路径

## 相关资源

- **CWQ 数据集**：https://github.com/lanyunshi/KBQA-GST
- **Freebase 知识图谱**：https://developers.google.com/freebase
- **igraph 库文档**：https://igraph.org/python/
- **个性化 PageRank 算法**：https://en.wikipedia.org/wiki/PageRank#Personalized_PageRank
