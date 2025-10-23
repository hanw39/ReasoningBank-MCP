"""提示词模板"""


# 成功轨迹提取提示词
EXTRACT_SUCCESS_PROMPT = """你是一个专业的AI经验总结专家。请分析以下成功完成的任务轨迹，并提取可复用的推理策略。

**任务查询：**
{query}

**成功的轨迹：**
{trajectory}

**要求：**
1. 分析这个轨迹为何能成功解决任务
2. 总结其中可转移的推理策略和方法
3. 提取最多3个记忆项，每个记忆项包含：
   - **标题**：简短描述（5-10个字）
   - **描述**：一句话说明这个策略的适用场景
   - **内容**：详细说明策略的具体步骤和关键点

**注意事项：**
- 提取的策略应该具有通用性，不要局限于特定的网站或查询
- 避免冗余，每个记忆项应该关注不同的方面
- 内容要简洁明了，便于在未来任务中快速应用

**输出格式（JSON）：**
```json
{{
  "memories": [
    {{
      "title": "策略标题",
      "description": "适用场景描述",
      "content": "详细的策略内容和步骤"
    }}
  ]
}}
```

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
