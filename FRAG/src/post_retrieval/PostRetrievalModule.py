from abc import ABC, abstractmethod
from utils.Query import Query
from utils.Timer import TimedClass
import inspect
from utils.ReasoningPath import ReasoningPath
from typing import List, Dict


class PostRetrievalModule(ABC, TimedClass):
    """后检索模块基类。

    该模块对检索阶段生成的候选推理路径进行后处理，例如：
    - 评分与重排序
    - 过滤无效路径
    - 调用大型语言模型（LLM）进行答案抽取或链路评估

    子类需实现 `_process` 与 `process` 方法。
    """
    @abstractmethod
    def process(self, query: Query) -> Query:
        """处理查询并返回更新后的 `Query` 对象"""
        pass

    @abstractmethod
    def _process(self, query: Query) -> List[ReasoningPath]:
        """核心处理逻辑，返回处理后的 `ReasoningPath` 列表"""
        pass

    # 打印实例化参数，便于调试
    def __str__(self):
        init_signature = inspect.signature(self.__init__)
        params = init_signature.parameters
        params_str = ', '.join(
            [f"{name}={getattr(self, name)}" for name in params if name != 'self'])
        return f"{self.__class__.__name__}({params_str})"
