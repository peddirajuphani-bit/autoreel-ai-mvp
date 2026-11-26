from datetime import datetime
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, Depends, HTTPException, Response, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from .config import settings
from .db import Base, engine, get_db
from .models import User, BrandProfile, Reel, Scene, Publication, InstagramAccount
from .auth import hash_password, verify_password, token_for, current_user
from .providers import MockContentProvider
from .state import move
from .render import render

Base.metadata.create_all(engine)
app=FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory="static"), name="static")
Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)

@app.get("/")
def home(): return FileResponse("static/index.html")

@app.post("/api/register")
def register(response: Response, email: str=Form(), name: str=Form(), password: str=Form(), db: Session=Depends(get_db)):
    if db.scalar(select(User).where(User.email==email.lower())): raise HTTPException(409,"Email already registered")
    u=User(email=email.lower(),name=name,password_hash=hash_password(password)); db.add(u); db.commit(); db.refresh(u)
    response.set_cookie("access_token",token_for(u.id),httponly=True,secure=settings.cookie_secure,samesite="lax",max_age=604800)
    return {"id":u.id,"name":u.name}

@app.post("/api/login")
def login(response: Response, email: str=Form(), password: str=Form(), db: Session=Depends(get_db)):
    u=db.scalar(select(User).where(User.email==email.lower()))
    if not u or not verify_password(password,u.password_hash): raise HTTPException(401,"Invalid credentials")
    response.set_cookie("access_token",token_for(u.id),httponly=True,secure=settings.cookie_secure,samesite="lax",max_age=604800)
    return {"id":u.id,"name":u.name}

@app.post("/api/logout")
def logout(response: Response): response.delete_cookie("access_token"); return {"ok":True}

@app.get("/api/me")
def me(u=Depends(current_user)): return {"id":u.id,"name":u.name,"email":u.email}

@app.get("/api/brand")
def get_brand(u=Depends(current_user),db:Session=Depends(get_db)):
    p=db.scalar(select(BrandProfile).where(BrandProfile.user_id==u.id)); return profile_dict(p) if p else None

def profile_dict(p): return {c.name:getattr(p,c.name) for c in p.__table__.columns} if p else None

@app.post("/api/brand")
def save_brand(brand_name:str=Form(),primary_genre:str=Form(),target_audience:str=Form(),country:str=Form(),language:str=Form(),tone:str=Form(),objective:str=Form(),preferred_duration:int=Form(),topics_include:str=Form(""),topics_exclude:str=Form(""),u=Depends(current_user),db:Session=Depends(get_db)):
    p=db.scalar(select(BrandProfile).where(BrandProfile.user_id==u.id)) or BrandProfile(user_id=u.id)
    for k,v in locals().copy().items():
        if k in {"brand_name","primary_genre","target_audience","country","language","tone","objective","preferred_duration","topics_include","topics_exclude"}: setattr(p,k,v)
    db.add(p);db.commit();db.refresh(p);return profile_dict(p)

@app.post("/api/reels/generate")
def generate(u=Depends(current_user),db:Session=Depends(get_db)):
    p=db.scalar(select(BrandProfile).where(BrandProfile.user_id==u.id))
    if not p: raise HTTPException(400,"Create brand profile first")
    data=MockContentProvider().generate(p)
    r=Reel(user_id=u.id,duration=p.preferred_duration,**{k:data[k] for k in ["topic","hook","title","script","caption","hashtags","cover_text","cta","quality_score"]})
    db.add(r);db.flush()
    move(r,"SCRIPT_GENERATED")
    for i,(h,v,d) in enumerate(data["scenes"],1): db.add(Scene(reel_id=r.id,scene_number=i,headline=h,voiceover_text=v,duration=d))
    move(r,"ASSETS_READY");move(r,"RENDERING");db.commit();db.refresh(r)
    try:
        r.video_path=render(r);move(r,"RENDERED");move(r,"QUALITY_CHECKING");move(r,"AWAITING_APPROVAL")
    except Exception as e:
        r.status="RENDER_FAILED";db.commit();raise HTTPException(500,f"Render failed: {e}")
    db.commit();return reel_dict(r)

def fetch_reel(db,rid,uid):
    r=db.scalar(select(Reel).options(selectinload(Reel.scenes)).where(Reel.id==rid,Reel.user_id==uid))
    if not r: raise HTTPException(404,"Reel not found")
    return r

def reel_dict(r):
    return {"id":r.id,"topic":r.topic,"hook":r.hook,"title":r.title,"script":r.script,"caption":r.caption,"hashtags":r.hashtags,"cover_text":r.cover_text,"cta":r.cta,"duration":r.duration,"quality_score":r.quality_score,"status":r.status,"scheduled_at":r.scheduled_at.isoformat() if r.scheduled_at else None,"video_url":f"/api/reels/{r.id}/video" if r.video_path else None,"scenes":[{"id":s.id,"scene_number":s.scene_number,"headline":s.headline,"voiceover_text":s.voiceover_text,"duration":s.duration} for s in r.scenes]}

@app.get("/api/reels")
def list_reels(u=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.scalars(select(Reel).options(selectinload(Reel.scenes)).where(Reel.user_id==u.id).order_by(Reel.id.desc())).all();return [reel_dict(x) for x in rows]

@app.get("/api/reels/{rid}")
def get_reel(rid:int,u=Depends(current_user),db:Session=Depends(get_db)): return reel_dict(fetch_reel(db,rid,u.id))

@app.get("/api/reels/{rid}/video")
def video(rid:int,u=Depends(current_user),db:Session=Depends(get_db)):
    r=fetch_reel(db,rid,u.id)
    if not r.video_path or not Path(r.video_path).exists(): raise HTTPException(404,"Video unavailable")
    return FileResponse(r.video_path,media_type="video/mp4",filename=f"autoreel-{rid}.mp4")

@app.post("/api/reels/{rid}/approve")
def approve(rid:int,u=Depends(current_user),db:Session=Depends(get_db)):
    r=fetch_reel(db,rid,u.id)
    try: move(r,"APPROVED")
    except ValueError as e: raise HTTPException(409,str(e))
    db.commit();return reel_dict(r)

@app.post("/api/reels/{rid}/schedule")
def schedule(rid:int,scheduled_at:str=Form(),u=Depends(current_user),db:Session=Depends(get_db)):
    r=fetch_reel(db,rid,u.id)
    try: dt=datetime.fromisoformat(scheduled_at); move(r,"SCHEDULED")
    except (ValueError,TypeError) as e: raise HTTPException(400,str(e))
    r.scheduled_at=dt;db.commit();return reel_dict(r)

@app.post("/api/reels/{rid}/publish")
def publish(rid:int,u=Depends(current_user),db:Session=Depends(get_db)):
    r=fetch_reel(db,rid,u.id)
    if r.status not in {"APPROVED","SCHEDULED"}: raise HTTPException(409,"Approve the Reel first")
    existing=db.scalar(select(Publication).where(Publication.reel_id==r.id))
    if existing: return {"status":existing.status,"message":"Existing publication returned; duplicate prevented"}
    pub=Publication(reel_id=r.id,idempotency_key=str(uuid4()),status="DRY_RUN" if not settings.instagram_publish_enabled else "PENDING")
    db.add(pub)
    if not settings.instagram_publish_enabled:
        db.commit();return {"status":"DRY_RUN","message":"Publishing is safely disabled. Configure Meta OAuth and enable production publishing."}
    raise HTTPException(501,"Complete Meta OAuth connection and production media hosting before enabling this route")

