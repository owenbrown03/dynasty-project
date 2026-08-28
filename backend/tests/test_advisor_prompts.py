import json

from app.services.advisor import prompts


def test_render_data_block_formats_payload():
    block = prompts.render_data_block(
        "Roster",
        {"players": ["A", "B"]},
    )

    assert block.startswith("### Roster\n```json\n")
    assert '"players"' in block
    assert block.endswith("```\n")


def test_system_prompt_forbids_invented_numbers():
    lowered = prompts.SYSTEM_PROMPT.lower()

    assert "never invent" in lowered
    assert "must come directly" in lowered


def test_render_data_block_handles_lists_and_objects():
    block = prompts.render_data_block("L", [1, 2, 3])

    parsed = json.loads(block.split("```json\n")[1].split("\n```")[0])

    assert parsed == [1, 2, 3]


def test_system_prompt_encodes_counterparty_direction_rules():
    lowered = prompts.SYSTEM_PROMPT.lower()

    assert "counterparty_fringe" in lowered
    assert "never" in lowered
    assert "draft picks" in lowered
    assert "hoarding capital" in lowered


def test_system_prompt_encodes_injury_rules():
    lowered = prompts.SYSTEM_PROMPT.lower()

    assert "injury_status" in lowered
    assert "avoid_injured" in lowered
    assert "absolute" in lowered


def test_system_prompt_describes_dual_waiver_ladders():
    lowered = prompts.SYSTEM_PROMPT.lower()

    assert "my_waiver_credit_war" in lowered
    assert "once" in lowered
