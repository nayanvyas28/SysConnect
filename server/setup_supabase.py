import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def init_db():
    from database import engine
    from models import Base
    print("Creating database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Failed to create database tables: {e}")

def init_storage():
    print("Setting up Storage Bucket...")
    try:
        from supabase import create_client, Client
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("Missing Supabase credentials, skipping storage setup.")
            return

        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Try to retrieve bucket to see if it exists
        try:
            supabase.storage.get_bucket("sysconnect-images")
            print("Bucket 'sysconnect-images' already exists.")
        except Exception:
            # Create the bucket
            print("Creating 'sysconnect-images' bucket...")
            supabase.storage.create_bucket("sysconnect-images", options={"public": True})
            print("Bucket created successfully!")

    except Exception as e:
        print(f"Failed to setup storage bucket: {e}")

if __name__ == "__main__":
    init_storage()
    asyncio.run(init_db())
