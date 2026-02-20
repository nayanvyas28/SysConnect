import asyncio
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Agent
from database import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def check_agents():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Agent))
        agents = result.scalars().all()
        print(f"Found {len(agents)} agents.")
        for agent in agents:
            print(f"Agent: {agent.hostname}, IP: {agent.ip_address}")

if __name__ == "__main__":
    asyncio.run(check_agents())
