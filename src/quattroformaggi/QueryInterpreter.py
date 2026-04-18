import json
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    query,
)

from models.QuerySpec import QuerySpec

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
WORKFLOW_PATH = PROJECT_ROOT / "agents" / "workflows" / "QueryInterpreter.md"


async def interpret_query(user_query: str) -> QuerySpec:
    schema = json.dumps(QuerySpec.model_json_schema(), indent=2)

    options = ClaudeAgentOptions(
        system_prompt={"type": "file", "path": str(WORKFLOW_PATH)},
        cwd=str(PROJECT_ROOT),
        allowed_tools=["Read"],
        permission_mode="bypassPermissions",
    )

    prompt = (
        "Read all files referenced in your workflow instructions before responding. "
        f"Then interpret this query:\n\n{user_query}\n\n"
        "Respond with a single JSON object matching this schema — no markdown, no explanation:\n"
        f"{schema}"
    )

    parts: list[str] = []

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    parts.append(block.text)

    return QuerySpec.model_validate_json("".join(parts))
