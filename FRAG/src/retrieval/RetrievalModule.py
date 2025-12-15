from abc import ABC, abstractmethod
from utils.Query import Query
import inspect

from utils.Timer import TimedClass


class RetrievalModule(ABC, TimedClass):
    """检索模块基类。

    该模块在预检索生成的子图范围内执行路径/答案检索，
    输出候选推理路径（ReasoningPath）集合，并更新 `Query` 对象。

    子类应实现 `process` 方法。
    """
    @abstractmethod
    def process(self, query: Query) -> Query:
        """处理查询并返回更新后的 `Query` 对象"""
        pass

    # 打印实例化参数，便于调试
    def __str__(self):
        init_signature = inspect.signature(self.__init__)
        params = init_signature.parameters
        params_str = ', '.join(
            [f"{name}={getattr(self, name)}" for name in params if name != 'self'])
        return f"{self.__class__.__name__}({params_str})"
