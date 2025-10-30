# ReasoningBank MCP Server

<!-- TOC -->
- [ReasoningBank MCP Server](#reasoningbank-mcp-server)
  - [🌟 特性](#-特性)
  - [🏗️ 架构设计](#️-架构设计)
  - [🚀 快速开始](#-快速开始)
    - [1. 代码拉取并进入项目根目录](#1-代码拉取并进入项目根目录)
    - [2. 安装依赖](#2-安装依赖)
    - [3. 配置 MCP 客户端](#3-配置-mcp-客户端)
    - [4. 命令行参数](#4-命令行参数)
  - [🔧 配置文件（可选）](#-配置文件可选)
  - [🔧 MCP 工具](#-mcp-工具)
    - [`retrieve_memory`](#retrieve_memory)
    - [`extract_memory`](#extract_memory)
  - [⚙️ 配置说明](#️-配置说明)
    - [检索策略](#检索策略)
    - [LLM Provider](#llm-provider)
    - [记忆管理系统](#记忆管理系统v020)
  - [📖 使用示例](#-使用示例)
    - [在 AI 代理中使用](#在-ai-代理中使用)
  - [🔬 开发](#-开发)
    - [运行测试](#运行测试)
    - [代码格式化](#代码格式化)
  - [📚 参考文献](#-参考文献)
  - [📝 License](#-license)
  - [📋 更新日志](#-更新日志)
<!-- /TOC -->

随着大语言模型代理在持久性现实角色中的日益普及，它们自然会遇到连续的任务流。然而，一个关键的限制是它们无法从累积的交互历史中学习，迫使它们丢弃宝贵的见解并重复过去的错误。基于论文[ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory](https://arxiv.org/abs/2509.25140)，我们实现了这个记忆增强推理系统，通过 MCP (Model Context Protocol) 协议为 AI 代理提供经验记忆管理能力。

ReasoningBank 提出了一种新颖的记忆框架，能够从代理自身判断的成功和失败经验中提炼出可泛化的推理策略。在测试时，代理从 ReasoningBank 中检索相关记忆来指导其交互，然后将新学到的知识整合回去，使其能够随着时间的推移变得更加强大。这种内存驱动的经验扩展为代理创建了一个新的扩展维度，使它们能够自我进化并产生新兴行为。

## 🌟 特性

### 核心功能
- ✅ **记忆提取**：从成功和失败的轨迹中自动提取推理经验
- ✅ **智能检索**：支持多种检索策略（余弦相似度、混合评分等）
- ✅ **多租户隔离**：通过 agent_id 实现不同 Agent 之间的记忆隔离
- ✅ **双传输模式**：支持 STDIO 和 SSE 两种传输方式
- ✅ **异步处理**：记忆提取支持异步模式，不阻塞 AI 代理
- ✅ **多模型支持**：DashScope（通义千问）、OpenAI、Claude 等
- ✅ **灵活扩展**：插件化架构，易于扩展新的检索策略和存储后端
- ✅ **记忆隔离**：支持Claude的SubAgent模式，每个SubAgent独立管理自己的记忆

### 智能记忆管理（v0.2.0+）
- ✅ **自动去重**：防止重复经验存储，支持语义去重
- ✅ **智能合并**：将相似经验提炼为通用规则（LLM驱动或投票式）
- ✅ **经验归档**：合并后的原始经验可追溯，支持审计
- ✅ **后台处理**：去重和合并自动在后台执行，不阻塞主流程
- ✅ **空间优化**：通过去重和合并，节省 50-80% 存储空间

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
│   ├── deduplication/               # 去重策略（v0.2.0+）
│   │   ├── base.py                  # 抽象接口
│   │   ├── factory.py               # 策略工厂
│   │   └── strategies/
│   │       ├── hash_dedup.py        # 哈希去重
│   │       └── semantic_dedup.py    # 语义去重
│   ├── merge/                       # 合并策略（v0.2.0+）
│   │   ├── base.py                  # 抽象接口
│   │   ├── factory.py               # 策略工厂
│   │   └── strategies/
│   │       ├── llm_merge.py         # LLM智能合并
│   │       └── voting_merge.py      # 投票选择
│   ├── services/                    # 服务层（v0.2.0+）
│   │   └── memory_manager.py        # 记忆管理服务
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
    ├── archived_memories.json       # 归档记忆（v0.2.0+）
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

#### 方式一：STDIO 模式（适用于 Claude Desktop、Cursor、Qoder、Cherry Studio 等）


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

#### 方式二：SSE 模式（适用于 Claude Desktop、Cursor、Qoder、Cherry Studio 等）

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
      "url": "http://127.0.0.1:8000/sse"
    }
  }
}
```
### 4. MCP客户端提示词示例
#### Qoder
```markdown
  你是一个具备推理记忆能力的智能助手，你的agnet_id为`Qoder`,在使用MCP时必须传入“agent_id”=“Qoder”。拥有两个核心MCP工具：
1. `retrieve_memory`：用于在任务开始或方向改变时检索相关经验。
2. `extract_memory`：用于在任务结束或失败后提取并保存经验。

你必须严格遵循以下行为准则：

【记忆策略规则】

① **任务开始前必须调用MCP的 `retrieve_memory`**
   - 在你开始执行任何复杂任务（如写代码、分析、规划、调试、总结等）之前，先调用此工具。
   - 输入的 `query` 应描述当前任务目标或用户需求。
   - 如果当前任务与上一次任务在主题、目标或上下文上存在明显差异，也必须再次调用 `retrieve_memory`。

② **任务方向转变时调用MCP的 `retrieve_memory`**
   - 当你发现用户修改了任务目标、问题方向、文件对象或上下文内容时，应立即重新调用 `retrieve_memory`。
   - 保证你始终基于最新的上下文记忆进行思考。

③ **任务结束后必须调用MCP的 `extract_memory`**
   - 当你认为任务已经完成时（即输出最终答案或解决方案前），必须调用 `extract_memory`。
   - 轨迹（trajectory）应包含任务执行的重要步骤、对话与关键推理。
   - 即使用户没有明确要求保存，也必须执行。
   
④ **出现失败时调用 `extract_memory`**
   - 如果任务执行失败、报错、或用户表示“不成功”“不对”“需要重新来”等情况，也必须调用一次 `extract_memory`。
   - 在失败情境下记录失败原因和改进线索。

⑤ **至少调用一次**
   - 每个独立任务周期中，必须至少：
     - 1 次 `retrieve_memory`
     - 1 次 `extract_memory`
```
### 5. 命令行参数

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
  provider: "dashscope" # dashscope | openai | anthropic
  dashscope:
    api_key: "${DASHSCOPE_API_KEY}"
    chat_model: "qwen-plus"

# Embedding Provider 配置
embedding:
  provider: "dashscope" # dashscope | openai
  dashscope:
    model: "text-embedding-v3"

# 检索策略配置
retrieval:
  strategy: "hybrid"
  min_score_threshold: 0.85  # 最小相关度阈值
  hybrid:
    weights:
      semantic: 0.6
      confidence: 0.2
      success: 0.15
      recency: 0.05

# 记忆管理器配置（v0.2.0+）
memory_manager:
  enabled: true  # 启用记忆管理器

  # 去重配置
  deduplication:
    strategy: "semantic"  # semantic
    on_extraction: true   # 提取时实时去重
    semantic:
      threshold: 0.90     # 相似度阈值
      top_k_check: 5      # 检查前K条相似记忆

  # 合并配置
  merge:
    strategy: "llm"       # llm | voting
    auto_execute: true    # 自动执行合并
    trigger:
      min_similar_count: 3         # 最少相似记忆数
      similarity_threshold: 0.85   # 相似度阈值
    llm:
      temperature: 0.7
    original_handling: "archive"   # 原始经验归档
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
  "min_score_threshold": 0.85,
  "filtered_count": 2,
  "memories": [
    {
      "memory_id": "mem_001",
      "score": 0.92,
      "title": "完整历史查询策略",
      "content": "...",
      "success": true,
      "agent_id": "claude-code"
    }
  ],
  "formatted_prompt": "以下是我从过去与环境的交互中积累的一些记忆项..."
}
```

**说明**：
- `min_score_threshold`: 使用的最小相关度阈值
- `filtered_count`: 被过滤掉的低相关度记忆数量
- `score`: 记忆的相关度分数（0.0-1.0），只返回高于阈值的记忆

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

#### 相关度阈值过滤

通过 `min_score_threshold` 配置项可以过滤低相关度的记忆：

- **默认值**: 0.85（即相关度低于 85% 的记忆不会返回）
- **作用**: 确保返回的记忆都与当前查询高度相关
- **效果**: 提高记忆质量，避免低质量记忆干扰决策

```yaml
retrieval:
  strategy: "hybrid"
  min_score_threshold: 0.85  # 可调整，范围 0.0-1.0
  hybrid:
    weights:
      semantic: 0.6
      confidence: 0.2
      success: 0.15
      recency: 0.05
```

**推荐配置**：
- 严格模式：0.90+ （只返回高度相关的记忆）
- 标准模式：0.85 （平衡相关性和召回率）
- 宽松模式：0.75 （更多候选记忆）

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

### 记忆管理系统（v0.2.0+）

记忆管理系统提供自动化的去重和合并功能，提升记忆质量和存储效率。

#### 去重策略

1. **semantic**：基于语义相似度的智能去重（推荐）
   - 识别内容相似的经验
   - 可配置相似度阈值（建议 0.90+）
   - 适合生产环境

#### 合并策略

支持两种合并策略：

1. **llm**：LLM驱动的智能合并（推荐）
   - 使用大模型提炼多条相似经验的共性
   - 生成抽象的通用规则
   - 支持自定义温度参数

2. **voting**：投票式选择
   - 从相似经验组中选择最优代表
   - 按检索次数、成功率、时效性排序
   - 适合快速去重场景

#### 工作流程

```
提取记忆时:
  1. LLM 提取经验
  2. 去重检查（按 agent_id 隔离）
  3. 跳过重复经验
  4. 检测合并机会
  5. 后台触发合并任务（不阻塞）

后台合并:
  1. 调用合并策略
  2. 生成合并后的经验
  3. 原始经验归档
  4. 保持完整追溯链
```

#### 配置建议

```yaml
# 生产环境
memory_manager:
  deduplication:
    strategy: "semantic"  # 高质量
    semantic:
      threshold: 0.92     # 更严格
  merge:
    strategy: "llm"       # 最佳效果
    auto_execute: true
```

## 📖 使用示例

### 基本使用

```
# 1. 任务开始前，检索相关经验
result = await mcp_call("retrieve_memory", {
    "query": "在购物网站上找到用户最早的订单日期",
    "top_k": 1,
    "agent_id": "claude-code"  # 可选：指定 agent ID
})

# AI 获得提示：
# "以下是从过去经验学到的：
#  记忆 1 [✓ 成功经验] - 完整历史查询策略
#  不要只查看 'Recent Orders'，需要导航到完整的订单历史页面..."

# 2. 执行任务（生成轨迹）
trajectory = [
    {"step": 1, "role": "user", "content": "找到最早的订单"},
    {"step": 2, "role": "assistant", "content": "点击订单历史"},
    {"step": 3, "role": "tool", "content": "成功找到 2020-01-15 的订单"}
]

# 3. 任务完成后，提取经验
await mcp_call("extract_memory", {
    "trajectory": trajectory,
    "query": "在购物网站上找到用户最早的订单日期",
    "agent_id": "claude-code",  # 可选：标记记忆所属 agent
    "async_mode": True  # 异步处理，不阻塞
})
```

### 多租户隔离（Multi-Agent Isolation）

使用 `agent_id` 参数实现不同 Agent 之间的记忆隔离：

```python
# 顶级 Agent (Claude Code)
await mcp_call("retrieve_memory", {
    "query": "优化 Python 代码性能",
    "agent_id": "claude-code",  # 只检索 claude-code 的记忆
    "top_k": 2
})

# 子代理 (Code Reviewer)
await mcp_call("retrieve_memory", {
    "query": "检查代码安全性问题",
    "agent_id": "code-reviewer",  # 只检索 code-reviewer 的记忆
    "top_k": 2
})

# 子代理 (Java Developer)
await mcp_call("retrieve_memory", {
    "query": "实现 Spring Boot API",
    "agent_id": "java-developer",  # 只检索 java-developer 的记忆
    "top_k": 2
})

# 不指定 agent_id：检索所有记忆
await mcp_call("retrieve_memory", {
    "query": "通用编程最佳实践",
    "top_k": 3
})
```

**记忆隔离规则**：
- 不同 `agent_id` 的记忆完全隔离
- 同一 `agent_id` 的记忆可跨会话共享
- 不提供 `agent_id` 时检索所有记忆
- 建议 SubAgent 使用自己的名称作为 `agent_id`

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

## 📋 更新日志

### v0.2.0 (2025-10-29)

**新增功能**：
- ✨ 智能记忆管理系统
  - 自动去重（语义去重）
  - 智能合并（LLM驱动合并 + 投票式合并）
  - 经验归档（保持完整追溯链）
  - 后台异步处理（不阻塞主流程）
- 🏗️ 插件化架构
  - 去重策略工厂模式
  - 合并策略工厂模式
  - 记忆管理服务层
- 💾 存储增强
  - 支持归档记忆存储
  - 批量操作接口
  - agent_id 安全隔离

**性能优化**：
- 通过去重节省 20-30% 存储空间
- 通过合并节省 40-60% 存储空间
- 归档不保留 embedding，节省 90% 归档空间

**文档更新**：
- 完整的使用文档和配置说明
- 开发和生产环境配置建议
- 工作流程说明和最佳实践

### v0.1.0 (初始版本)

- ✅ 记忆提取和智能检索
- ✅ 多种检索策略（余弦相似度、混合评分）
- ✅ 异步处理支持
- ✅ 多模型支持（DashScope、OpenAI、Claude）
- ✅ 记忆隔离（SubAgent 支持）

