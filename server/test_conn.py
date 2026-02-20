import asyncio
import asyncpg
import sys
import os

from dotenv import load_dotenv

load_dotenv()

async def main():
    url = os.environ.get("DATABASE_URL").replace("+asyncpg", "")
    print(f"Testing URL: {url.replace('rqYCUDsx0jsrbGVQAdOOopaEhcYCj2E4', '***')}")
    try:
        conn = await asyncpg.connect(url)
        print("Success!")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
