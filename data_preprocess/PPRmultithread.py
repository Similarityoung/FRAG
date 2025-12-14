# 个性化 PageRank (PPR) 多线程处理脚本
# 用于从知识图谱中提取与问题相关的子图
# 基于问题中的实体作为种子节点，使用 PPR 算法排序相关实体

from multiprocessing import Pool
from time import time
from copy import deepcopy
import json
import igraph as ig
from typing import List, Dict, Set


def personalized_pagerank(G: ig.Graph, vertices: Set[str], seed_nodes: List[str], restart_prob=0.8):
    """计算给定种子节点的个性化 PageRank (PPR) 向量
    
    使用 igraph 库计算 PPR，用于在知识图谱中找到与种子节点相关的实体。

    Args:
        G: igraph 图对象（知识图谱）
        vertices: 图中所有顶点的集合
        seed_nodes: 种子节点ID列表（问题中提到的实体）
        restart_prob: 重启概率，范围 [0, 1]，默认 0.8

    Returns:
        ppr: 字典，映射节点ID到其PPR值
    """

    vertices_list = list(vertices)
    # 使用 igraph 的 personalized_pagerank 方法计算 PPR
    ppr = G.personalized_pagerank(
        vertices=vertices,
        damping=restart_prob,
        reset_vertices=seed_nodes,
    )

    return dict(zip(vertices_list, ppr))


def rank_ppr_ents(G: ig.Graph, vertices: Set[str], seed_list: List[str], mode="fixed", max_ent=2000, min_ppr=0.005):
    """基于 PPR 值排序并提取相关实体
    
    Args:
        G: igraph 图对象
        vertices: 图中所有顶点的集合
        seed_list: 种子节点列表
        mode: 提取模式，"fixed" 表示固定数量，其他表示阈值模式
        max_ent: 固定模式下要提取的最大实体数，默认 2000
        min_ppr: 阈值模式下的最小 PPR 值，默认 0.005
        
    Returns:
        提取的实体ID列表，按 PPR 值排序
    """
    # 在子图上运行 PPR 算法
    ppr = personalized_pagerank(G, vertices, seed_list, restart_prob=0.8)

    # 根据模式提取实体
    if mode == "fixed":
        # 固定数量模式：取 PPR 值最高的 max_ent 个实体
        sorted_ppr = sorted(ppr.items(), key=lambda x: x[1], reverse=True)
        extracted_ents = [node for node, _ in sorted_ppr[:max_ent]]
    else:
        # 阈值模式：取 PPR 值大于 min_ppr 的所有实体
        extracted_ents = [node for node,
                          value in ppr.items() if value > min_ppr]

    return extracted_ents


def get_k_hop_neighbors_optimized(G: ig.Graph, seed_list: List[str], hop: int) -> Set:
    """获取种子节点的 k-hop 邻域（优化版本）
    
    从种子节点出发，沿着图的边界扩展 k 跳，收集所有可达的节点。
    
    Args:
        G: igraph 图对象
        seed_list: 种子节点列表
        hop: 跳数（邻域深度）
        
    Returns:
        包含所有 k-hop 邻域节点的集合
    """
    visited = set(seed_list)  # 已访问的节点集合
    current_layer = set(seed_list)  # 当前层的节点
    
    # 迭代 hop 次，每次扩展一层
    for _ in range(hop):
        next_layer = set()
        for node in current_layer:
            # 获取该节点的出边邻居
            neighbors = G.neighbors(node, mode="out")
            # 只保留未访问过的邻居
            new_neighbors = set(neighbors) - visited
            next_layer.update(new_neighbors)
            visited.update(new_neighbors)
        current_layer = next_layer
    
    return visited


def get_triples(G: ig.Graph):
    """从图中提取所有三元组（实体-关系-实体）
    
    Args:
        G: igraph 图对象
        
    Returns:
        三元组列表，每个三元组为 [head_entity, relation, tail_entity]
    """
    ans = []
    # 遍历图中的所有边
    for edge in G.es:
        head = G.vs[edge.source]["label"]  # 源节点的标签（实体名称）
        tail = G.vs[edge.target]["label"]  # 目标节点的标签（实体名称）
        rel = edge["name"]  # 边的标签（关系类型）
        ans.append([head, rel, tail])
    return ans


def chunkify(lst, n):
    """将列表均匀分割成 n 个块
    
    用于多线程处理时的数据分割。
    
    Args:
        lst: 待分割的列表
        n: 要分割成的块数
        
    Returns:
        分割后的块列表
    """
    base_chunk_size = len(lst) // n  # 基础块大小
    num_chunks_with_extra = len(lst) % n  # 需要额外元素的块数
    chunks = []
    start_index = 0

    # 创建 n 个块
    for i in range(n):
        if i < num_chunks_with_extra:
            # 前 num_chunks_with_extra 个块多分配一个元素
            chunk_size = base_chunk_size + 1
        else:
            chunk_size = base_chunk_size
        chunks.append(lst[start_index:start_index + chunk_size])
        start_index += chunk_size

    return chunks


def process(info: Dict):
    """处理单个问题：提取相关子图
    
    对于每个问题：
    1. 从问题中提取种子实体
    2. 获取这些实体的 2-hop 邻域
    3. 使用 PPR 算法排序邻域中的实体
    4. 提取排名前 2000 的实体及其连接关系
    
    Args:
        info: 包含问题信息的字典，需要包含 "entities" 字段
        
    Returns:
        处理后的问题对象，包含提取的子图，如果处理失败返回 None
    """
    try:
        # 从问题中提取种子实体ID列表
        seed_list = [entity["kb_id"] for entity in info["entities"]]
        
        # 获取种子实体的 2-hop 邻域
        subgraph_nodes = get_k_hop_neighbors_optimized(G, seed_list, 2)
        
        # 如果没有邻域节点，跳过该问题
        if len(subgraph_nodes) == 0:
            return None
        
        # 使用 PPR 算法排序邻域中的实体，取前 2000 个
        entities = rank_ppr_ents(G, subgraph_nodes, seed_list, max_ent=2000)
        
        # 从排序后的实体中提取子图
        ppr_subgraph = G.subgraph(entities)
        
        # 深拷贝原始问题对象
        obj = deepcopy(info)
        
        # 将答案ID转换为答案文本
        obj["answers"] = [ans["text"] if ans["text"] else ans["kb_id"]
                          for ans in obj["answers"]]
        
        # 将实体ID转换为实体名称
        obj["entities"] = [ent["text"] if ent["text"] else ent["kb_id"]
                           for ent in obj["entities"]]
        
        # 提取子图的三元组
        obj["subgraph"] = get_triples(ppr_subgraph)
        
        return obj
    except Exception as e:
        print(e)
        return None


def process_data_chunk(args):
    """处理数据块（用于多线程处理）
    
    处理一个数据块中的所有问题，将结果写入输出文件。
    
    Args:
        args: 包含 (data_chunk, out_file_path) 的元组
              - data_chunk: 问题数据行列表
              - out_file_path: 输出文件路径
    """
    data_chunk, out_file_path = args
    t = time()
    
    with open(out_file_path, "w") as output_file:
        for index, line in enumerate(data_chunk):
            # 解析 JSON 行
            info = json.loads(line)
            # 处理问题，提取子图
            obj = process(info)
            # 跳过处理失败的问题
            if obj is None:
                continue
            # 写入输出文件
            output_file.write(json.dumps(obj) + "\n")
            # 每处理 20 个问题打印一次进度
            if index % 20 == 0:
                print(out_file_path, index, ":", time()-t, "s")
    
    # 打印块处理完成时间
    print(out_file_path, ":", time()-t, "s")


def main():
    """主函数：使用 PPR 算法提取知识图谱子图"""
    # ============ 配置参数 ============
    kb_file = "rel_filter.txt"  # 知识图谱文件（三元组）
    in_file = "CWQ/CWQ_step0.jsonl"  # 输入：预处理后的问题数据
    out_file_ppr = "dataset/AAAI/MainExperiment/CWQ/PPR2/test_name.jsonl"  # 输出：包含子图的问题数据
    map_file = "id2name.txt"  # 实体ID到名称的映射文件
    threads = 64  # 使用的线程数
    
    # ============ 初始化 ============
    t = time()
    
    # 加载实体ID到名称的映射
    id2name_dict = {}
    with open(map_file, "r") as fp:
        for line in fp:
            mid, rel, name = line.strip().split('\t')
            id2name_dict[mid] = name

    def id2name(mid):
        """查询实体ID对应的名称"""
        if mid in id2name_dict:
            return id2name_dict[mid]
        else:
            return mid

    # ============ 构建知识图谱 ============
    G = ig.Graph(directed=True)  # 创建有向图
    
    # 从知识图谱文件读取三元组
    with open(kb_file, "r") as fp:
        edges = []
        nodes = set()
        for line in fp:
            head, rel, tail = line.strip().split('\t')
            nodes.add(head)
            nodes.add(tail)
            edges.append((head, tail, rel))

    # 添加节点和边到图中
    G.add_vertices(list(nodes))
    G.add_edges([(edge[0], edge[1]) for edge in edges])
    G.es["name"] = [edge[2] for edge in edges]  # 设置边的关系类型

    # 为每个节点添加标签（实体名称）
    for v in G.vs:
        v["label"] = id2name(v["name"])

    print("prepare:", time()-t, "s")

    # ============ 加载输入数据 ============
    with open(in_file, "r") as fp:
        lines = fp.readlines()

    # 将输入数据分割成多个块用于多线程处理
    data_chunks = chunkify(lines, threads)

    # ============ 多线程处理 ============
    pool = Pool(processes=threads)

    temp_files = []
    args = []
    # 为每个线程准备数据块和输出文件
    for i in range(threads):
        temp_file = f"CWQ/tmp_ppr2000_2/ppr_{i}.tmp"
        temp_files.append(temp_file)
        args.append((data_chunks[i], temp_file))

    # 并行处理所有数据块
    pool.map(process_data_chunk, args)

    # ============ 合并结果 ============
    # 将所有临时文件的结果合并到最终输出文件
    with open(out_file_ppr, "w") as final_file:
        for temp_file in temp_files:
            with open(temp_file, "r") as f:
                for line in f:
                    final_file.write(line)


if __name__ == "__main__":
    main()
