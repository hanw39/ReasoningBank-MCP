"""轨迹格式化工具"""
from typing import List, Dict


def format_trajectory(trajectory: List[Dict]) -> str:
    """
    将轨迹列表格式化为可读的文本

    Args:
        trajectory: 轨迹步骤列表，每个步骤包含：
            - step: 步骤序号
            - role: 角色 ("user" | "assistant" | "tool")
            - content: 具体内容
            - metadata: 额外信息（可选）

    Returns:
        格式化的轨迹文本
    """
    if not trajectory:
        return "（空轨迹）"

    lines = []

    for step_data in trajectory:
        step_num = step_data.get("step", "?")
        role = step_data.get("role", "unknown")
        content = step_data.get("content", "")
        metadata = step_data.get("metadata", {})

        # 角色标签
        role_label = {
            "user": "User",
            "assistant": "Assistant",
            "tool": "Tool"
        }.get(role, role.capitalize())

        # 如果是 tool 角色且有工具名称
        if role == "tool" and "tool_name" in metadata:
            tool_name = metadata["tool_name"]
            action_type = metadata.get("action_type", "")
            if action_type:
                role_label = f"Tool - {tool_name} ({action_type})"
            else:
                role_label = f"Tool - {tool_name}"

        # 格式化步骤
        line = f"步骤 {step_num} [{role_label}]: {content}"
        lines.append(line)

    return "\n".join(lines)


def format_memory_for_prompt(memories: List[Dict]) -> str:
    """
    将检索到的记忆格式化为可直接用于 LLM 提示的文本

    Args:
        memories: 记忆项列表

    Returns:
        格式化的提示文本
    """
    if not memories:
        return ""

    prompt = "以下是我从过去与环境的交互中积累的一些记忆项，可能有助于解决任务。当您觉得它们相关时可以使用它们。\n\n"

    for i, mem in enumerate(memories, 1):
        status = "✓ 成功经验" if mem.get("success", True) else "✗ 失败教训"
        prompt += f"**记忆 {i} [{status}] - {mem['title']}**\n"
        prompt += f"{mem['content']}\n\n"

    return prompt.strip()
