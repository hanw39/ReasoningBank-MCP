"""MCP 服务器入口点"""
import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())
