import asyncio
from sqlalchemy.future import select
import models
from database import AsyncSessionLocal, engine

async def test():
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(models.GlobalConfig).limit(1))
            config = result.scalars().first()
            print(f"Config: {config}")
        except Exception as e:
            print(f"Error querying GlobalConfig: {e}")

asyncio.run(test())
