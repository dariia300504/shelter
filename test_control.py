"""Перевірка контрольного прикладу з додатка Д.

Запуск: python test_control.py
"""
import json
from pathlib import Path

import matching

ROOT = Path(__file__).resolve().parent


def run_control_example():
    data = json.loads((ROOT / "control_input.json").read_text(encoding="utf-8"))
    partial = {int(k): v for k, v in data["partial"].items()}
    return matching.recommend(data["profile"], data["animals"], data["weights"],
                              partial=partial)


def test_control_example_matches_appendix_d():
    expected = json.loads((ROOT / "control_output.json").read_text(encoding="utf-8"))
    assert run_control_example() == expected["items"]


if __name__ == "__main__":
    result = run_control_example()
    print(json.dumps({"items": result}, ensure_ascii=False, indent=2))
    test_control_example_matches_appendix_d()
    print("\nOK: результат збігається з додатком Д")
