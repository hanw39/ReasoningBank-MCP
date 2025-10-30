"""测试 MCP 工具调用"""
import asyncio
import json


async def test_mcp_tool():
    """模拟 MCP 客户端调用"""
    from src.server import ReasoningBankServer

    # 创建服务器实例
    server = ReasoningBankServer()

    # 初始化
    await server.initialize()

    # 设置处理器
    server.setup_handlers()

    # 模拟工具调用
    arguments = {
        "query": "分析开源深度研究智能体项目",
        "agent_id": "Qoder"
    }

    print("调用 retrieve_memory 工具...")
    print(f"参数: {json.dumps(arguments, ensure_ascii=False)}")

    # 获取处理器并调用
    result = await server.retrieve_tool.execute(**arguments)

    print("\n结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_tool())
        print("\n✓ 测试成功")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
