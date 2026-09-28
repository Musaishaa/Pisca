"""Create the SQLite tables used by PISCA."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import Base, engine

Base.metadata.create_all(bind=engine)
print("Database PISCA siap.")
