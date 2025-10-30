"""提示词模板"""


# 成功轨迹提取提示词
EXTRACT_SUCCESS_PROMPT = """你是一个专业的AI经验总结专家。请分析以下成功完成的任务轨迹，并提取可复用的推理策略。

**任务查询：**
{query}

**成功的轨迹：**
{trajectory}

**分析目标：**
1. 成功原因分析：解释该轨迹中关键的推理路径、决策点或信息利用方式，说明为何任务能被成功完成。
2. 抽象可复用策略：从成功行为中提炼出可迁移的思维模式或操作步骤，而非表层动作。
3. 形成记忆项（3条以内）：每条代表一种通用策略或方法论，适合未来相似任务的快速复用。

**输出格式（JSON）：**
```json
{{
  "memories": [
    {{
      "title": "策略标题（5-10字）",
      "description": "一句话说明策略适用的典型场景",
      "content": "详细说明策略的逻辑结构、关键判断点和可执行步骤"
    }}
  ]
}}
```

**注意事项：**
- 聚焦于“如何思考”而不是“做了什么”
- 优先提取体现分解问题、假设验证、信息整合、动态调整等高层推理能力的内容
- 策略要具备跨任务适用性，避免与具体工具、网站或数据源绑定
- 输出应简洁、概念清晰、结构稳定，方便后续自动化学习或知识库吸收
- 避免冗余，每个记忆项应该关注不同的方面

请按照上述格式输出，只输出JSON，不要包含其他内容。
"""


# 失败轨迹提取提示词
EXTRACT_FAILURE_PROMPT = """你是一个专业的AI经验总结专家。请分析以下失败的任务轨迹，并提取教训和预防策略。

**任务查询：**
{query}

**失败的轨迹：**
{trajectory}

**要求：**
1. 反思这个轨迹为何失败
2. 识别导致失败的关键错误或陷阱
3. 提取最多3个记忆项（教训），每个记忆项包含：
   - **标题**：简短描述教训（5-10个字）
   - **描述**：一句话说明这个错误的常见场景
   - **内容**：详细说明错误原因、后果，以及如何避免

**注意事项：**
- 提取的教训应该具有警示作用，帮助避免类似错误
- 避免冗余，每个记忆项应该关注不同的失败原因
- 内容要包含"不要做X，应该做Y"的明确指导

**输出格式（JSON）：**
```json
{{
  "memories": [
    {{
      "title": "教训标题",
      "description": "错误场景描述",
      "content": "详细的错误分析和避免方法"
    }}
  ]
}}
```

请按照上述格式输出，只输出JSON，不要包含其他内容。
"""


# 轨迹判断提示词
JUDGE_TRAJECTORY_PROMPT = """你是一个专业的任务评估专家。请判断以下任务执行是否成功。

**任务查询：**
{query}

**执行轨迹：**
{trajectory}

**判断标准：**
- 是否完成了任务查询中要求的目标
- 最终结果是否准确、完整
- 执行过程是否达到了预期状态

**要求：**
请仔细分析轨迹，判断任务是"成功"还是"失败"，并给出简短的理由。

**输出格式（JSON）：**
```json
{{
  "result": "success",  // "success" 或 "failure"
  "reason": "简短的判断理由（1-2句话）"
}}
```

请按照上述格式输出，只输出JSON，不要包含其他内容。
"""


# 记忆合并提示词
MEMORY_MERGE_PROMPT = """你是一个经验提炼专家。以下是 {len(memories)} 条相似的经验，它们来自同一个AI Agent在不同任务中积累的知识。

{memories_text}

请分析这些经验的**共同模式**，提炼出一条更通用、更深层的经验。

要求：
1. **title**: 5-15字的简洁标题，概括核心策略
2. **description**: 一句话（20-40字）概括适用场景
3. **content**: 详细描述通用策略（200-500字），包括：
   - 这个策略解决什么问题
   - 为什么这样做
   - 如何应用到新场景
   - 需要注意的事项
4. **query**: 提炼出的通用场景描述（可以是"<通用场景：xxx>"格式）
5. **abstraction_level**: 抽象层级
   - 0 = 具体案例（特定问题的解决方案）
   - 1 = 模式识别（一类问题的通用方法）
   - 2 = 原则层面（跨领域的指导原则）

请以JSON格式返回，只返回JSON，不要其他内容：
```json
{{
  "title": "...",
  "description": "...",
  "content": "...",
  "query": "...",
  "abstraction_level": 1
}}
```
"""


def get_extract_prompt(query: str, trajectory: str, success: bool) -> str:
    """
    获取记忆提取提示词

    Args:
        query: 任务查询
        trajectory: 格式化的轨迹文本
        success: 是否成功

    Returns:
        完整的提示词
    """
    template = EXTRACT_SUCCESS_PROMPT if success else EXTRACT_FAILURE_PROMPT
    return template.format(query=query, trajectory=trajectory)


def get_judge_prompt(query: str, trajectory: str) -> str:
    """
    获取轨迹判断提示词

    Args:
        query: 任务查询
        trajectory: 格式化的轨迹文本

    Returns:
        完整的提示词
    """
    return JUDGE_TRAJECTORY_PROMPT.format(query=query, trajectory=trajectory)


def get_merge_prompt(memories_text: str) -> str:
    """
    获取记忆合并提示词

    Args:
        memories_text: 需要合并的记忆项

    Returns:
        完整的提示词
    """
    return MEMORY_MERGE_PROMPT.format(memories_text=memories_text)
