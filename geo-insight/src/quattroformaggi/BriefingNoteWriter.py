from pathlib import Path

import anthropic

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "prompts" / "BriefingNoteWriter.md"


async def brief_writer(
    data_as_csv: str, message: str, articles:str, interpretation_notes: str | None = None
) -> str:
    notes_instruction = (
        f"\n5. **Interpretation Notes:** Add the following as the first paragraph of the briefing note:\n{interpretation_notes}\n"
        if interpretation_notes
        else ""
    )

    notes_instruction += f"This is the original user query: {message}."
    notes_instruction += f"These are the most recent articles from that area and sector{articles}. Summarise them in the introduction."
    system_prompt = SYSTEM_PROMPT_PATH.read_text().replace(
        "{{interpretation_notes}}", notes_instruction
    )

    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": (f"Data (CSV):\n{data_as_csv}"),
            }
        ],
    )

    return next(
        block.text
        for block in message.content
        if isinstance(block, anthropic.types.TextBlock)
    )
