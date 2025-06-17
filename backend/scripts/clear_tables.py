import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.db.session import init_db, SessionLocal
from backend.ingestion.run_ingest import clear_all_tables

def main():
    """Clear all tables in the database"""
    init_db()
    with SessionLocal() as db:
        clear_all_tables(db)
    print("✅ All tables cleared successfully.")

if __name__ == "__main__":
    main() 