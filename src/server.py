"""ReasoningBank MCP 服务器"""
import asyncio
import logging
import argparse
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import Response
import uvicorn

from .config import load_config
from .llm import LLMFactory, EmbeddingFactory
from .storage import StorageFactory
from .retrieval import RetrievalFactory
from .tools import RetrieveMemoryTool, ExtractMemoryTool

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("reasoning-bank-mcp")


class ReasoningBankServer:
    """ReasoningBank MCP 服务器"""

    def __init__(self):
        self.config = None
        self.storage = None
        self.llm = None
        self.embedding = None
        self.retrieval = None
        self.retrieve_tool = None
        self.extract_tool = None
        self.server = Server("reasoning-bank")

    async def initialize(self):
        """初始化服务器组件"""
        try:
            # 1. 加载配置
            logger.info("正在加载配置...")
            self.config = load_config()

            # 2. 初始化存储后端
            logger.info("正在初始化存储后端...")
            storage_config = self.config.get_storage_config()
            self.storage = StorageFactory.create(storage_config)

            # 3. 初始化 LLM Provider
            logger.info("正在初始化 LLM Provider...")
            llm_config = self.config.get_llm_config()
            self.llm = LLMFactory.create(llm_config)

            # 4. 初始化 Embedding Provider
            logger.info("正在初始化 Embedding Provider...")
            embedding_config = self.config.get_embedding_config()
            self.embedding = EmbeddingFactory.create(embedding_config)

            # 5. 初始化检索策略
            logger.info("正在初始化检索策略...")
            retrieval_config = self.config.get_retrieval_config()
            self.retrieval = RetrievalFactory.create(
                retrieval_config["strategy"],
                retrieval_config.get("strategy_config")
            )

            # 6. 初始化工具
            logger.info("正在初始化 MCP 工具...")
            self.retrieve_tool = RetrieveMemoryTool(
                self.config,
                self.storage,
                self.embedding,
                self.retrieval
            )

            self.extract_tool = ExtractMemoryTool(
                self.config,
                self.storage,
                self.llm,
                self.embedding
            )

            logger.info("✓ 服务器组件初始化完成")
            logger.info(f"  - LLM: {self.llm.get_provider_name()}")
            logger.info(f"  - Embedding: {self.embedding.get_provider_name()}")
            logger.info(f"  - 检索策略: {self.retrieval.get_name()}")
            logger.info(f"  - 存储后端: {storage_config.get('backend', 'json')}")

        except Exception as e:
            logger.error(f"✗ 服务器初始化失败: {e}")
            raise

    def setup_handlers(self):
        """设置 MCP 处理器"""
        # todo 描述得强制些吧 JSON是不是得放在相对路径
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """列出可用的工具"""
            return [
                Tool(
                    name="retrieve_memory",
                    description="检索相关的历史经验记忆，帮助指导当前任务的执行。在开始执行任何复杂任务前都应该先调用此工具来获取相关经验。例如：编写代码、数据分析、制定计划等任务前。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "当前任务的查询描述"
                            },
                            "top_k": {
                                "type": "number",
                                "description": "检索的记忆数量（可选，默认1）",
                                "default": 1
                            },
                            "agent_id": {
                                "type": "string",
                                "description": "Agent ID（可选）。用于多租户隔离，只检索指定 agent 的记忆。不提供时检索所有记忆。建议 SubAgent 传递自己的 name 作为 agent_id。"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="extract_memory",
                    description="从任务轨迹中提取推理经验并保存到记忆库。当任务执行完成后必须调用此工具，以便将经验保存供未来使用。这应该在每次任务结束时调用。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "trajectory": {
                                "type": "array",
                                "description": "任务执行的轨迹步骤列表",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "step": {"type": "number"},
                                        "role": {"type": "string", "enum": ["user", "assistant", "tool"]},
                                        "content": {"type": "string"},
                                        "metadata": {"type": "object"}
                                    },
                                    "required": ["step", "role", "content"]
                                }
                            },
                            "query": {
                                "type": "string",
                                "description": "任务查询描述"
                            },
                            "success_signal": {
                                "type": "boolean",
                                "description": "任务是否成功（可选，null时自动判断）"
                            },
                            "async_mode": {
                                "type": "boolean",
                                "description": "是否异步处理（可选，默认true）"
                            },
                            "agent_id": {
                                "type": "string",
                                "description": "Agent ID（可选）。用于多租户隔离，标记记忆属于哪个 agent。建议 SubAgent 传递自己的 name 作为 agent_id。"
                            }
                        },
                        "required": ["trajectory", "query"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """调用工具"""
            try:
                if name == "retrieve_memory":
                    result = await self.retrieve_tool.execute(
                        query=arguments["query"],
                        top_k=arguments.get("top_k"),
                        agent_id=arguments.get("agent_id")
                    )
                elif name == "extract_memory":
                    result = await self.extract_tool.execute(
                        trajectory=arguments["trajectory"],
                        query=arguments["query"],
                        success_signal=arguments.get("success_signal"),
                        async_mode=arguments.get("async_mode"),
                        agent_id=arguments.get("agent_id")
                    )
                else:
                    result = {"status": "error", "message": f"Unknown tool: {name}"}

                # 返回格式化的结果
                import json
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]

            except Exception as e:
                logger.error(f"工具调用失败 [{name}]: {e}", exc_info=True)
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": f"工具执行出错: {str(e)}"
                    }, ensure_ascii=False, indent=2)
                )]

    async def run_stdio(self):
        """使用 STDIO 运行服务器"""
        logger.info("正在启动 ReasoningBank MCP 服务器 (STDIO 模式)...")

        # 初始化组件
        await self.initialize()

        # 设置处理器
        self.setup_handlers()

        # 启动服务器
        logger.info("✓ 服务器已启动，等待连接...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

    async def run_sse(self, host: str = "127.0.0.1", port: int = 8000):
        """使用 SSE 运行服务器"""
        logger.info(f"正在启动 ReasoningBank MCP 服务器 (SSE 模式) 在 {host}:{port}...")

        # 初始化组件
        await self.initialize()

        # 设置处理器
        self.setup_handlers()

        # 创建 SSE 传输层
        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            """处理 SSE 连接"""
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await self.server.run(
                    streams[0], streams[1], self.server.create_initialization_options()
                )
            return Response()

        # 创建 Starlette 应用
        app = Starlette(
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ]
        )

        logger.info("✓ 服务器已启动，等待连接...")
        logger.info(f"  SSE 端点: http://{host}:{port}/sse")

        # 运行服务器
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="ReasoningBank MCP 服务器")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="传输方式: stdio (默认) 或 sse"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="SSE 模式的主机地址 (默认: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="SSE 模式的端口号 (默认: 8000)"
    )

    args = parser.parse_args()

    server = ReasoningBankServer()

    if args.transport == "stdio":
        await server.run_stdio()
    else:  # sse
        await server.run_sse(host=args.host, port=args.port)


def run_server():
    """运行服务器的同步入口点"""
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    run_server()
