import asyncio
import asyncpg

async def test_conn():
    print(f"Testing direct connection with kwargs")
    try:
        conn = await asyncpg.connect(
            host='127.0.0.1',
            port=5432,
            user='postgres',
            password='SysConnect@123',
            database='postgres'
        )
        print("Success! Connection established.")
        await conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

asyncio.run(test_conn())
