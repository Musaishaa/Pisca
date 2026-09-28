from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, get_db
from backend.main import app
from backend.services.llm_service import LLMService
from backend.services.dataset_service import DatasetService
from backend.services.chat_service import ChatService
from scripts.validate_dataset import validate


class StubLLM(LLMService):
    async def generate(self, system_prompt: str, user_message: str) -> str:
        return "Jawaban lokal untuk pengujian."


def test_dataset_exact_match(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'dataset.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as db:
        answer, memory_used, _conversation_id = __import__("asyncio").run(
            ChatService(StubLLM()).reply(db, "Apa itu database?")
        )
    assert answer.startswith("Database adalah")
    assert memory_used is False


def test_dataset_search_has_reference():
    matches = DatasetService().search("Jelaskan database")
    assert matches
    assert matches[0][0].category == "Database"


def make_client(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    def override():
        db = Session()
        try: yield db
        finally: db.close()
    app.dependency_overrides[get_db] = override
    return TestClient(app)


def test_memory_crud(tmp_path):
    client = make_client(tmp_path)
    created = client.post("/api/memories", json={"category":"personal", "key":"nama", "value":"Pisca"})
    assert created.status_code == 201
    memory_id = created.json()["id"]
    assert client.get("/api/memories").json()[0]["value"] == "Pisca"
    assert client.put(f"/api/memories/{memory_id}", json={"category":"personal", "key":"nama", "value":"PISCA"}).status_code == 200
    assert client.delete(f"/api/memories/{memory_id}").status_code == 204


def test_chat_explicit_memory_without_llm(tmp_path):
    client = make_client(tmp_path)
    response = client.post("/api/chat", json={"message":"Ingat bahwa nama saya Pisca"})
    assert response.status_code == 200
    assert response.json()["memory_used"] is True


def test_recall_memory_without_llm(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/chat", json={"message":"Ingat bahwa nama saya Pisca"})
    response = client.post("/api/chat", json={"message":"Siapa nama saya?"})
    assert response.status_code == 200
    assert "Pisca" in response.json()["answer"]
    assert response.json()["memory_used"] is True


def test_honesty_unknown_personal_info(tmp_path):
    client = make_client(tmp_path)
    response = client.post("/api/chat", json={"message":"Berapa umur saya?"})
    assert response.status_code == 200
    assert "belum pernah diberikan" in response.json()["answer"]


def test_fuzzy_dataset_answer_without_llm(tmp_path):
    client = make_client(tmp_path)
    response = client.post("/api/chat", json={"message":"Jelaskan database"})
    assert response.status_code == 200
    assert "Database adalah" in response.json()["answer"]


def test_fallback_unknown_topic_without_llm(tmp_path):
    client = make_client(tmp_path)
    response = client.post("/api/chat", json={"message":"Apa itu blockchain?"})
    assert response.status_code == 200
    assert "belum memiliki informasi" in response.json()["answer"]


def test_health_and_dataset():
    assert TestClient(app).get("/health").status_code == 200
    assert validate() == []
