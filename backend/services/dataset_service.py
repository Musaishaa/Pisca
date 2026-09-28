import json
import re
from dataclasses import dataclass
from pathlib import Path


DATASET_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "pisca_dataset.jsonl"
STOPWORDS = {
    "apa", "itu", "yang", "dan", "atau", "di", "ke", "dari", "untuk", "dengan",
    "adalah", "jelaskan", "jelaskanlah", "jelaskan", "saya", "ini", "bagaimana",
    "mengapa", "fungsi", "pengertian", "sebuah", "suatu", "pada", "dalam",
}


@dataclass(frozen=True)
class DatasetEntry:
    category: str
    instruction: str
    response: str


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.casefold())
    return {word for word in words if word not in STOPWORDS and len(word) > 1}


class DatasetService:
    def __init__(self, path: Path = DATASET_PATH):
        self.entries = self._load(path)

    @staticmethod
    def _load(path: Path) -> list[DatasetEntry]:
        entries = []
        for line in path.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            entries.append(DatasetEntry(item["category"], item["instruction"], item["response"]))
        return entries

    def search(self, question: str, limit: int = 3) -> list[tuple[DatasetEntry, float]]:
        query_tokens = _tokens(question)
        if not query_tokens:
            return []
        scored = []
        for entry in self.entries:
            entry_tokens = _tokens(entry.instruction)
            overlap = len(query_tokens & entry_tokens)
            score = overlap / len(query_tokens | entry_tokens) if entry_tokens else 0
            if overlap:
                scored.append((entry, score))
        return sorted(scored, key=lambda item: item[1], reverse=True)[:limit]

    def exact(self, question: str) -> DatasetEntry | None:
        normalized = " ".join(question.casefold().split()).strip(" ?.!,-")
        for entry in self.entries:
            candidate = " ".join(entry.instruction.casefold().split()).strip(" ?.!,-")
            if normalized == candidate:
                return entry
        return None

    def context(self, question: str) -> str:
        matches = self.search(question)
        if not matches or matches[0][1] < 0.18:
            return "Tidak ada referensi dataset yang cukup relevan."
        return "\n\n".join(
            f"[{entry.category}]\nPertanyaan referensi: {entry.instruction}\nJawaban referensi: {entry.response}"
            for entry, _score in matches
        )
