"""
file: tests/test_usage.py
importable: nothing, pytest loads this file

description: Checks the token count of a reels session.
"""

import json

from reels.usage import Usage, count


# One answer is written as several lines with the same message id and counted once.
def test_usage_counts_each_answer_once(tmp_path):
    lines = [{"type": "assistant", "message": {"id": "m1", "model": "claude-opus-5-5", "usage": {"input_tokens": 5, "cache_read_input_tokens": 100, "output_tokens": 7}}},
             {"type": "assistant", "message": {"id": "m1", "model": "claude-opus-5-5", "usage": {"input_tokens": 5, "cache_read_input_tokens": 100, "output_tokens": 7}}},
             {"type": "user", "message": {"content": "hi"}}]
    path = tmp_path / "s.jsonl"
    path.write_text("\n".join(json.dumps(line) for line in lines))
    found: dict[str, Usage] = {}
    count(path, found, "main ")
    assert found["main claude-opus-5-5"].turns == 1
    assert found["main claude-opus-5-5"].tokens["cache_read"] == 100
