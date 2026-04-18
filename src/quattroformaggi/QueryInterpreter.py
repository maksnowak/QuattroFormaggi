import json
from pathlib import Path

import anthropic

from models.QuerySpec import QuerySpec

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "prompts" / "QueryInterpreter.md"


async def interpret_query(user_query: str) -> QuerySpec:
    system_prompt = SYSTEM_PROMPT_PATH.read_text()
    schema = json.dumps(QuerySpec.model_json_schema(), indent=2)

    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Interpret this query:\n\n{user_query}\n\n"
                    "Respond with a single JSON object matching this schema — no markdown, no explanation:\n"
                    f"{schema}"
                ),
            }
        ],
    )

    text = next(
        block.text for block in message.content if isinstance(block, anthropic.types.TextBlock)
    ).strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return QuerySpec.model_validate_json(text)
