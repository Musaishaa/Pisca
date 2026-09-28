import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import Memory
from backend.schemas import MemoryCreate, MemoryUpdate


class MemoryService:
    def list(self, db: Session) -> list[Memory]:
        return list(db.scalars(select(Memory).order_by(Memory.updated_at.desc())).all())

    def create(self, db: Session, item: MemoryCreate) -> Memory:
        existing = db.scalar(select(Memory).where(Memory.key == item.key))
        if existing:
            existing.category, existing.value, existing.source = item.category, item.value, item.source
            db.commit()
            db.refresh(existing)
            return existing
        memory = Memory(**item.model_dump())
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory

    def update(self, db: Session, memory: Memory, item: MemoryUpdate) -> Memory:
        for field, value in item.model_dump().items():
            setattr(memory, field, value)
        db.commit()
        db.refresh(memory)
        return memory

    def delete(self, db: Session, memory: Memory) -> None:
        db.delete(memory)
        db.commit()

    def context(self, db: Session) -> str:
        memories = self.list(db)
        if not memories:
            return "Tidak ada informasi pribadi yang tersimpan."
        return "\n".join(f"- {memory.key}: {memory.value}" for memory in memories)

    def recall(self, db: Session, message: str) -> str | None:
        """Answer personal questions from stored memory without an LLM.

        Returns a string when the message is a memory question, otherwise None.
        """
        text = message.casefold()
        if any(phrase in text for phrase in (
            "apa yang kamu ingat tentang saya",
            "apa yang kamu tahu tentang saya",
            "apa yang kamu ketahui tentang saya",
            "apa saja yang kamu ingat",
        )):
            memories = self.list(db)
            if not memories:
                return "Saya belum menyimpan informasi apa pun tentang Anda."
            return "Berikut yang saya ingat tentang Anda:\n" + "\n".join(
                f"- {memory.key}: {memory.value}" for memory in memories
            )

        lookups = [
            (("nama saya", "namaku", "siapa saya", "siapa aku"), "nama"),
            (("jurusan", "mahasiswa apa", "kuliah apa", "status saya"), "status dan jurusan"),
            (("umur", "usia", "berapa tua"), "umur"),
            (("alamat", "tinggal", "rumah saya", "di mana saya"), "alamat"),
        ]
        for keywords, key in lookups:
            if any(keyword in text for keyword in keywords):
                memory = db.scalar(select(Memory).where(Memory.key == key))
                if memory:
                    return f"Berdasarkan ingatan saya, {key} Anda adalah {memory.value}."
                return f"Saya belum mengetahui {key} Anda karena informasi tersebut belum pernah diberikan."
        return None

    def extract_explicit(self, message: str) -> MemoryCreate | None:
        """Support intentional Indonesian memory commands without storing all chat."""
        text = message.strip()
        patterns = [
            (r"^ingat(?:lah)? bahwa nama saya (.+)$", "personal", "nama"),
            (r"^ingat(?:lah)? bahwa saya mahasiswa (.+)$", "education", "status dan jurusan"),
            (r"^ingat(?:lah)? bahwa saya (.+)$", "personal", "informasi pengguna"),
        ]
        for pattern, category, key in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                return MemoryCreate(category=category, key=key, value=match.group(1).strip(), source="user")
        return None

    def extract_forget_key(self, message: str) -> str | None:
        match = re.match(r"^lupakan bahwa (?:saya )?(.+)$", message.strip(), re.IGNORECASE)
        if not match:
            return None
        phrase = match.group(1).lower()
        if "mahasiswa" in phrase or "jurusan" in phrase:
            return "status dan jurusan"
        if "nama" in phrase:
            return "nama"
        return phrase
