"""配置管理模块"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置管理类"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化配置

        Args:
            config_path: 配置文件路径，支持：
                - 绝对路径：如 "/path/to/config.yaml"
                - 相对路径：会依次在以下位置查找
                  1. 当前工作目录
                  2. 项目根目录（pyproject.toml 所在目录）
                  3. ~/.reasoningbank/config.yaml
        """
        self.config_path = self._resolve_config_path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _resolve_config_path(self, config_path: str) -> Path:
        """
        智能解析配置文件路径

        查找顺序：
        1. 如果是绝对路径且存在，直接使用
        2. 当前工作目录
        3. 项目根目录（从 src/config.py 向上查找 pyproject.toml）
        4. 用户主目录 ~/.reasoningbank/
        """
        path = Path(config_path)

        # 1. 绝对路径直接使用
        if path.is_absolute():
            return path

        # 2. 当前工作目录
        cwd_path = Path.cwd() / config_path
        if cwd_path.exists():
            return cwd_path

        # 3. 项目根目录（向上查找 pyproject.toml）
        # 从当前文件所在目录（src/）开始向上查找
        current_file = Path(__file__).resolve()  # src/config.py
        src_dir = current_file.parent              # src/
        project_root = src_dir.parent              # 项目根目录

        # 验证是否找到项目根目录（检查 pyproject.toml）
        if (project_root / "pyproject.toml").exists():
            project_config = project_root / config_path
            if project_config.exists():
                return project_config

        # 4. 用户主目录
        home_path = Path.home() / ".reasoningbank" / config_path
        if home_path.exists():
            return home_path

        # 如果都没找到，优先使用项目根目录路径（即使不存在，错误信息也更清晰）
        if (project_root / "pyproject.toml").exists():
            return project_root / config_path

        # 最后返回当前工作目录路径
        return cwd_path

    def _load_config(self):
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

        # 替换环境变量
        self._replace_env_variables(self._config)

    def _replace_env_variables(self, config: Any) -> Any:
        """
        递归替换配置中的环境变量

        支持的格式:
        - ${VAR_NAME}           : 必需的环境变量，不存在时抛出异常
        - ${VAR_NAME?}          : 可选的环境变量，不存在时返回空字符串
        - ${VAR_NAME:default}   : 带默认值的环境变量，不存在时使用默认值
        """
        if isinstance(config, dict):
            for key, value in config.items():
                config[key] = self._replace_env_variables(value)
        elif isinstance(config, list):
            return [self._replace_env_variables(item) for item in config]
        elif isinstance(config, str):
            # 替换 ${VAR_NAME} 格式的环境变量
            if config.startswith("${") and config.endswith("}"):
                var_spec = config[2:-1]

                # 支持带默认值: ${VAR_NAME:default_value}
                if ':' in var_spec:
                    var_name, default_value = var_spec.split(':', 1)
                    return os.getenv(var_name, default_value)

                # 支持可选环境变量: ${VAR_NAME?}
                if var_spec.endswith('?'):
                    var_name = var_spec[:-1]
                    return os.getenv(var_name, "")

                # 必需的环境变量
                env_value = os.getenv(var_spec)
                if env_value is None:
                    raise ValueError(f"环境变量未设置: {var_spec}")
                return env_value

        return config

    def get(self, *keys, default=None) -> Any:
        """
        获取配置值

        例如: config.get('llm', 'provider') -> 'dashscope'
        """
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
        return value

    def get_llm_config(self) -> Dict[str, Any]:
        """获取 LLM 配置"""
        provider = self.get('llm', 'provider')
        return {
            'provider': provider,
            **self.get('llm', provider, default={})
        }

    def get_embedding_config(self) -> Dict[str, Any]:
        """获取 Embedding 配置"""
        provider = self.get('embedding', 'provider')
        return {
            'provider': provider,
            **self.get('embedding', provider, default={})
        }

    def get_retrieval_config(self) -> Dict[str, Any]:
        """获取检索配置"""
        strategy = self.get('retrieval', 'strategy')
        return {
            'strategy': strategy,
            'default_top_k': self.get('retrieval', 'default_top_k', default=1),
            'max_top_k': self.get('retrieval', 'max_top_k', default=10),
            'strategy_config': self.get('retrieval', strategy, default={})
        }

    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置"""
        backend = self.get('storage', 'backend')
        return {
            'backend': backend,
            **self.get('storage', backend, default={})
        }

    def get_extraction_config(self) -> Dict[str, Any]:
        """获取记忆提取配置"""
        return self.get('extraction', default={})

    @property
    def all(self) -> Dict[str, Any]:
        """返回完整配置"""
        return self._config


# 全局配置实例
_global_config: Config = None


def load_config(config_path: str = "config.yaml") -> Config:
    """加载全局配置"""
    global _global_config
    _global_config = Config(config_path)
    return _global_config


def get_config() -> Config:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config
