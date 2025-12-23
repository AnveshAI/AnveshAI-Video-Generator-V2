import base64
import time
from typing import Optional, Tuple, Union

from .dsl_parser import parse_dsl, DSLParseError, DSLValidationError
from .renderer import AnimationRenderer
from .llm_translator import translate_prompt_to_dsl
from .constants import MAX_DURATION, MAX_FPS, MAX_WIDTH, MAX_HEIGHT, RENDER_TIMEOUT
from .database import save_video_metadata


class PipelineError(Exception):
    pass


def generate_video_sync(
    prompt: str,
    duration: float = 3.0,
    fps: int = 24,
    width: int = 640,
    height: int = 360,
    model: str = "auto",
    save_metadata: bool = True
) -> Tuple[str, str]:
    start_time = time.time()
    
    duration = min(max(duration, 0.5), MAX_DURATION)
    fps = min(max(fps, 1), MAX_FPS)
    width = min(max(width, 320), MAX_WIDTH)
    height = min(max(height, 180), MAX_HEIGHT)
    
    try:
        dsl_script = translate_prompt_to_dsl(prompt, duration, fps, model)
    except Exception as e:
        raise PipelineError(f"Failed to generate animation script: {str(e)}")
    
    if time.time() - start_time > RENDER_TIMEOUT:
        raise PipelineError("Timeout during script generation")
    
    try:
        spec = parse_dsl(dsl_script)
    except DSLParseError as e:
        raise PipelineError(f"Invalid animation script: {str(e)}")
    except DSLValidationError as e:
        raise PipelineError(f"Animation validation failed: {str(e)}")
    
    if time.time() - start_time > RENDER_TIMEOUT:
        raise PipelineError("Timeout during parsing")
    
    try:
        renderer = AnimationRenderer(spec, width=width, height=height)
        video_bytes = renderer.render_to_bytes()
    except Exception as e:
        raise PipelineError(f"Rendering failed: {str(e)}")
    
    if time.time() - start_time > RENDER_TIMEOUT:
        raise PipelineError("Timeout during rendering")
    
    video_b64 = base64.b64encode(video_bytes).decode('utf-8')
    
    if save_metadata:
        try:
            save_video_metadata(
                dsl_script=dsl_script,
                video_base64=video_bytes,
                prompt=prompt,
                model=model,
                duration=duration,
                fps=fps,
                width=width,
                height=height
            )
        except Exception as e:
            print(f"Warning: Failed to save metadata: {e}")
    
    return (video_b64, dsl_script)


def generate_video_from_dsl(
    dsl_script: str,
    width: int = 640,
    height: int = 360,
    save_metadata: bool = True
) -> str:
    width = min(max(width, 320), MAX_WIDTH)
    height = min(max(height, 180), MAX_HEIGHT)
    
    try:
        spec = parse_dsl(dsl_script)
    except DSLParseError as e:
        raise PipelineError(f"Invalid DSL script: {str(e)}")
    except DSLValidationError as e:
        raise PipelineError(f"DSL validation failed: {str(e)}")
    
    try:
        renderer = AnimationRenderer(spec, width=width, height=height)
        video_bytes = renderer.render_to_bytes()
    except Exception as e:
        raise PipelineError(f"Rendering failed: {str(e)}")
    
    video_b64 = base64.b64encode(video_bytes).decode('utf-8')
    
    if save_metadata:
        try:
            save_video_metadata(
                dsl_script=dsl_script,
                video_base64=video_bytes,
                model="dsl",
                duration=spec.duration,
                fps=spec.fps,
                width=width,
                height=height
            )
        except Exception as e:
            print(f"Warning: Failed to save metadata: {e}")
    
    return video_b64
