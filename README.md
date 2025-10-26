# ReasoningBank MCP Server

基于论文ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory[https://arxiv.org/abs/2509.25140] 实现的记忆增强推理系统，通过 MCP (Model Context Protocol) 协议为 AI 代理提供经验记忆管理能力。

## 🌟 特性

- ✅ **记忆提取**：从成功和失败的轨迹中自动提取推理经验
- ✅ **智能检索**：支持多种检索策略（余弦相似度、混合评分等）
- ✅ **异步处理**：记忆提取支持异步模式，不阻塞 AI 代理
- ✅ **多模型支持**：DashScope（通义千问）、OpenAI、Claude 等
- ✅ **灵活扩展**：插件化架构，易于扩展新的检索策略和存储后端

## 🏗️ 架构设计

```
reasoning-bank-mcp/
├── src/
│   ├── server.py                    # MCP 服务器入口
│   ├── config.py                    # 配置管理
│   ├── tools/                       # MCP 工具
│   │   ├── retrieve_memory.py       # 检索记忆
│   │   └── extract_memory.py        # 提取记忆
│   ├── retrieval/                   # 检索策略
│   │   ├── base.py                  # 抽象接口
│   │   ├── factory.py               # 策略工厂
│   │   └── strategies/              # 具体策略实现
│   ├── storage/                     # 存储后端
│   │   ├── base.py                  # 抽象接口
│   │   └── backends/                # 具体存储实现
│   ├── llm/                         # LLM 客户端
│   │   ├── base.py                  # 抽象接口
│   │   ├── factory.py               # Provider 工厂
│   │   └── providers/               # 具体 Provider 实现
│   ├── prompts/                     # 提示词模板
│   └── utils/                       # 工具函数
└── data/                            # 数据存储目录
    ├── memories.json                # 记忆数据库
    └── embeddings.json              # 嵌入向量
```

## 🚀 快速开始

### 1. 代码拉取并进入项目根目录
```bash
git clone https://github.com/hanw39/ReasoningBank-MCP.git
cd ReasoningBank-MCP
```

### 2. 安装依赖

```bash
pip install -e .
```

### 3. 配置 MCP 客户端

#### 方式一：STDIO 模式（适用于 Claude Desktop）

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "reasoning-bank": {
      "command": "reasoning-bank-mcp",
      "env": {
        "DASHSCOPE_API_KEY": "你的百炼APIKEY"
      }
    }
  }
}
```

#### 方式二：SSE 模式（适用于 Qoder、Cherry Studio 等）

**1) 启动服务器**：
```bash
# 使用默认配置 (127.0.0.1:8000)
python3 -m src.server --transport sse

# 或指定主机和端口
python3 -m src.server --transport sse --host 0.0.0.0 --port 8080
```

**2) 客户端配置**：
```json
{
  "mcpServers": {
    "reasoning-bank": {
      "url": "http://127.0.0.1:8000/sse",
      "env": {
        "DASHSCOPE_API_KEY": "你的百炼APIKEY"
      }
    }
  }
}
```

### 4. 命令行参数

```bash
python3 -m src.server --help

# 可用参数：
# --transport {stdio,sse}  传输方式 (默认: stdio)
# --host HOST              SSE 模式的主机地址 (默认: 127.0.0.1)
# --port PORT              SSE 模式的端口号 (默认: 8000)
```


## 🔧 配置文件（可选）

如果需要自定义配置，可以编辑 `config.yaml`：

```yaml
# LLM Provider 配置
llm:
  provider: "dashscope"
  dashscope:
    api_key: "${DASHSCOPE_API_KEY}"
    chat_model: "qwen-plus"

# Embedding Provider 配置
embedding:
  provider: "dashscope"
  dashscope:
    model: "text-embedding-v3"

# 检索策略配置
retrieval:
  strategy: "hybrid"
  hybrid:
    weights:
      semantic: 0.6
      confidence: 0.2
      success: 0.15
      recency: 0.05
```

## 🔧 MCP 工具

### `retrieve_memory`

检索相关的历史经验记忆，帮助指导当前任务的执行。

**参数**：
- `query` (string, 必填): 当前任务的查询描述
- `top_k` (number, 可选): 检索的记忆数量，默认 1
- `agent_id` (string, 可选): Agent ID，用于多租户隔离
  - 只检索指定 agent 的记忆
  - 不提供时检索所有记忆
  - 建议 SubAgent 传递自己的 name 作为 agent_id
  - 例如：`"claude-code"`、`"code-reviewer"` 等

**返回**：
```json
{
  "status": "success",
  "memories": [
    {
      "memory_id": "mem_001",
      "score": 0.85,
      "title": "完整历史查询策略",
      "content": "...",
      "success": true,
      "agent_id": "claude-code"
    }
  ],
  "formatted_prompt": "以下是我从过去与环境的交互中积累的一些记忆项..."
}
```

### `extract_memory`

从任务轨迹中提取推理经验并保存到记忆库。

**参数**：
- `trajectory` (array, 必填): 任务执行的轨迹步骤列表
  - 每个步骤包含: `step` (number), `role` (string), `content` (string), `metadata` (object, 可选)
- `query` (string, 必填): 任务查询描述
- `success_signal` (boolean, 可选): 任务是否成功，null 时自动判断
- `async_mode` (boolean, 可选): 是否异步处理，默认 true
- `agent_id` (string, 可选): Agent ID，用于多租户隔离
  - 标记记忆属于哪个 agent
  - 建议 SubAgent 传递自己的 name 作为 agent_id
  - 例如：`"claude-code"`、`"java-developer"` 等

**返回**（异步模式）：
```json
{
  "status": "processing",
  "message": "记忆提取任务已提交，正在后台处理",
  "task_id": "extract_12345",
  "async_mode": true
}
```

**返回**（同步模式）：
```json
{
  "status": "success",
  "message": "记忆提取成功",
  "memory_id": "mem_123",
  "agent_id": "claude-code"
}
```

## ⚙️ 配置说明

### 检索策略

支持两种检索策略：

1. **cosine**：纯余弦相似度（论文基线方法）
2. **hybrid**：混合评分（推荐）
   - 语义相似度 (60%)
   - 置信度 (20%)
   - 成功偏好 (15%)
   - 时效性 (5%)

```yaml
retrieval:
  strategy: "hybrid"
  hybrid:
    weights:
      semantic: 0.6
      confidence: 0.2
      success: 0.15
      recency: 0.05
```

### LLM Provider

支持多种模型 API：

- **dashscope**：通义千问（推荐）
- **openai**：OpenAI 或兼容 API
- **anthropic**：Claude

```yaml
llm:
  provider: "dashscope"
  dashscope:
    api_key: "${DASHSCOPE_API_KEY}"
    chat_model: "qwen-plus"

embedding:
  provider: "dashscope"
  dashscope:
    model: "text-embedding-v3"
```

## 📖 使用示例

### 在 AI 代理中使用

```python
# 1. 任务开始前，检索相关经验
result = await mcp_call("retrieve_memory", {
    "query": "在购物网站上找到用户最早的订单日期",
    "top_k": 1
})

# AI 获得提示：
# "以下是从过去经验学到的：
#  记忆 1 [✓ 成功经验] - 完整历史查询策略
#  不要只查看 'Recent Orders'，需要导航到完整的订单历史页面..."

# 2. 执行任务（生成轨迹）
trajectory = [...]

# 3. 任务完成后，提取经验
await mcp_call("extract_memory", {
    "trajectory": trajectory,
    "query": query,
    "async_mode": True  # 异步处理，不阻塞
})
```

## 🔬 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black src/
ruff check src/
```

## 📚 参考文献

基于论文：**ReasoningBank: Memory as Test-Time Compute Scaling**

- 论文核心思想：从成功和失败经验中提取推理模式
- 检索机制：基于语义嵌入的相似度检索
- 扩展点：支持更高级的检索策略和存储后端

## 📝 License

MIT License
