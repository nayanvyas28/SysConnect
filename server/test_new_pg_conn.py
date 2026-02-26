import asyncio
import asyncpg
import logging

logging.basicConfig(level=logging.DEBUG)

async def test_conn():
    print("Testing local Supabase connection")
    try:
        # Using exact password from image: lgAWUPXZdlVmuAv9Pixqx9hO64MRN1je
        # (Starts with lowercase L, ends with O before 64)
        url = 'postgresql://postgres:lgAWUPXZdlVmuAv9Pixqx9hO64MRN1je@127.0.0.1:5432/postgres'
        conn = await asyncpg.connect(url, timeout=5)
        print("Success! Connection established.")
        await conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

asyncio.run(test_conn())
