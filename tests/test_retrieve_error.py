"""测试脚本：重现 retrieve_memory 错误"""
import asyncio
import sys
import traceback


async def test_retrieve():
    """测试记忆检索"""
    try:
        from src.config import load_config
        from src.storage import StorageFactory
        from src.llm import EmbeddingFactory
        from src.retrieval import RetrievalFactory
        from src.tools import RetrieveMemoryTool

        print("加载配置...")
        config = load_config()

        print("初始化存储后端...")
        storage_config = config.get_storage_config()
        storage = StorageFactory.create(storage_config)

        print("初始化 Embedding Provider...")
        embedding_config = config.get_embedding_config()
        embedding = EmbeddingFactory.create(embedding_config)

        print("初始化检索策略...")
        retrieval_config = config.get_retrieval_config()
        retrieval = RetrievalFactory.create(
            retrieval_config["strategy"],
            retrieval_config.get("strategy_config")
        )

        print("创建检索工具...")
        retrieve_tool = RetrieveMemoryTool(
            config,
            storage,
            embedding,
            retrieval
        )

        print("执行检索...")
        result = await retrieve_tool.execute(
            query="分析开源深度研究智能体项目",
            agent_id="Qoder"
        )

        print("检索结果:")
        print(result)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        print("\n完整错误堆栈:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_retrieve())
