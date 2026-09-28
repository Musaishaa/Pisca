"""Validate PISCA's editable JSONL knowledge dataset."""
import json
import sys
from pathlib import Path


DATASET = Path(__file__).resolve().parent.parent / "data" / "pisca_dataset.jsonl"
REQUIRED = {"category", "instruction", "response"}


def validate(path: Path = DATASET) -> list[str]:
    errors, questions = [], set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            errors.append(f"Baris {number}: kosong.")
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append(f"Baris {number}: JSON tidak valid ({error.msg}).")
            continue
        missing = REQUIRED - item.keys()
        if missing:
            errors.append(f"Baris {number}: field kurang: {', '.join(sorted(missing))}.")
        if any(not isinstance(item.get(field), str) or not item.get(field).strip() for field in REQUIRED):
            errors.append(f"Baris {number}: terdapat field wajib yang kosong.")
        question = str(item.get("instruction", "")).strip().casefold()
        if question in questions:
            errors.append(f"Baris {number}: pertanyaan duplikat: {item.get('instruction')}")
        questions.add(question)
    return errors


if __name__ == "__main__":
    issues = validate()
    count = len(DATASET.read_text(encoding="utf-8").splitlines())
    if issues:
        print("Dataset tidak valid:")
        print("\n".join(issues))
        sys.exit(1)
    print(f"Dataset valid: {count} data.")
