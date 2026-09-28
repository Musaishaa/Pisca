from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import Conversation, Memory, Message
from backend.services.llm_service import LLMService
from backend.services.dataset_service import DatasetService
from backend.services.memory_service import MemoryService


SYSTEM_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "system_prompt.txt"
FALLBACK_ANSWER = (
    "Saya belum memiliki informasi tentang itu. "
    "Anda bisa mengajari saya lewat perintah 'Ingat bahwa ...'."
)
MATCH_THRESHOLD = 0.18


class ChatService:
    def __init__(
        self,
        llm: LLMService | None,
        memories: MemoryService | None = None,
        dataset: DatasetService | None = None,
    ):
        self.llm = llm
        self.memories = memories or MemoryService()
        self.dataset = dataset or DatasetService()

    async def reply(self, db: Session, message: str, conversation_id: int | None = None) -> tuple[str, bool, int]:
        message = message.strip()
        if not message:
            raise ValueError("Silakan masukkan pertanyaan.")
        conversation = db.get(Conversation, conversation_id) if conversation_id else None
        if conversation is None:
            conversation = Conversation()
            db.add(conversation)
            db.flush()
        db.add(Message(conversation_id=conversation.id, role="user", content=message))

        remembered = self.memories.extract_explicit(message)
        if remembered:
            saved = self.memories.create(db, remembered)
            answer = f"Baik, saya akan mengingat bahwa {saved.key} Anda adalah {saved.value}."
            db.add(Message(conversation_id=conversation.id, role="assistant", content=answer))
            db.commit()
            return answer, True, conversation.id

        forget_key = self.memories.extract_forget_key(message)
        if forget_key:
            memory = db.scalar(select(Memory).where(Memory.key == forget_key))
            answer = "Informasi tersebut tidak ditemukan di memory saya."
            if memory:
                self.memories.delete(db, memory)
                answer = "Baik, informasi tersebut sudah saya lupakan."
            db.add(Message(conversation_id=conversation.id, role="assistant", content=answer))
            db.commit()
            return answer, memory is not None, conversation.id

        recall_answer = self.memories.recall(db, message)
        if recall_answer is not None:
            db.add(Message(conversation_id=conversation.id, role="assistant", content=recall_answer))
            db.commit()
            return recall_answer, True, conversation.id

        exact_entry = self.dataset.exact(message)
        if exact_entry:
            db.add(Message(conversation_id=conversation.id, role="assistant", content=exact_entry.response))
            db.commit()
            return exact_entry.response, False, conversation.id

        top_matches = self.dataset.search(message, limit=1)
        has_reference = bool(top_matches and top_matches[0][1] >= MATCH_THRESHOLD)

        if self.llm is not None:
            memory_context = self.memories.context(db)
            dataset_context = self.dataset.context(message)
            prompt = (
                SYSTEM_PROMPT.read_text(encoding="utf-8")
                .replace("{{MEMORIES}}", memory_context)
                .replace("{{DATASET_CONTEXT}}", dataset_context)
            )
            answer = await self.llm.generate(prompt, message)
            db.add(Message(conversation_id=conversation.id, role="assistant", content=answer))
            db.commit()
            return answer, memory_context != "Tidak ada informasi pribadi yang tersimpan.", conversation.id

        if has_reference:
            answer = top_matches[0][0].response
            db.add(Message(conversation_id=conversation.id, role="assistant", content=answer))
            db.commit()
            return answer, False, conversation.id

        db.add(Message(conversation_id=conversation.id, role="assistant", content=FALLBACK_ANSWER))
        db.commit()
        return FALLBACK_ANSWER, False, conversation.id
