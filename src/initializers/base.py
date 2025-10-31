"""组件初始化器基类"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger("reasoning-bank-mcp")


class ComponentInitializer(ABC):
    """组件初始化器基类

    每个组件（如 Storage、LLM、Embedding 等）都应该实现自己的初始化器。
    初始化器负责：
    1. 声明组件名称
    2. 声明依赖的其他组件
    3. 从配置中读取必要的配置项
    4. 执行初始化逻辑
    """

    def __init__(self, config: Any):
        """初始化器构造函数

        Args:
            config: 配置对象
        """
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        """组件名称，用于标识和日志输出"""
        pass

    @property
    def dependencies(self) -> List[str]:
        """依赖的其他组件名称列表，确保按依赖顺序初始化"""
        return []

    @property
    def enabled(self) -> bool:
        """组件是否启用，默认启用。可被子类重写以支持条件初始化"""
        return True

    @abstractmethod
    async def initialize(self, context: Dict[str, Any]) -> Any:
        """执行初始化逻辑

        Args:
            context: 初始化上下文，包含 config 和已初始化的其他组件

        Returns:
            初始化后的组件实例
        """
        pass

    def _get_config(self, context: Dict[str, Any]) -> Any:
        """从上下文获取配置对象"""
        return context.get("config")

    def _get_component(self, context: Dict[str, Any], name: str) -> Optional[Any]:
        """从上下文获取已初始化的组件"""
        return context.get(name)


class InitializerRegistry:
    """初始化器注册表

    负责：
    1. 注册所有组件初始化器
    2. 解析依赖关系
    3. 按正确顺序执行初始化
    4. 管理初始化上下文
    """

    def __init__(self):
        self._initializers: Dict[str, ComponentInitializer] = {}
        self._initialized_components: Dict[str, Any] = {}

    def register(self, initializer: ComponentInitializer):
        """注册一个初始化器"""
        self._initializers[initializer.name] = initializer
        logger.debug(f"已注册初始化器: {initializer.name}")

    def register_many(self, initializers: List[ComponentInitializer]):
        """批量注册初始化器"""
        for initializer in initializers:
            self.register(initializer)

    def auto_register(self, initializer_classes: List[Type[ComponentInitializer]], config: Any):
        """自动注册初始化器类

        Args:
            initializer_classes: 初始化器类列表
            config: 配置对象，将传递给初始化器构造函数
        """
        for initializer_class in initializer_classes:
            initializer = initializer_class(config)
            if initializer.enabled:
                self.register(initializer)
            else:
                logger.info(f"跳过禁用的组件: {initializer.name}")

    async def initialize_all(self, config: Any) -> Dict[str, Any]:
        """按依赖顺序初始化所有组件

        Args:
            config: 配置对象

        Returns:
            所有已初始化的组件字典
        """
        # 初始化上下文
        context = {
            "config": config
        }

        # 拓扑排序，解析依赖顺序
        sorted_names = self._topological_sort()

        # 按顺序初始化
        for name in sorted_names:
            initializer = self._initializers[name]

            logger.info(f"正在初始化 {initializer.name}...")

            try:
                # 执行初始化
                component = await initializer.initialize(context)

                # 保存到上下文
                context[name] = component
                self._initialized_components[name] = component

                logger.info(f"✓ {initializer.name} 初始化完成")

            except Exception as e:
                logger.error(f"✗ {initializer.name} 初始化失败: {e}")
                raise

        return self._initialized_components

    def _topological_sort(self) -> List[str]:
        """拓扑排序，解析依赖关系

        Returns:
            排序后的组件名称列表

        Raises:
            ValueError: 如果存在循环依赖
        """
        # 构建依赖图和入度表
        graph = {}
        in_degree = {}

        # 初始化图结构
        for name, initializer in self._initializers.items():
            graph[name] = initializer.dependencies
            in_degree[name] = 0

        # 计算入度
        for name, deps in graph.items():
            for dep in deps:
                if dep not in self._initializers:
                    raise ValueError(f"组件 '{name}' 依赖的组件 '{dep}' 未注册")
                in_degree[name] = in_degree.get(name, 0) + 1

        # Kahn 算法进行拓扑排序
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # 选择入度为0的节点
            current = queue.pop(0)
            result.append(current)

            # 减少依赖当前节点的其他节点的入度
            for name in self._initializers.keys():
                if current in graph[name]:
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)

        # 检查是否存在循环依赖
        if len(result) != len(self._initializers):
            raise ValueError("存在循环依赖，无法初始化")

        return result

    def get_component(self, name: str) -> Optional[Any]:
        """获取已初始化的组件"""
        return self._initialized_components.get(name)

    def get_all_components(self) -> Dict[str, Any]:
        """获取所有已初始化的组件"""
        return self._initialized_components.copy()
