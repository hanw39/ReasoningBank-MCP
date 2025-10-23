# 快速开始指南

## 📦 安装和配置

### 1. 安装依赖

```bash
# 进入项目目录
cd reasoning-bank-mcp

# 安装依赖
pip install -r requirements.txt

# 或者使用 pip install -e . 进行开发安装
pip install -e .
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API Key
nano .env
```

在 `.env` 文件中添加：

```env
# DashScope (通义千问) API Key
DASHSCOPE_API_KEY=your-actual-api-key-here
```

### 3. 测试组件

运行测试脚本验证所有组件是否正常工作：

```bash
python test_components.py
```

你应该看到类似输出：

```
============================================================
测试 1: 配置加载
============================================================
✓ 配置加载成功
  - LLM Provider: dashscope
  - Embedding Provider: dashscope
  - 检索策略: hybrid
  - 存储后端: json

============================================================
测试 2: LLM Provider
============================================================
✓ LLM Provider 初始化成功: dashscope:qwen-plus
  正在测试对话...
  响应: 你好！我是通义千问，由阿里云开发的大型语言模型...

...

✓ 通过: 5/5
✗ 失败: 0/5

🎉 所有组件测试通过！系统已准备就绪。
```

## 🚀 启动 MCP 服务器

### 方式 1: 直接运行

```bash
python -m src.server
```

### 方式 2: 使用 Python 模块

```bash
python -m src
```

服务器启动后，你会看到：

```
2025-10-20 23:00:00 - reasoning-bank-mcp - INFO - 正在加载配置...
2025-10-20 23:00:01 - reasoning-bank-mcp - INFO - 正在初始化存储后端...
2025-10-20 23:00:01 - reasoning-bank-mcp - INFO - 正在初始化 LLM Provider...
2025-10-20 23:00:02 - reasoning-bank-mcp - INFO - 正在初始化 Embedding Provider...
2025-10-20 23:00:02 - reasoning-bank-mcp - INFO - 正在初始化检索策略...
2025-10-20 23:00:03 - reasoning-bank-mcp - INFO - 正在初始化 MCP 工具...
2025-10-20 23:00:03 - reasoning-bank-mcp - INFO - ✓ 服务器组件初始化完成
2025-10-20 23:00:03 - reasoning-bank-mcp - INFO -   - LLM: dashscope:qwen-plus
2025-10-20 23:00:03 - reasoning-bank-mcp - INFO -   - Embedding: dashscope:text-embedding-v3
2025-10-20 23:00:03 - reasoning-bank-mcp - INFO -   - 检索策略: hybrid
2025-10-20 23:00:03 - reasoning-bank-mcp - INFO -   - 存储后端: json
2025-10-20 23:00:03 - reasoning-bank-mcp - INFO - ✓ 服务器已启动，等待连接...
```

## 🔧 在 Claude Desktop 中配置

### 1. 找到配置文件

macOS 配置文件路径：
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### 2. 编辑配置文件

```json
{
  "mcpServers": {
    "reasoning-bank": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/Users/hanw/ai-code/reasoning-bank-mcp",
      "env": {
        "DASHSCOPE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**注意**：
- 将 `cwd` 路径改为你的项目实际路径
- 可以在 `env` 中直接设置 API Key，或者使用项目中的 `.env` 文件

### 3. 重启 Claude Desktop

关闭并重新打开 Claude Desktop 应用。

### 4. 验证连接

在 Claude 对话中，你应该能看到新的工具：
- `retrieve_memory` - 检索相关记忆
- `extract_memory` - 提取并保存记忆

## 💡 使用示例

### 示例 1: 使用记忆辅助任务

与 Claude 对话：

```
用户: 我想在购物网站上找到用户最早的订单日期。

Claude: 让我先检索一下是否有相关的历史经验...
[调用 retrieve_memory 工具]

Claude: 我找到了相关经验！根据过去的成功案例，在查找最早订单时，
不要只查看 "Recent Orders"，需要导航到完整的订单历史页面。

现在让我帮你规划具体步骤...
```

### 示例 2: 保存任务经验

```
用户: 我完成了这个任务，轨迹如下：
1. 点击 Account 菜单
2. 选择 Order History
3. 查看完整订单列表
4. 找到最早订单: 2023-01-15

请保存这次经验。

Claude: 好的，让我提取这次成功经验并保存...
[调用 extract_memory 工具]

Claude: ✓ 已成功提取并保存 3 个记忆项：
1. 完整历史查询策略
2. 导航菜单路径模式
3. 订单列表查看方法

这些经验将在未来类似任务中自动被检索和应用。
```

## 🔍 验证数据

查看保存的记忆：

```bash
# 查看记忆数据库
cat data/memories.json

# 查看嵌入向量（文件较大）
ls -lh data/embeddings.json
```

## ⚙️ 自定义配置

### 修改检索策略

编辑 `config.yaml`：

```yaml
retrieval:
  strategy: "hybrid"  # 或 "cosine"

  hybrid:
    weights:
      semantic: 0.6      # 调整权重
      confidence: 0.2
      success: 0.15
      recency: 0.05
    time_decay_halflife: 30  # 调整时间衰减
```

### 切换 LLM 模型

```yaml
llm:
  provider: "dashscope"
  dashscope:
    chat_model: "qwen-max"  # 使用更强的模型
```

### 使用 OpenAI

```yaml
llm:
  provider: "openai"
  openai:
    api_key: "${OPENAI_API_KEY}"
    chat_model: "gpt-4o-mini"

embedding:
  provider: "openai"
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "text-embedding-3-small"
```

## 🐛 故障排除

### 问题 1: API Key 未设置

```
ValueError: 环境变量未设置: DASHSCOPE_API_KEY
```

**解决方案**：确保 `.env` 文件存在且包含有效的 API Key。

### 问题 2: 依赖包未安装

```
ModuleNotFoundError: No module named 'mcp'
```

**解决方案**：运行 `pip install -r requirements.txt`

### 问题 3: 权限错误

```
PermissionError: [Errno 13] Permission denied: 'data/memories.json'
```

**解决方案**：检查 `data/` 目录权限，或删除后重新创建。

## 📚 更多资源

- [完整文档](README.md)
- [配置说明](config.yaml)
- [实现计划](IMPLEMENTATION_PLAN.md)
- [论文原文](Appendix AExperiment Details.docx)

## 🎉 开始使用

现在你已经准备好使用 ReasoningBank MCP 了！

试试在 Claude 中说：

> "请帮我检索一下关于网页导航的历史经验"

或者：

> "我刚完成了一个任务，请帮我提取经验教训"
