import os
import re
from typing import Optional

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

DSL_SYSTEM_PROMPT = """You are a video animation DSL generator. Convert user prompts into a Mini-DSL animation script.

RULES:
1. Output ONLY the DSL script, no explanations
2. Use ONLY these commands:
   - BACKGROUND #RRGGBB
   - TEXT "content" AT x,y SIZE pixels COLOR #RRGGBB [MOVE TO x,y DUR seconds]
   - SHAPE CIRCLE ID name AT x,y RADIUS pixels COLOR #RRGGBB [MOVE TO x,y DUR seconds EASE linear]
   - SHAPE RECT ID name AT x,y WIDTH pixels HEIGHT pixels COLOR #RRGGBB [MOVE TO x,y DUR seconds EASE linear]
   - MOVE object_id TO x,y DUR seconds EASE linear
   - FPS number (max 24)
   - DURATION seconds (max 6)

3. Canvas size is 640x360 pixels
4. All colors must be hex format #RRGGBB
5. Keep animations simple and clean
6. Maximum 6 seconds duration
7. Maximum 24 FPS

EXAMPLE OUTPUT for "bouncing red ball":
BACKGROUND #1a1a2e
FPS 24
DURATION 3
SHAPE CIRCLE ID ball AT 50,180 RADIUS 30 COLOR #FF4444 MOVE TO 590,180 DUR 3 EASE linear

EXAMPLE OUTPUT for "hello world text":
BACKGROUND #202030
FPS 24
DURATION 2
TEXT "Hello World" AT 200,160 SIZE 48 COLOR #FFFFFF MOVE TO 300,160 DUR 2
"""


def translate_prompt_to_dsl(
    prompt: str, 
    duration: float = 3.0, 
    fps: int = 24,
    model: str = "auto"
) -> str:
    if model == "auto":
        if GROQ_API_KEY:
            model = "groq"
        elif OPENAI_API_KEY:
            model = "openai"
        else:
            model = "fallback"
    
    if model == "groq" and GROQ_API_KEY:
        return translate_with_groq(prompt, duration, fps)
    elif model == "openai" and OPENAI_API_KEY:
        return translate_with_openai(prompt, duration, fps)
    else:
        return generate_fallback_dsl(prompt, duration, fps)


def translate_with_groq(prompt: str, duration: float, fps: int) -> str:
    try:
        from groq import Groq
        
        client = Groq(api_key=GROQ_API_KEY)
        
        user_message = f"""Create a DSL animation script for: {prompt}

Settings: duration={min(duration, 6.0)} seconds, fps={min(fps, 24)}

Output only the DSL script, nothing else."""

        response = client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=[
                {"role": "system", "content": DSL_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1024,
        )
        
        content = response.choices[0].message.content
        if content is None:
            return generate_fallback_dsl(prompt, duration, fps)
        
        dsl_output = clean_dsl_output(content)
        return dsl_output
    
    except Exception as e:
        print(f"Groq/Llama error: {e}, using fallback")
        return generate_fallback_dsl(prompt, duration, fps)


def translate_with_openai(prompt: str, duration: float, fps: int) -> str:
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        user_message = f"""Create a DSL animation script for: {prompt}

Settings: duration={min(duration, 6.0)} seconds, fps={min(fps, 24)}

Output only the DSL script, nothing else."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": DSL_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1024,
        )
        
        content = response.choices[0].message.content
        if content is None:
            return generate_fallback_dsl(prompt, duration, fps)
        
        dsl_output = clean_dsl_output(content)
        return dsl_output
    
    except Exception as e:
        print(f"OpenAI error: {e}, using fallback")
        return generate_fallback_dsl(prompt, duration, fps)


def clean_dsl_output(content: str) -> str:
    dsl_output = content.strip()
    
    if dsl_output.startswith("```"):
        lines = dsl_output.split('\n')
        if lines[-1].strip() == '```':
            dsl_output = '\n'.join(lines[1:-1])
        else:
            dsl_output = '\n'.join(lines[1:])
    
    return dsl_output


def generate_fallback_dsl(prompt: str, duration: float = 3.0, fps: int = 24) -> str:
    prompt_lower = prompt.lower()
    duration = min(duration, 6.0)
    fps = min(fps, 24)
    
    if any(word in prompt_lower for word in ['text', 'word', 'title', 'caption', 'hello', 'message']):
        text = extract_quoted_text(prompt) or "Hello World"
        return f"""BACKGROUND #202030
FPS {fps}
DURATION {duration}
TEXT "{text}" AT 180,150 SIZE 48 COLOR #FFFFFF MOVE TO 280,150 DUR {duration}
"""
    
    elif any(word in prompt_lower for word in ['ball', 'circle', 'bounce', 'dot', 'sphere']):
        color = extract_color(prompt) or "#FF4444"
        return f"""BACKGROUND #1a1a2e
FPS {fps}
DURATION {duration}
SHAPE CIRCLE ID ball AT 50,180 RADIUS 35 COLOR {color} MOVE TO 550,180 DUR {duration} EASE linear
"""
    
    elif any(word in prompt_lower for word in ['square', 'rect', 'box', 'rectangle']):
        color = extract_color(prompt) or "#44FF44"
        return f"""BACKGROUND #1a1a2e
FPS {fps}
DURATION {duration}
SHAPE RECT ID box AT 50,130 WIDTH 80 HEIGHT 80 COLOR {color} MOVE TO 510,130 DUR {duration} EASE linear
"""
    
    elif any(word in prompt_lower for word in ['slide', 'move', 'animate']):
        return f"""BACKGROUND #202040
FPS {fps}
DURATION {duration}
SHAPE CIRCLE ID obj1 AT 100,100 RADIUS 25 COLOR #FF6600 MOVE TO 500,100 DUR {duration} EASE linear
SHAPE RECT ID obj2 AT 100,220 WIDTH 50 HEIGHT 50 COLOR #0066FF MOVE TO 500,220 DUR {duration} EASE linear
"""
    
    else:
        return f"""BACKGROUND #1e1e2e
FPS {fps}
DURATION {duration}
SHAPE CIRCLE ID ball AT 100,180 RADIUS 30 COLOR #6699FF MOVE TO 540,180 DUR {duration} EASE linear
TEXT "Animation" AT 220,50 SIZE 36 COLOR #FFFFFF
"""


def extract_quoted_text(prompt: str) -> str:
    match = re.search(r'"([^"]+)"', prompt)
    if match:
        return match.group(1)
    match = re.search(r"'([^']+)'", prompt)
    if match:
        return match.group(1)
    return ""


def extract_color(prompt: str) -> str:
    color_map = {
        'red': '#FF4444',
        'blue': '#4444FF',
        'green': '#44FF44',
        'yellow': '#FFFF44',
        'orange': '#FF8844',
        'purple': '#AA44FF',
        'pink': '#FF44AA',
        'white': '#FFFFFF',
        'cyan': '#44FFFF',
        'neon': '#00FF88',
    }
    prompt_lower = prompt.lower()
    for color_name, hex_val in color_map.items():
        if color_name in prompt_lower:
            return hex_val
    return ""


def get_available_models() -> dict:
    models = {"fallback": True}
    if GROQ_API_KEY:
        models["groq"] = True
    if OPENAI_API_KEY:
        models["openai"] = True
    return models
