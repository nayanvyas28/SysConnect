from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from typing import List, Optional
import models, schemas, database, auth
import shutil
import os
import uuid
import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

try:
    from supabase import create_client, Client
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except ImportError:
    supabase = None

# Dependency
async def get_db():
    async with database.AsyncSessionLocal() as session:
        yield session

@app.on_event("startup")
async def startup():
    async with database.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # Simple mock auth for now - in production use DB lookup
    # user = await auth.authenticate_user(db, form_data.username, form_data.password)
    # Validating admin user (hardcoded for initial setup, TODO: implementing real user check)
    if form_data.username == "admin" and form_data.password == "admin":
        access_token = auth.create_access_token(data={"sub": form_data.username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.post("/agent/register", response_model=schemas.AgentCreate)
async def register_agent(agent: schemas.AgentCreate, db: AsyncSession = Depends(get_db)):
    # Check if agent exists
    result = await db.execute(select(models.Agent).where(models.Agent.hostname == agent.hostname))
    existing_agent = result.scalars().first()
    
    if existing_agent:
        existing_agent.ip_address = agent.ip_address
        existing_agent.last_seen = func.now()
        await db.commit()
        return agent
    
    new_agent = models.Agent(hostname=agent.hostname, ip_address=agent.ip_address)
    db.add(new_agent)
    await db.commit()
    return agent

@app.get("/config/retention")
async def get_retention_config(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.GlobalConfig).limit(1))
    config = result.scalars().first()
    if not config:
        config = models.GlobalConfig(retention_days=30)
        db.add(config)
        await db.commit()
    return {"retention_days": config.retention_days}

async def run_cleanup_task():
    # Because this is a background task, we need our own DB session
    async with database.AsyncSessionLocal() as db:
        result = await db.execute(select(models.GlobalConfig).limit(1))
        config = result.scalars().first()
        days = config.retention_days if config else 30
        
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
        
        # 1. Delete old ActivityLogs
        from sqlalchemy import delete
        await db.execute(delete(models.ActivityLog).where(models.ActivityLog.timestamp < cutoff))
        
        # 2. Delete old Screenshots
        # Get screenshots to delete files from Supabase or local storage
        shot_result = await db.execute(select(models.Screenshot).where(models.Screenshot.timestamp < cutoff))
        old_shots = shot_result.scalars().all()
        
        if old_shots:
            paths_to_delete = []
            for shot in old_shots:
                if "supabase" in shot.file_path and supabase:
                    try:
                        suffix = shot.file_path.split("sysconnect-images/")[-1].split("?")[0]
                        paths_to_delete.append(suffix)
                    except:
                        pass
                else:
                    if os.path.exists(shot.file_path):
                        try:
                            os.remove(shot.file_path)
                        except:
                            pass
            
            if paths_to_delete and supabase:
                try:
                    supabase.storage.from_("sysconnect-images").remove(paths_to_delete)
                except Exception as e:
                    print(f"Failed to delete old screenshots from Supabase: {e}")
                    
            await db.execute(delete(models.Screenshot).where(models.Screenshot.timestamp < cutoff))
            
        await db.commit()

@app.post("/config/retention")
async def update_retention_config(
    background_tasks: BackgroundTasks, 
    days: int = Form(...), 
    db: AsyncSession = Depends(get_db)
):
    if days < 1 or days > 90:
        raise HTTPException(status_code=400, detail="Retention days must be between 1 and 90")
        
    result = await db.execute(select(models.GlobalConfig).limit(1))
    config = result.scalars().first()
    
    if not config:
        config = models.GlobalConfig(retention_days=days)
        db.add(config)
    else:
        config.retention_days = days
        
    await db.commit()
    
    # Trigger cleanup immediately when config is changed
    background_tasks.add_task(run_cleanup_task)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard", status_code=303)

from sqlalchemy.orm import selectinload

# ... (existing imports)

# ... (existing code)

@app.post("/agent/upload/logs")
async def upload_logs(logs: List[schemas.ActivityLogCreate], hostname: str, db: AsyncSession = Depends(get_db)):
    # Find agent
    result = await db.execute(select(models.Agent).where(models.Agent.hostname == hostname))
    agent = result.scalars().first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Update last_seen
    agent.last_seen = func.now()
    
    for log in logs:
        db_log = models.ActivityLog(
            agent_id=agent.id,
            log_type=log.log_type,
            content=log.content,
            timestamp=log.timestamp
        )
        db.add(db_log)
    
    await db.commit()
    return {"status": "success", "count": len(logs)}

@app.post("/agent/upload/screenshot")
async def upload_screenshot(
    hostname: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Agent).where(models.Agent.hostname == hostname))
    agent = result.scalars().first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Update last_seen
    agent.last_seen = func.now()
    
    # Save file
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_hostname = hostname.replace(" ", "_").replace("/", "_").replace("\\", "_")
    filename = f"{sanitized_hostname}_{now_str}.png"
    storage_path = f"{sanitized_hostname}/{filename}"
    
    file_path = f"uploads/screenshots/{filename}"
    upload_dir = "uploads/screenshots"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_bytes = await file.read()
    
    if supabase:
        try:
            supabase.storage.from_("sysconnect-images").upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": "image/png"}
            )
            public_url = supabase.storage.from_("sysconnect-images").get_public_url(storage_path)
            file_path = public_url
        except Exception as e:
            print(f"Supabase upload error: {e}")
            with open(file_path, "wb") as buffer:
                buffer.write(file_bytes)
    else:
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)
        
    db_screenshot = models.Screenshot(
        agent_id=agent.id,
        file_path=file_path
    )
    db.add(db_screenshot)
    await db.commit()
    return {"status": "success", "file_name": filename}

# --- Frontend Routes ---
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from datetime import datetime

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

@app.get("/dashboard")
async def dashboard(request: Request, q: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(models.Agent).order_by(models.Agent.last_seen.desc())
    if q:
        query = query.filter(models.Agent.hostname.ilike(f"%{q}%"))
        
    result = await db.execute(query)
    agents = result.scalars().all()
    
    config_result = await db.execute(select(models.GlobalConfig).limit(1))
    config = config_result.scalars().first()
    retention_days = config.retention_days if config else 30
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "agents": agents,
        "now": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
        "q": q or "",
        "retention_days": retention_days
    })

@app.get("/gallery")
async def gallery(request: Request, search_hostname: Optional[str] = None, search_date: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(models.Screenshot).options(selectinload(models.Screenshot.agent))
    
    if search_hostname:
        query = query.join(models.Agent).filter(models.Agent.hostname.ilike(f"%{search_hostname}%"))
        
    if search_date:
        from sqlalchemy import cast, Date
        try:
            date_obj = datetime.datetime.strptime(search_date, "%Y-%m-%d").date()
            query = query.filter(cast(models.Screenshot.timestamp, Date) == date_obj)
        except ValueError:
            pass # Invalid date format, ignore
            
    query = query.order_by(models.Screenshot.timestamp.desc()).limit(50)
    result = await db.execute(query)
    screenshots = result.scalars().all()
    return templates.TemplateResponse("gallery.html", {
        "request": request, 
        "screenshots": screenshots,
        "search_hostname": search_hostname or "",
        "search_date": search_date or ""
    })

@app.post("/agent/{agent_id}/clear_logs")
async def clear_logs(agent_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    # Verify agent exists
    result = await db.execute(select(models.Agent).where(models.Agent.id == agent_id))
    agent = result.scalars().first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    # Delete logs
    from sqlalchemy import delete
    await db.execute(delete(models.ActivityLog).where(models.ActivityLog.agent_id == agent_id))
    await db.commit()
    
    # Redirect back to agent detail
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/agent/{agent_id}", status_code=303)

@app.get("/agent/{agent_id}")
async def agent_detail(agent_id: int, request: Request, q: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Agent).where(models.Agent.id == agent_id))
    agent = result.scalars().first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    from sqlalchemy import cast, String
    log_query = select(models.ActivityLog).where(models.ActivityLog.agent_id == agent_id)
    
    if q:
        log_query = log_query.filter(
            (models.ActivityLog.log_type.ilike(f"%{q}%")) |
            (cast(models.ActivityLog.content, String).ilike(f"%{q}%"))
        )
        
    log_query = log_query.order_by(models.ActivityLog.timestamp.desc()).limit(100)
    log_result = await db.execute(log_query)
    logs = log_result.scalars().all()
    
    return templates.TemplateResponse("agent_detail.html", {
        "request": request,
        "agent": agent,
        "logs": logs,
        "q": q or ""
    })

