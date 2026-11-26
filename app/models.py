from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class BrandProfile(Base):
    __tablename__ = "brand_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    brand_name: Mapped[str] = mapped_column(String(160))
    primary_genre: Mapped[str] = mapped_column(String(80), default="AI + Career")
    target_audience: Mapped[str] = mapped_column(String(255), default="Indian IT professionals")
    country: Mapped[str] = mapped_column(String(80), default="India")
    language: Mapped[str] = mapped_column(String(40), default="English")
    tone: Mapped[str] = mapped_column(String(80), default="Professional")
    objective: Mapped[str] = mapped_column(String(80), default="Grow followers")
    preferred_duration: Mapped[int] = mapped_column(Integer, default=30)
    topics_include: Mapped[str] = mapped_column(Text, default="")
    topics_exclude: Mapped[str] = mapped_column(Text, default="")

class InstagramAccount(Base):
    __tablename__ = "instagram_accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    instagram_user_id: Mapped[str] = mapped_column(String(100), unique=True)
    username: Mapped[str] = mapped_column(String(120))
    access_token: Mapped[str] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="CONNECTED")

class Reel(Base):
    __tablename__ = "reels"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic: Mapped[str] = mapped_column(String(255))
    hook: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(255))
    script: Mapped[str] = mapped_column(Text)
    caption: Mapped[str] = mapped_column(Text)
    hashtags: Mapped[str] = mapped_column(Text)
    cover_text: Mapped[str] = mapped_column(String(120))
    cta: Mapped[str] = mapped_column(String(255))
    duration: Mapped[int] = mapped_column(Integer, default=30)
    quality_score: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(40), default="IDEA_CREATED")
    video_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    scenes: Mapped[list["Scene"]] = relationship(back_populates="reel", cascade="all,delete-orphan", order_by="Scene.scene_number")

class Scene(Base):
    __tablename__ = "scenes"
    id: Mapped[int] = mapped_column(primary_key=True)
    reel_id: Mapped[int] = mapped_column(ForeignKey("reels.id"))
    scene_number: Mapped[int] = mapped_column(Integer)
    headline: Mapped[str] = mapped_column(String(255))
    voiceover_text: Mapped[str] = mapped_column(Text)
    duration: Mapped[int] = mapped_column(Integer)
    reel: Mapped[Reel] = relationship(back_populates="scenes")

class Publication(Base):
    __tablename__ = "publications"
    id: Mapped[int] = mapped_column(primary_key=True)
    reel_id: Mapped[int] = mapped_column(ForeignKey("reels.id"), unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True)
    instagram_media_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    media_container_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="PENDING")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

