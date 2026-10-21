from app.safety import clean_reply, crisis_match


def test_crisis_phrases_match():
    for t in ["I want to die", "thinking about suicide", "I don’t want to be alive",
              "I keep hurting myself", "I can't go on", "everyone is better off without me"]:
        assert crisis_match(t), t


def test_ordinary_text_does_not_match():
    for t in ["this drill is killing me", "I'm dead tired", "my phone died",
              "I killed it at practice", "deadline tomorrow"]:
        assert not crisis_match(t), t


def test_known_miss_is_documented():
    # Limitation: indirect wording is not caught. The prompt and the always-visible
    # button are the backup. Kept as a test so the limit stays visible.
    assert not crisis_match("I just want to disappear for good")


def test_clean_reply_blocks_clinical_and_monitoring():
    assert clean_reply("This sounds like a disorder.", 100) is None
    assert clean_reply("I'll check in with you tomorrow.", 100) is None
    assert clean_reply("As your therapist I think...", 100) is None


def test_clean_reply_softens_and_limits():
    assert clean_reply("You did it!", 20) == "You did it."
    assert clean_reply("word " * 30, 20) is None
    assert clean_reply("You should breathe more.", 20, short=True) is None


def test_every_mock_line_passes_the_output_filter():
    # Found during the 3.2 browser run: a mock closing line contained "you need to",
    # so the filter replaced it with the fallback. Every saved line must pass.
    import json
    from pathlib import Path
    mocks = json.loads((Path(__file__).parent.parent / "app/mock_responses.json").read_text())
    for key in ("opening", "closing", "closing_usual"):
        for line in mocks[key]:
            assert clean_reply(line, 25, short=True) == line, line
    replies = [r["reply"] for r in mocks["journal"]["rules"]] + mocks["journal"]["default"]
    for line in replies:
        assert clean_reply(line, 110) == line, line
