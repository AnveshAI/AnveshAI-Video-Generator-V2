import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from .constants import (
    ALLOWED_COMMANDS, ALLOWED_SHAPE_TYPES, ALLOWED_EASE_TYPES,
    VALID_COLORS_PATTERN, MAX_OBJECTS, MAX_DURATION, MAX_FPS, MAX_FRAMES,
    MAX_WIDTH, MAX_HEIGHT
)


class DSLParseError(Exception):
    pass


class DSLValidationError(Exception):
    pass


@dataclass
class BackgroundCommand:
    color: str


@dataclass
class TextCommand:
    text: str
    x: int
    y: int
    size: int = 32
    color: str = "#FFFFFF"
    move_to: Optional[Tuple[int, int]] = None
    move_duration: float = 0.0
    obj_id: str = ""


@dataclass
class ShapeCommand:
    shape_type: str
    obj_id: str
    x: int
    y: int
    color: str = "#FFFFFF"
    radius: int = 20
    width: int = 50
    height: int = 50
    move_to: Optional[Tuple[int, int]] = None
    move_duration: float = 0.0
    ease: str = "linear"


@dataclass
class MoveCommand:
    obj_id: str
    to_x: int
    to_y: int
    duration: float
    ease: str = "linear"


@dataclass
class AnimationSpec:
    background: str = "#202020"
    fps: int = 24
    duration: float = 3.0
    objects: List[Any] = field(default_factory=list)
    moves: List[MoveCommand] = field(default_factory=list)


def validate_color(color: str) -> bool:
    if not color or not isinstance(color, str):
        return False
    return bool(re.match(VALID_COLORS_PATTERN, color))


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b)


def parse_dsl(dsl_script: str) -> AnimationSpec:
    spec = AnimationSpec()
    lines = dsl_script.strip().split('\n')
    object_count = 0
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        tokens = tokenize_line(line)
        if not tokens:
            continue
        
        command = tokens[0].upper()
        
        if command not in ALLOWED_COMMANDS:
            raise DSLParseError(f"Line {line_num}: Unknown command '{command}'. Allowed: {ALLOWED_COMMANDS}")
        
        try:
            if command == 'BACKGROUND':
                color = tokens[1] if len(tokens) > 1 else "#202020"
                if not validate_color(color):
                    raise DSLValidationError(f"Line {line_num}: Invalid color '{color}'. Use hex format like #FF0000 (red), #00FF00 (green), #0000FF (blue)")
                spec.background = color
            
            elif command == 'FPS':
                fps = int(tokens[1]) if len(tokens) > 1 else 24
                if fps < 1 or fps > MAX_FPS:
                    raise DSLValidationError(f"Line {line_num}: FPS must be between 1 and {MAX_FPS}")
                spec.fps = fps
            
            elif command == 'DURATION':
                duration = float(tokens[1]) if len(tokens) > 1 else 3.0
                if duration <= 0 or duration > MAX_DURATION:
                    raise DSLValidationError(f"Line {line_num}: Duration must be between 0 and {MAX_DURATION} seconds")
                spec.duration = duration
            
            elif command == 'TEXT':
                object_count += 1
                if object_count > MAX_OBJECTS:
                    raise DSLValidationError(f"Line {line_num}: Too many objects. Maximum is {MAX_OBJECTS}")
                text_cmd = parse_text_command(tokens[1:], line_num)
                spec.objects.append(text_cmd)
            
            elif command == 'SHAPE':
                object_count += 1
                if object_count > MAX_OBJECTS:
                    raise DSLValidationError(f"Line {line_num}: Too many objects. Maximum is {MAX_OBJECTS}")
                shape_cmd = parse_shape_command(tokens[1:], line_num)
                spec.objects.append(shape_cmd)
            
            elif command == 'MOVE':
                move_cmd = parse_move_command(tokens[1:], line_num)
                spec.moves.append(move_cmd)
        
        except (IndexError, ValueError) as e:
            raise DSLParseError(f"Line {line_num}: Invalid syntax - {str(e)}")
    
    total_frames = int(spec.fps * spec.duration)
    if total_frames > MAX_FRAMES:
        raise DSLValidationError(f"Total frames ({total_frames}) exceeds maximum ({MAX_FRAMES}). Reduce duration or FPS.")
    
    return spec


def tokenize_line(line: str) -> List[str]:
    tokens = []
    current = ""
    in_quotes = False
    
    for char in line:
        if char == '"' and not in_quotes:
            in_quotes = True
        elif char == '"' and in_quotes:
            in_quotes = False
            tokens.append(current)
            current = ""
        elif char == ' ' and not in_quotes:
            if current:
                tokens.append(current)
                current = ""
        else:
            current += char
    
    if current:
        tokens.append(current)
    
    return tokens


def parse_text_command(tokens: List[str], line_num: int) -> TextCommand:
    if not tokens:
        raise DSLParseError(f"Line {line_num}: TEXT requires text content")
    
    text = tokens[0]
    cmd = TextCommand(text=text, x=100, y=100, obj_id=f"text_{line_num}")
    
    i = 1
    while i < len(tokens):
        keyword = tokens[i].upper()
        
        if keyword == 'AT' and i + 1 < len(tokens):
            coords = tokens[i + 1].split(',')
            if len(coords) == 2:
                cmd.x = clamp_coord(int(coords[0]), MAX_WIDTH)
                cmd.y = clamp_coord(int(coords[1]), MAX_HEIGHT)
            i += 2
        elif keyword == 'SIZE' and i + 1 < len(tokens):
            cmd.size = min(max(int(tokens[i + 1]), 8), 200)
            i += 2
        elif keyword == 'COLOR' and i + 1 < len(tokens):
            color = tokens[i + 1]
            if not validate_color(color):
                raise DSLValidationError(f"Line {line_num}: Invalid color '{color}'. Use hex format like #FF0000, #00FF00, #0000FF")
            cmd.color = color
            i += 2
        elif keyword == 'ID' and i + 1 < len(tokens):
            cmd.obj_id = tokens[i + 1]
            i += 2
        elif keyword == 'MOVE' and i + 2 < len(tokens) and tokens[i + 1].upper() == 'TO':
            coords = tokens[i + 2].split(',')
            if len(coords) == 2:
                cmd.move_to = (clamp_coord(int(coords[0]), MAX_WIDTH), clamp_coord(int(coords[1]), MAX_HEIGHT))
            i += 3
        elif keyword == 'DUR' and i + 1 < len(tokens):
            dur_val = float(tokens[i + 1])
            cmd.move_duration = max(0.0, min(dur_val, MAX_DURATION))
            i += 2
        else:
            i += 1
    
    return cmd


def parse_shape_command(tokens: List[str], line_num: int) -> ShapeCommand:
    if not tokens:
        raise DSLParseError(f"Line {line_num}: SHAPE requires a type (CIRCLE or RECT)")
    
    shape_type = tokens[0].upper()
    if shape_type not in ALLOWED_SHAPE_TYPES:
        raise DSLValidationError(f"Line {line_num}: Unknown shape type '{shape_type}'. Allowed: {ALLOWED_SHAPE_TYPES}")
    
    cmd = ShapeCommand(shape_type=shape_type, obj_id=f"shape_{line_num}", x=50, y=50)
    
    i = 1
    while i < len(tokens):
        keyword = tokens[i].upper()
        
        if keyword == 'ID' and i + 1 < len(tokens):
            cmd.obj_id = tokens[i + 1]
            i += 2
        elif keyword == 'AT' and i + 1 < len(tokens):
            coords = tokens[i + 1].split(',')
            if len(coords) == 2:
                cmd.x = clamp_coord(int(coords[0]), MAX_WIDTH)
                cmd.y = clamp_coord(int(coords[1]), MAX_HEIGHT)
            i += 2
        elif keyword == 'RADIUS' and i + 1 < len(tokens):
            cmd.radius = min(max(int(tokens[i + 1]), 1), 500)
            i += 2
        elif keyword == 'WIDTH' and i + 1 < len(tokens):
            cmd.width = min(max(int(tokens[i + 1]), 1), MAX_WIDTH)
            i += 2
        elif keyword == 'HEIGHT' and i + 1 < len(tokens):
            cmd.height = min(max(int(tokens[i + 1]), 1), MAX_HEIGHT)
            i += 2
        elif keyword == 'COLOR' and i + 1 < len(tokens):
            color = tokens[i + 1]
            if not validate_color(color):
                raise DSLValidationError(f"Line {line_num}: Invalid color '{color}'. Use hex format like #FF0000, #00FF00, #0000FF")
            cmd.color = color
            i += 2
        elif keyword == 'MOVE' and i + 2 < len(tokens) and tokens[i + 1].upper() == 'TO':
            coords = tokens[i + 2].split(',')
            if len(coords) == 2:
                cmd.move_to = (clamp_coord(int(coords[0]), MAX_WIDTH), clamp_coord(int(coords[1]), MAX_HEIGHT))
            i += 3
        elif keyword == 'DUR' and i + 1 < len(tokens):
            dur_val = float(tokens[i + 1])
            cmd.move_duration = max(0.0, min(dur_val, MAX_DURATION))
            i += 2
        elif keyword == 'EASE' and i + 1 < len(tokens):
            ease = tokens[i + 1].lower()
            if ease in ALLOWED_EASE_TYPES:
                cmd.ease = ease
            i += 2
        else:
            i += 1
    
    return cmd


def parse_move_command(tokens: List[str], line_num: int) -> MoveCommand:
    if len(tokens) < 4:
        raise DSLParseError(f"Line {line_num}: MOVE requires: obj_id TO x,y DUR seconds")
    
    obj_id = tokens[0]
    to_x, to_y = 0, 0
    duration = 1.0
    ease = "linear"
    
    i = 1
    while i < len(tokens):
        keyword = tokens[i].upper()
        
        if keyword == 'TO' and i + 1 < len(tokens):
            coords = tokens[i + 1].split(',')
            if len(coords) == 2:
                to_x = clamp_coord(int(coords[0]), MAX_WIDTH)
                to_y = clamp_coord(int(coords[1]), MAX_HEIGHT)
            i += 2
        elif keyword == 'DUR' and i + 1 < len(tokens):
            dur_val = float(tokens[i + 1])
            duration = max(0.1, min(dur_val, MAX_DURATION))
            i += 2
        elif keyword == 'EASE' and i + 1 < len(tokens):
            ease = tokens[i + 1].lower()
            if ease not in ALLOWED_EASE_TYPES:
                ease = "linear"
            i += 2
        else:
            i += 1
    
    return MoveCommand(obj_id=obj_id, to_x=to_x, to_y=to_y, duration=duration, ease=ease)


def clamp_coord(val: int, max_val: int) -> int:
    return max(0, min(val, max_val))
