from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional
import io
import base64

from video_engine.pipeline import generate_video_sync, generate_video_from_dsl, PipelineError
from video_engine.llm_translator import get_available_models
from video_engine.database import get_all_videos, get_video_by_id, delete_video

app = FastAPI(
    title="AnveshAI Video Generator",
    description="Programmatic video generation using LLM-to-DSL translation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Natural language description of the animation")
    duration: float = Field(default=3.0, ge=0.5, le=6.0, description="Duration in seconds (max 6)")
    fps: int = Field(default=24, ge=1, le=24, description="Frames per second (max 24)")
    width: int = Field(default=640, ge=320, le=1280, description="Video width (max 1280)")
    height: int = Field(default=360, ge=180, le=720, description="Video height (max 720)")
    model: str = Field(default="auto", description="Model to use: auto, groq, openai, or fallback")


class DSLRequest(BaseModel):
    dsl: str = Field(..., description="DSL animation script")
    width: int = Field(default=640, ge=320, le=1280, description="Video width (max 1280)")
    height: int = Field(default=360, ge=180, le=720, description="Video height (max 720)")


class GenerateResponse(BaseModel):
    ok: bool
    video_base64: Optional[str] = None
    dsl: Optional[str] = None
    error: Optional[str] = None


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get('/gallery', response_class=HTMLResponse)
async def gallery(request: Request):
    return templates.TemplateResponse("videos.html", {"request": request})


@app.get('/architecture', response_class=HTMLResponse)
async def architecture(request: Request):
    return templates.TemplateResponse("architecture.html", {"request": request})


@app.get('/models')
def get_models():
    return get_available_models()


@app.post('/generate', response_model=GenerateResponse)
def generate(req: GenerateRequest):
    try:
        video_b64, dsl = generate_video_sync(
            prompt=req.prompt,
            duration=req.duration,
            fps=req.fps,
            width=req.width,
            height=req.height,
            model=req.model
        )
        return GenerateResponse(ok=True, video_base64=video_b64, dsl=dsl)
    except PipelineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post('/generate-dsl', response_model=GenerateResponse)
def generate_from_dsl(req: DSLRequest):
    try:
        video_b64 = generate_video_from_dsl(
            dsl_script=req.dsl,
            width=req.width,
            height=req.height
        )
        return GenerateResponse(ok=True, video_base64=video_b64)
    except PipelineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get('/health')
def health():
    return {"status": "ok"}


@app.get('/dsl-help')
def dsl_help():
    return {
        "description": "Mini-DSL Animation Language",
        "commands": {
            "BACKGROUND": "BACKGROUND #RRGGBB - Set background color",
            "TEXT": 'TEXT "content" AT x,y SIZE pixels COLOR #RRGGBB [MOVE TO x,y DUR seconds]',
            "SHAPE_CIRCLE": "SHAPE CIRCLE ID name AT x,y RADIUS pixels COLOR #RRGGBB [MOVE TO x,y DUR seconds EASE type]",
            "SHAPE_RECT": "SHAPE RECT ID name AT x,y WIDTH pixels HEIGHT pixels COLOR #RRGGBB [MOVE TO x,y DUR seconds EASE type]",
            "MOVE": "MOVE object_id TO x,y DUR seconds EASE type",
            "FPS": "FPS number (1-24)",
            "DURATION": "DURATION seconds (0.5-6)"
        },
        "limits": {
            "max_resolution": "1280x720",
            "max_duration": "6 seconds",
            "max_fps": 24,
            "max_frames": 300,
            "max_objects": 50
        },
        "ease_types": ["linear", "ease-in", "ease-out"],
        "example": """BACKGROUND #1a1a2e
FPS 24
DURATION 3
SHAPE CIRCLE ID ball AT 50,180 RADIUS 30 COLOR #FF4444 MOVE TO 550,180 DUR 3 EASE linear
TEXT "Hello" AT 280,50 SIZE 36 COLOR #FFFFFF"""
    }


@app.get('/api/videos')
def list_videos():
    videos = get_all_videos()
    return [
        {
            "id": v.id,
            "prompt": v.prompt,
            "model_used": v.model_used,
            "duration": v.duration,
            "fps": v.fps,
            "created_at": v.created_at.isoformat(),
            "video_base64": base64.b64encode(v.video_base64).decode('utf-8') if isinstance(v.video_base64, bytes) else v.video_base64
        }
        for v in videos
    ]


@app.get('/api/videos/{video_id}/download')
def download_video(video_id: int):
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_bytes = video.video_base64 if isinstance(video.video_base64, bytes) else video.video_base64.encode('utf-8')
    return StreamingResponse(
        io.BytesIO(video_bytes),
        media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename=video_{video_id}.mp4"}
    )


@app.delete('/api/videos/{video_id}')
def delete_video_endpoint(video_id: int):
    if delete_video(video_id):
        return {"ok": True}
    raise HTTPException(status_code=404, detail="Video not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
