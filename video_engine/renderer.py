import tempfile
import os
from typing import List, Tuple, Any
from PIL import Image, ImageDraw, ImageFont
import imageio
import numpy as np

from .dsl_parser import (
    AnimationSpec, TextCommand, ShapeCommand, MoveCommand,
    hex_to_rgb
)
from .constants import MAX_WIDTH, MAX_HEIGHT, RENDER_TIMEOUT


def ease_linear(t: float) -> float:
    return t


def ease_in(t: float) -> float:
    return t * t


def ease_out(t: float) -> float:
    return 1 - (1 - t) * (1 - t)


EASE_FUNCTIONS = {
    'linear': ease_linear,
    'ease-in': ease_in,
    'ease-out': ease_out,
}


class AnimationRenderer:
    def __init__(self, spec: AnimationSpec, width: int = 640, height: int = 360):
        self.spec = spec
        self.width = min(width, MAX_WIDTH)
        self.height = min(height, MAX_HEIGHT)
        self.frames: List[Image.Image] = []
        self.total_frames = int(spec.fps * spec.duration)
        self.bg_color = hex_to_rgb(spec.background)
        
        self.object_positions = {}
        self.object_moves = {}
        
        self._prepare_movements()
    
    def _prepare_movements(self):
        for obj in self.spec.objects:
            if isinstance(obj, (TextCommand, ShapeCommand)):
                self.object_positions[obj.obj_id] = (obj.x, obj.y)
                
                if obj.move_to and obj.move_duration > 0:
                    ease = getattr(obj, 'ease', 'linear')
                    self.object_moves[obj.obj_id] = {
                        'from': (obj.x, obj.y),
                        'to': obj.move_to,
                        'start_frame': 0,
                        'end_frame': int(obj.move_duration * self.spec.fps),
                        'ease': ease
                    }
        
        for move in self.spec.moves:
            if move.obj_id in self.object_positions:
                current_pos = self.object_positions[move.obj_id]
                self.object_moves[move.obj_id] = {
                    'from': current_pos,
                    'to': (move.to_x, move.to_y),
                    'start_frame': 0,
                    'end_frame': int(move.duration * self.spec.fps),
                    'ease': move.ease
                }
    
    def _get_position(self, obj_id: str, frame: int) -> Tuple[int, int]:
        if obj_id not in self.object_moves:
            return self.object_positions.get(obj_id, (0, 0))
        
        move = self.object_moves[obj_id]
        start_frame = move['start_frame']
        end_frame = move['end_frame']
        
        if frame < start_frame:
            return move['from']
        if frame >= end_frame:
            return move['to']
        
        progress = (frame - start_frame) / max(1, end_frame - start_frame)
        ease_func = EASE_FUNCTIONS.get(move['ease'], ease_linear)
        t = ease_func(progress)
        
        x = int(move['from'][0] + (move['to'][0] - move['from'][0]) * t)
        y = int(move['from'][1] + (move['to'][1] - move['from'][1]) * t)
        
        return (x, y)
    
    def _get_font(self, size: int):
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except:
            try:
                return ImageFont.truetype("DejaVuSans.ttf", size)
            except:
                return ImageFont.load_default()
    
    def _draw_text(self, draw: Any, cmd: TextCommand, frame: int):
        x, y = self._get_position(cmd.obj_id, frame)
        color = hex_to_rgb(cmd.color)
        font = self._get_font(cmd.size)
        draw.text((x, y), cmd.text, fill=color, font=font)
    
    def _draw_shape(self, draw: Any, cmd: ShapeCommand, frame: int):
        x, y = self._get_position(cmd.obj_id, frame)
        color = hex_to_rgb(cmd.color)
        
        if cmd.shape_type == 'CIRCLE':
            r = cmd.radius
            draw.ellipse((x - r, y - r, x + r, y + r), fill=color)
        elif cmd.shape_type == 'RECT':
            w, h = cmd.width, cmd.height
            draw.rectangle((x, y, x + w, y + h), fill=color)
    
    def _get_contrasting_color(self, rgb: Tuple[int, int, int]) -> Tuple[int, int, int, int]:
        """Calculate contrasting color based on background luminosity"""
        r, g, b = rgb
        # Calculate luminosity using standard formula
        luminosity = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        
        # If background is light (luminosity > 0.5), use dark text; otherwise use light text
        if luminosity > 0.5:
            # Light background: use dark gray/black with opacity
            return (50, 50, 50, 200)
        else:
            # Dark background: use white with opacity
            return (255, 255, 255, 200)
    
    def _draw_watermark(self, img: Image.Image):
        """Draw AnveshAI watermark at bottom-right corner, scaled to background"""
        draw = ImageDraw.Draw(img, 'RGBA')
        watermark_text = "AnveshAI"
        # Make watermark much bigger - scales with height
        font_size = max(24, int(self.height / 12))
        font = self._get_font(font_size)
        
        # Get text bounding box for positioning
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Position at bottom-right with padding
        padding = 15
        x = self.width - text_width - padding
        y = self.height - text_height - padding
        
        # Choose color based on background
        watermark_color = self._get_contrasting_color(self.bg_color)
        draw.text((x, y), watermark_text, fill=watermark_color, font=font)
    
    def render_frame(self, frame_num: int) -> Image.Image:
        img = Image.new('RGB', (self.width, self.height), color=self.bg_color)
        draw = ImageDraw.Draw(img)
        
        for obj in self.spec.objects:
            if isinstance(obj, TextCommand):
                self._draw_text(draw, obj, frame_num)
            elif isinstance(obj, ShapeCommand):
                self._draw_shape(draw, obj, frame_num)
        
        # Add watermark
        self._draw_watermark(img)
        
        return img
    
    def render_all_frames(self) -> List[Image.Image]:
        self.frames = []
        for i in range(self.total_frames):
            frame = self.render_frame(i)
            self.frames.append(frame)
        return self.frames
    
    def _frames_to_arrays(self) -> List[np.ndarray]:
        return [np.array(frame) for frame in self.frames]
    
    def save_mp4(self, output_path: str) -> str:
        if not self.frames:
            self.render_all_frames()
        
        frame_arrays = self._frames_to_arrays()
        imageio.mimsave(output_path, frame_arrays, fps=self.spec.fps, macro_block_size=1)
        return output_path
    
    def render_to_bytes(self) -> bytes:
        if not self.frames:
            self.render_all_frames()
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            frame_arrays = self._frames_to_arrays()
            imageio.mimsave(tmp_path, frame_arrays, fps=self.spec.fps, macro_block_size=1)
            with open(tmp_path, 'rb') as f:
                video_bytes = f.read()
            return video_bytes
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
