from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./videos.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class VideoMetadata(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(String, nullable=True)
    dsl_script = Column(String)
    model_used = Column(String)
    duration = Column(Float)
    fps = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    video_base64 = Column(LargeBinary)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_video_metadata(
    dsl_script: str,
    video_base64: bytes,
    prompt: Optional[str] = None,
    model: str = "auto",
    duration: float = 3.0,
    fps: int = 24,
    width: int = 640,
    height: int = 360
) -> "VideoMetadata":
    db = SessionLocal()
    try:
        video_bytes = video_base64 if isinstance(video_base64, bytes) else video_base64
        video = VideoMetadata(
            prompt=prompt,
            dsl_script=dsl_script,
            model_used=model,
            duration=duration,
            fps=fps,
            width=width,
            height=height,
            video_base64=video_bytes
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        return video
    finally:
        db.close()


def get_all_videos():
    db = SessionLocal()
    try:
        return db.query(VideoMetadata).order_by(VideoMetadata.created_at.desc()).all()
    finally:
        db.close()


def get_video_by_id(video_id: int):
    db = SessionLocal()
    try:
        return db.query(VideoMetadata).filter(VideoMetadata.id == video_id).first()
    finally:
        db.close()


def delete_video(video_id: int):
    db = SessionLocal()
    try:
        video = db.query(VideoMetadata).filter(VideoMetadata.id == video_id).first()
        if video:
            db.delete(video)
            db.commit()
            return True
        return False
    finally:
        db.close()
