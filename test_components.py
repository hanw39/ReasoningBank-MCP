"""简单的测试脚本 - 测试核心组件"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_config
from src.llm import LLMFactory, EmbeddingFactory
from src.storage import StorageFactory
from src.retrieval import RetrievalFactory


async def test_config():
    """测试配置加载"""
    print("=" * 60)
    print("测试 1: 配置加载")
    print("=" * 60)

    try:
        config = load_config()
        print("✓ 配置加载成功")
        print(f"  - LLM Provider: {config.get('llm', 'provider')}")
        print(f"  - Embedding Provider: {config.get('embedding', 'provider')}")
        print(f"  - 检索策略: {config.get('retrieval', 'strategy')}")
        print(f"  - 存储后端: {config.get('storage', 'backend')}")
        return config
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return None


async def test_llm(config):
    """测试 LLM Provider"""
    print("\n" + "=" * 60)
    print("测试 2: LLM Provider")
    print("=" * 60)

    try:
        llm_config = config.get_llm_config()
        llm = LLMFactory.create(llm_config)
        print(f"✓ LLM Provider 初始化成功: {llm.get_provider_name()}")

        # 测试简单对话
        print("  正在测试对话...")
        response = await llm.chat([
            {"role": "user", "content": "请用一句话介绍你自己"}
        ])
        print(f"  响应: {response[:100]}...")
        return llm
    except Exception as e:
        print(f"✗ LLM Provider 测试失败: {e}")
        return None


async def test_embedding(config):
    """测试 Embedding Provider"""
    print("\n" + "=" * 60)
    print("测试 3: Embedding Provider")
    print("=" * 60)

    try:
        embedding_config = config.get_embedding_config()
        embedding = EmbeddingFactory.create(embedding_config)
        print(f"✓ Embedding Provider 初始化成功: {embedding.get_provider_name()}")
        print(f"  嵌入维度: {embedding.get_embedding_dim()}")

        # 测试嵌入
        print("  正在测试嵌入...")
        vec = await embedding.embed("这是一个测试文本")
        print(f"  嵌入向量长度: {len(vec)}")
        print(f"  前5个值: {vec[:5]}")
        return embedding
    except Exception as e:
        print(f"✗ Embedding Provider 测试失败: {e}")
        return None


async def test_storage(config):
    """测试存储后端"""
    print("\n" + "=" * 60)
    print("测试 4: 存储后端")
    print("=" * 60)

    try:
        storage_config = config.get_storage_config()
        storage = StorageFactory.create(storage_config)
        print("✓ 存储后端初始化成功")

        # 获取统计信息
        stats = await storage.get_stats()
        print(f"  记忆总数: {stats['total_count']}")
        print(f"  成功记忆: {stats['success_count']}")
        print(f"  失败记忆: {stats['failure_count']}")
        return storage
    except Exception as e:
        print(f"✗ 存储后端测试失败: {e}")
        return None


async def test_retrieval(config):
    """测试检索策略"""
    print("\n" + "=" * 60)
    print("测试 5: 检索策略")
    print("=" * 60)

    try:
        retrieval_config = config.get_retrieval_config()
        retrieval = RetrievalFactory.create(
            retrieval_config["strategy"],
            retrieval_config.get("strategy_config")
        )
        print(f"✓ 检索策略初始化成功: {retrieval.get_name()}")
        return retrieval
    except Exception as e:
        print(f"✗ 检索策略测试失败: {e}")
        return None


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("ReasoningBank MCP 组件测试")
    print("=" * 60)

    # 测试配置
    config = await test_config()
    if not config:
        print("\n✗ 配置测试失败，终止后续测试")
        return

    # 测试 LLM
    llm = await test_llm(config)

    # 测试 Embedding
    embedding = await test_embedding(config)

    # 测试存储
    storage = await test_storage(config)

    # 测试检索
    retrieval = await test_retrieval(config)

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    success_count = sum([
        config is not None,
        llm is not None,
        embedding is not None,
        storage is not None,
        retrieval is not None
    ])
    print(f"✓ 通过: {success_count}/5")
    print(f"✗ 失败: {5 - success_count}/5")

    if success_count == 5:
        print("\n🎉 所有组件���试通过！系统已准备就绪。")
        print("\n下一步:")
        print("  1. 运行 'python -m src.server' 启动 MCP 服务器")
        print("  2. 在 Claude Desktop 中配置 MCP 服务器")
    else:
        print("\n⚠️  部分组件测试失败，请检查配置和环境。")


if __name__ == "__main__":
    asyncio.run(main())
