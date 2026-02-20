import asyncio
import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost/sysconnect")

async def test_connection():
    try:
        # Try connecting to 'postgres' database first to check credentials
        conn = await asyncpg.connect(user='postgres', password='password', database='postgres', host='localhost')
        print("Connected to 'postgres' database successfully.")
        await conn.close()
        
        # Now try 'sysconnect'
        try:
            conn = await asyncpg.connect(user='postgres', password='password', database='sysconnect', host='localhost')
            print("Connected to 'sysconnect' database successfully.")
            await conn.close()
        except asyncpg.InvalidCatalogNameError:
            print("Database 'sysconnect' does not exist.")
            # Create it?
            sys_conn = await asyncpg.connect(user='postgres', password='password', database='postgres', host='localhost')
            await sys_conn.execute('CREATE DATABASE sysconnect')
            print("Created 'sysconnect' database.")
            await sys_conn.close()
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
