from utils.Evaluation import eval_acc, eval_f1, eval_hr_topk, eval_hit
from pre_retrieval import PreRetrievalModule
from retrieval import RetrievalModule
from post_retrieval import PostRetrievalModule
from utils.Query import Query
import igraph as ig
from time import time
from dataclasses import dataclass
from config import hr_top_k, max_reasoning_paths
from utils.LLM import LLM
from utils.PromptTemplate import REASONING_INPUT


@dataclass
class RecordPipeline:
    """RecordPipeline：将查询依次经过预检索、检索与后检索模块，并在每一步统计耗时与评估指标。

    Attributes:
        preRetrieval: 预检索模块，负责根据原始问题构建子图、抽取实体等准备工作。
        retrieval: 检索模块，负责在子图上进行推理/路径检索，产生候选推理路径。
        postRetrieval: 后检索模块，负责对候选路径进行重排序、筛选或调用LLM做后处理。
    """
    preRetrieval: PreRetrievalModule
    retrieval: RetrievalModule
    postRetrieval: PostRetrievalModule

    def run(self, query: Query):
        """执行完整流水线。

        参数:
            query (Query): 查询对象，包含问题ID、问题文本、答案集合、初始实体等。

        返回:
            Tuple[Query, dict]: 更新后的 `Query` 对象及结果字典 `res_dict`，后者记录各阶段耗时、评估指标与推理路径等。
        """
        res_dict = {"id": query.qid, "question": query.question,
                    "answers": query.answers, "entities": query.entities}
        # 记录阶段耗时起始时间
        t = time()
        query = self.preRetrieval.process(query)
        res_dict["PreRetrievalModuleTime"] = time()-t

        # region Eval-PreRetrieval  # 评估预检索阶段中答案实体在子图中的覆盖情况
        found_count = 0
        # 遍历标准答案实体，检查是否在子图中出现
        for ans in query.answers:
            try:
                query.subgraph.vs.find(name=ans)
                found_count += 1
            except:
                pass
        print("Eval-PreRetrieval: ACC =",
              f"{found_count}/{len(query.subgraph.vs)}")
        res_dict["PreRetrievalModuleACC"] = f"{found_count}/{len(query.subgraph.vs)}"
        # endregion

        # 记录阶段耗时起始时间
        t = time()
        query = self.retrieval.process(query)
        res_dict["RetrievalModuleTime"] = time()-t

        # region Eval-Retrieval  # 评估检索阶段推理路径的质量
        # 将推理路径对象转换为字符串，便于与标准答案匹配及评估
        paths = [str(path) for path in query.reasoning_paths]
        acc = eval_acc(paths, query.answers)

        f1, acc, recall = eval_f1(paths, query.answers)
        print("Eval-Retrieval: ACC =", acc)
        print("Eval-Retrieval: F1 =", f1)
        print("Eval-Retrieval: Recall =", recall)
        res_dict["RetrievalModuleACC"] = acc
        res_dict["RetrievalModuleF1"] = f1
        res_dict["RetrievalModuleRecall"] = recall
        # endregion

        # 记录阶段耗时起始时间
        t = time()
        query = self.postRetrieval.process(query)
        res_dict["PostRetrievalModuleTime"] = time()-t

        # region Eval-PostRetrieval  # 评估后检索阶段（重排序后）的路径质量
        # 将推理路径对象转换为字符串，便于与标准答案匹配及评估
        paths = [str(path) for path in query.reasoning_paths]
        f1, acc, recall = eval_f1(paths, query.answers)
        hr1 = eval_hr_topk(paths, query.answers, 1)
        hr = eval_hr_topk(paths, query.answers, hr_top_k)

        print("Eval-PostRetrieval: ACC =", acc)
        print("Eval-PostRetrieval: F1 =", f1)
        print("Eval-PostRetrieval: Recall =", recall)
        print(f"Eval-PostRetrieval: HR@{hr_top_k} =", hr)
        res_dict["PostRetrievalModuleACC"] = acc
        res_dict["PostRetrievalModuleF1"] = f1
        res_dict["PostRetrievalModuleRecall"] = recall
        res_dict[f"PostRetrievalModuleHR@{hr_top_k}"] = hr
        res_dict["PostRetrievalModuleHR@1"] = hr1
        # endregion

        # 仅保留最多 `max_reasoning_paths` 条推理路径用于日志输出，避免过长
        reasoning_paths = '\n'.join(
            str(path) for path in query.reasoning_paths[:max_reasoning_paths])
        res_dict["ReasoningPaths"] = reasoning_paths
        return query, res_dict

    # 打印流水线结构，便于调试和日志记录
    def __str__(self):
        return f"Pipeline: {self.preRetrieval} -> {self.retrieval} -> {self.postRetrieval}"
