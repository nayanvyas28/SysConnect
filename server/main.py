from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from typing import List, Optional
import models, schemas, database, auth
import shutil
import os
import uuid
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv(override=True)

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

@app.get("/agent/config")
async def get_agent_config(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.GlobalConfig).limit(1))
    config = result.scalars().first()
    interval = config.screenshot_interval if config else 20
    return {"screenshot_interval_minutes": interval}

@app.get("/config/retention")
async def get_retention_config(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.GlobalConfig).limit(1))
    config = result.scalars().first()
    if not config:
        config = models.GlobalConfig(retention_days=30, screenshot_interval=20)
        db.add(config)
        await db.commit()
    return {
        "retention_days": config.retention_days,
        "screenshot_interval": config.screenshot_interval
    }

async def run_cleanup_task():
    # Because this is a background task, we need our own DB session
    async with database.AsyncSessionLocal() as db:
        result = await db.execute(select(models.GlobalConfig).limit(1))
        config = result.scalars().first()
        days = config.retention_days if config else 30
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
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
    screenshot_interval: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    if days < 1 or days > 90:
        raise HTTPException(status_code=400, detail="Retention days must be between 1 and 90")
    if screenshot_interval < 1:
        raise HTTPException(status_code=400, detail="Screenshot interval must be greater than 0")
        
    result = await db.execute(select(models.GlobalConfig).limit(1))
    config = result.scalars().first()
    
    if not config:
        config = models.GlobalConfig(retention_days=days, screenshot_interval=screenshot_interval)
        db.add(config)
    else:
        config.retention_days = days
        config.screenshot_interval = screenshot_interval
        
    await db.commit()
    
    # Trigger cleanup immediately when config is changed
    background_tasks.add_task(run_cleanup_task)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/config/supabase")
async def update_supabase_config(
    db_url: str = Form(""), 
    supa_url: str = Form(""),
    supa_key: str = Form("")
):
    env_content = f"DATABASE_URL={db_url}\nSUPABASE_URL={supa_url}\nSUPABASE_KEY={supa_key}\n"
    with open(".env", "w") as f:
        f.write(env_content)
        
    # Reload environment dynamically for storage, but SQLAlchemy engine requires restart
    os.environ["SUPABASE_URL"] = supa_url
    os.environ["SUPABASE_KEY"] = supa_key
    
    global supabase
    if supa_url and supa_key:
        try:
            supabase = create_client(supa_url, supa_key)
        except:
            supabase = None
    else:
        supabase = None
        
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
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_hostname = hostname.replace(" ", "_").replace("/", "_").replace("\\", "_")
    filename = f"{sanitized_hostname}_{now_str}.jpg"
    storage_path = f"{sanitized_hostname}/{filename}"
    
    file_bytes = await file.read()
    
    # Supabase strictly enforced
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured. Local storage is disabled.")
        
    try:
        supabase.storage.from_("sysconnect-images").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": "image/jpeg"}
        )
        public_url = supabase.storage.from_("sysconnect-images").get_public_url(storage_path)
        file_path = public_url
    except Exception as e:
        print(f"Supabase upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Supabase upload failed: {str(e)}")
        
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
    screenshot_interval = config.screenshot_interval if config else 20
    
    # Load env vars to pre-fill
    import os
    from dotenv import dotenv_values
    env_dict = dotenv_values(".env")
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "agents": agents,
        "now": datetime.now(timezone.utc).replace(tzinfo=None),
        "q": q or "",
        "retention_days": retention_days,
        "screenshot_interval": screenshot_interval,
        "env_db_url": env_dict.get("DATABASE_URL", ""),
        "env_supa_url": env_dict.get("SUPABASE_URL", ""),
        "env_supa_key": env_dict.get("SUPABASE_KEY", "")
    })

@app.get("/gallery")
async def gallery(request: Request, search_hostname: Optional[str] = None, search_date: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(models.Screenshot).options(selectinload(models.Screenshot.agent))
    
    if search_hostname:
        query = query.join(models.Agent).filter(models.Agent.hostname.ilike(f"%{search_hostname}%"))
        
    if search_date:
        from sqlalchemy import cast, Date
        try:
            date_obj = datetime.strptime(search_date, "%Y-%m-%d").date()
            query = query.filter(cast(models.Screenshot.timestamp, Date) == date_obj)
        except ValueError:
            pass # Invalid date format, ignore
            
    query = query.order_by(models.Screenshot.timestamp.desc()).limit(150)
    result = await db.execute(query)
    all_screenshots = result.scalars().all()
    
    # Filter out missing local files so empty blocks don't show in UI
    import os
    valid_screenshots = []
    for shot in all_screenshots:
        if "http" in shot.file_path:
            valid_screenshots.append(shot)
        else:
            # Check if local file exists
            if os.path.exists(shot.file_path):
                valid_screenshots.append(shot)
                
    # Limit final results
    valid_screenshots = valid_screenshots[:50]
                
    return templates.TemplateResponse("gallery.html", {
        "request": request, 
        "screenshots": valid_screenshots,
        "search_hostname": search_hostname or "",
        "search_date": search_date or ""
    })

@app.post("/gallery/delete/{shot_id}")
async def delete_screenshot(shot_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Screenshot).where(models.Screenshot.id == shot_id))
    shot = result.scalars().first()
    if not shot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
        
    # Delete file
    if "supabase" in shot.file_path and supabase:
        try:
            suffix = shot.file_path.split("sysconnect-images/")[-1].split("?")[0]
            supabase.storage.from_("sysconnect-images").remove([suffix])
        except Exception as e:
            print(f"Failed to delete screenshot from Supabase: {e}")
                
    # Delete DB record
    from sqlalchemy import delete
    await db.execute(delete(models.Screenshot).where(models.Screenshot.id == shot_id))
    await db.commit()
    
    # Redirect back to gallery
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/gallery", status_code=303)

@app.post("/gallery/delete_multiple")
async def delete_multiple_screenshots(
    request: Request,
    shot_ids: List[int] = Form(default=[]),
    db: AsyncSession = Depends(get_db)
):
    if not shot_ids:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/gallery", status_code=303)
        
    result = await db.execute(select(models.Screenshot).where(models.Screenshot.id.in_(shot_ids)))
    shots = result.scalars().all()
    
    for shot in shots:
        # Delete file
        if "supabase" in shot.file_path and supabase:
            try:
                suffix = shot.file_path.split("sysconnect-images/")[-1].split("?")[0]
                supabase.storage.from_("sysconnect-images").remove([suffix])
            except Exception as e:
                print(f"Failed to delete screenshot from Supabase: {e}")
                    
    # Delete DB records
    if shot_ids:
        from sqlalchemy import delete
        await db.execute(delete(models.Screenshot).where(models.Screenshot.id.in_(shot_ids)))
        await db.commit()
    
    # Redirect back to gallery
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/gallery", status_code=303)

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

@app.get("/debug/supabase")
async def debug_supabase():
    global supabase
    return {
        "supabase_is_not_none": supabase is not None,
        "env_url": os.environ.get("SUPABASE_URL"),
        "key_start": os.environ.get("SUPABASE_KEY", "")[:10] if os.environ.get("SUPABASE_KEY") else None
    }

