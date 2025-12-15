from abc import ABC, abstractmethod
from utils.Query import Query
from utils.Timer import TimedClass

import inspect
class PreRetrievalModule(ABC, TimedClass):
    """预检索模块基类。

    该模块负责在检索前对原始查询进行处理，例如：
    - 实体识别与链接
    - 构建候选子图/候选节点集合
    - 其他必要的清洗或转换

    子类应实现 `process` 方法，并返回更新后的 `Query` 对象。
    """
    @abstractmethod
    def process(self, query: Query) -> Query:
        """处理查询并返回更新后的 `Query` 对象"""
        pass

    # 便于打印实例化参数，帮助调试
    def __str__(self):
        init_signature = inspect.signature(self.__init__)
        params = init_signature.parameters
        params_str = ', '.join(
            [f"{name}={getattr(self, name)}" for name in params if name != 'self'])
        return f"{self.__class__.__name__}({params_str})"
