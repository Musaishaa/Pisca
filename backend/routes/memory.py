from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Memory
from backend.schemas import MemoryCreate, MemoryResponse, MemoryUpdate
from backend.services.memory_service import MemoryService

router = APIRouter(prefix="/api/memories", tags=["memories"])
service = MemoryService()


@router.get("", response_model=list[MemoryResponse])
def list_memories(db: Session = Depends(get_db)):
    return service.list(db)


@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
def create_memory(item: MemoryCreate, db: Session = Depends(get_db)):
    return service.create(db, item)


@router.put("/{memory_id}", response_model=MemoryResponse)
def update_memory(memory_id: int, item: MemoryUpdate, db: Session = Depends(get_db)):
    memory = db.get(Memory, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory tidak ditemukan.")
    return service.update(db, memory, item)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(memory_id: int, db: Session = Depends(get_db)):
    memory = db.get(Memory, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory tidak ditemukan.")
    service.delete(db, memory)
