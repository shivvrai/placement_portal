import asyncio
from app.core.database import Base, AsyncSessionLocal
from sqlalchemy import text
import app.main  # load all models

async def main():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        existing = set(r[0] for r in res.fetchall())
        declared = set(Base.metadata.tables.keys())
        print(f"Declared models tables: {len(declared)}")
        print(f"Existing in DB: {len(existing)}")
        missing = declared - existing
        print(f"Missing in DB ({len(missing)}): {sorted(list(missing))}")
        
        # Check column differences for existing tables
        for t in sorted(list(declared.intersection(existing))):
            col_res = await session.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t}'"))
            db_cols = set(r[0] for r in col_res.fetchall())
            model_cols = set(Base.metadata.tables[t].columns.keys())
            missing_cols = model_cols - db_cols
            if missing_cols:
                print(f"Table '{t}' missing columns: {missing_cols}")

if __name__ == "__main__":
    asyncio.run(main())
