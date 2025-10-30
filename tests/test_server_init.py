"""
测试服务器初始化

验证所有组件能否正常加载
"""
import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_server_initialization():
    """测试服务器初始化"""
    print("=" * 60)
    print("测试服务器初始化")
    print("=" * 60)

    try:
        from src.config import load_config
        from src.llm import LLMFactory, EmbeddingFactory
        from src.storage import StorageFactory
        from src.retrieval import RetrievalFactory
        from src.deduplication import DeduplicationFactory
        from src.merge import MergeFactory
        from src.services import MemoryManager

        print("\n✓ 所有模块导入成功")

        # 1. 加载配置
        print("\n1. 加载配置...")
        config = load_config()
        print(f"   ✓ 配置加载成功")
        print(f"   - LLM Provider: {config.get('llm', 'provider')}")
        print(f"   - Embedding Provider: {config.get('embedding', 'provider')}")
        print(f"   - Storage Backend: {config.get('storage', 'backend')}")
        print(f"   - Memory Manager: {config.get('memory_manager', 'enabled', default=True)}")

        # 2. 初始化存储
        print("\n2. 初始化存储后端...")
        storage_config = config.get_storage_config()
        storage = StorageFactory.create(storage_config)
        print(f"   ✓ 存储后端初始化成功")

        # 3. 初始化 LLM
        print("\n3. 初始化 LLM Provider...")
        llm_config = config.get_llm_config()
        llm = LLMFactory.create(llm_config)
        print(f"   ✓ LLM Provider: {llm.get_provider_name()}")

        # 4. 初始化 Embedding
        print("\n4. 初始化 Embedding Provider...")
        embedding_config = config.get_embedding_config()
        embedding = EmbeddingFactory.create(embedding_config)
        print(f"   ✓ Embedding Provider: {embedding.get_provider_name()}")

        # 5. 初始化检索策略
        print("\n5. 初始化检索策略...")
        retrieval_config = config.get_retrieval_config()
        retrieval = RetrievalFactory.create(
            retrieval_config["strategy"],
            retrieval_config.get("strategy_config")
        )
        print(f"   ✓ 检索策略: {retrieval.get_name()}")

        # 注入 retrieval_strategy
        storage.retrieval_strategy = retrieval
        print(f"   ✓ 检索策略已注入到存储后端")

        # 6. 初始化记忆管理器
        if config.get("memory_manager", "enabled", default=True):
            print("\n6. 初始化记忆管理器...")

            # 创建去重策略
            dedup_strategy = DeduplicationFactory.create(config.all)
            print(f"   ✓ 去重策略: {dedup_strategy.name}")

            # 创建合并策略
            merge_strategy = MergeFactory.create(config.all)
            print(f"   ✓ 合并策略: {merge_strategy.name}")

            # 创建管理器
            memory_manager = MemoryManager(
                storage_backend=storage,
                dedup_strategy=dedup_strategy,
                merge_strategy=merge_strategy,
                embedding_provider=embedding,
                llm_provider=llm,
                config=config.all
            )
            print(f"   ✓ 记忆管理器初始化成功")
        else:
            print("\n6. 记忆管理器已禁用")
            memory_manager = None

        print("\n" + "=" * 60)
        print("✅ 所有组件初始化成功！")
        print("=" * 60)

        # 显示配置摘要
        print("\n配置摘要:")
        print(f"  - LLM: {llm.get_provider_name()}")
        print(f"  - Embedding: {embedding.get_provider_name()}")
        print(f"  - 检索策略: {retrieval.get_name()}")
        print(f"  - 存储后端: {storage_config.get('backend', 'json')}")
        if memory_manager:
            print(f"  - 去重策略: {dedup_strategy.name}")
            print(f"  - 合并策略: {merge_strategy.name}")
            print(f"  - 记忆管理: 已启用")
        else:
            print(f"  - 记忆管理: 已禁用")

        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ 初始化失败")
        print("=" * 60)
        print(f"\n错误信息: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_server_initialization())
    sys.exit(0 if success else 1)
