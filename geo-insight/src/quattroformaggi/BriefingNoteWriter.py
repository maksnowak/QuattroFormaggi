from pathlib import Path

import anthropic

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "prompts" / "BriefingNoteWriter.md"


async def brief_writer(
    data_as_csv: str, interpretation_notes: str | None = None
) -> str:
    notes_instruction = (
        f"\n5. **Interpretation Notes:** Add the following as the first paragraph of the briefing note, before the BLUF section:\n{interpretation_notes}\n"
        if interpretation_notes
        else ""
    )
    system_prompt = SYSTEM_PROMPT_PATH.read_text().replace(
        "{{interpretation_notes}}", notes_instruction
    )

    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
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
