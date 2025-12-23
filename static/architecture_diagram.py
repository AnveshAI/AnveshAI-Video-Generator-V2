
from PIL import Image, ImageDraw, ImageFont
import os

# Create high-resolution image
width, height = 2000, 1400
img = Image.new('RGB', (width, height), '#0a0e1a')
draw = ImageDraw.Draw(img)

# Load fonts with fallback
try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    heading_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    subheading_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
except:
    title_font = heading_font = subheading_font = text_font = small_font = ImageFont.load_default()

# Professional color palette
colors = {
    'primary': '#6366f1',
    'secondary': '#8b5cf6', 
    'accent': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#06b6d4',
    'text': '#f1f5f9',
    'text_dim': '#94a3b8',
    'bg_dark': '#0f172a',
    'bg_box': '#1e293b',
    'bg_highlight': '#334155',
    'border': '#475569',
}

def draw_gradient_box(x, y, w, h, title, color, include_shadow=True):
    """Draw a modern box with gradient effect and shadow"""
    if include_shadow:
        shadow_offset = 8
        draw.rounded_rectangle(
            [x + shadow_offset, y + shadow_offset, x + w + shadow_offset, y + h + shadow_offset],
            radius=15, fill='#000000'
        )
    
    # Main box
    draw.rounded_rectangle([x, y, x + w, y + h], radius=15, fill=colors['bg_box'], outline=color, width=3)
    
    # Title bar with gradient effect
    draw.rounded_rectangle([x, y, x + w, y + 50], radius=15, fill=color)
    draw.rectangle([x, y + 35, x + w, y + 50], fill=color)
    
    # Title text
    bbox = draw.textbbox((0, 0), title, font=heading_font)
    text_w = bbox[2] - bbox[0]
    draw.text((x + (w - text_w) // 2, y + 13), title, fill='#ffffff', font=heading_font)

def draw_styled_arrow(x1, y1, x2, y2, color, width=5, label=None):
    """Draw arrow with glow effect and label"""
    import math
    
    # Glow layers
    for i, w in enumerate([width + 6, width + 3, width]):
        alpha_color = color if i == 2 else color + '80'
        draw.line([x1, y1, x2, y2], fill=color, width=w)
    
    # Arrowhead
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx * dx + dy * dy)
    
    if length > 0:
        dx /= length
        dy /= length
        angle = 0.5
        arrow_len = 25
        
        x3 = x2 - arrow_len * (dx * math.cos(angle) + dy * math.sin(angle))
        y3 = y2 - arrow_len * (dy * math.cos(angle) - dx * math.sin(angle))
        x4 = x2 - arrow_len * (dx * math.cos(angle) - dy * math.sin(angle))
        y4 = y2 - arrow_len * (dy * math.cos(angle) + dx * math.sin(angle))
        
        draw.polygon([x2, y2, x3, y3, x4, y4], fill=color)
    
    # Label
    if label:
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        bbox = draw.textbbox((0, 0), label, font=small_font)
        label_w = bbox[2] - bbox[0]
        label_h = bbox[3] - bbox[1]
        
        draw.rounded_rectangle(
            [mid_x - label_w//2 - 8, mid_y - label_h//2 - 5,
             mid_x + label_w//2 + 8, mid_y + label_h//2 + 5],
            radius=6, fill=colors['bg_dark'], outline=color, width=2
        )
        draw.text((mid_x - label_w//2, mid_y - label_h//2), label, fill=colors['text'], font=small_font)

def draw_bullet_list(x, y, items, icon="•"):
    """Draw styled bullet list"""
    for i, item in enumerate(items):
        y_pos = y + i * 26
        draw.text((x, y_pos), icon, fill=colors['accent'], font=text_font)
        draw.text((x + 20, y_pos), item, fill=colors['text'], font=text_font)

# Header
draw.text((60, 50), "AnveshAI", fill=colors['primary'], font=title_font)
draw.text((60, 110), "System Architecture & Data Flow Diagram", fill=colors['text_dim'], font=subheading_font)
draw.rectangle([60, 150, 1940, 154], fill=colors['border'])

# ========== LAYER 1: CLIENT & API (Top Row) ==========
y1 = 200

# Web Client
draw_gradient_box(60, y1, 420, 220, "🌐 Web Client Interface", colors['primary'])
draw_bullet_list(80, y1 + 65, [
    "HTML5 + Vanilla JavaScript",
    "Natural Language Prompt Input",
    "DSL Script Code Editor",
    "Real-time Video Preview",
    "Model Selection (Auto/Groq/OpenAI)",
    "Video Gallery with Download/Delete",
])

# FastAPI Backend
draw_gradient_box(520, y1, 480, 220, "⚙️ FastAPI REST API", colors['secondary'])
draw_bullet_list(540, y1 + 65, [
    "POST /generate - NL → Video",
    "POST /generate-dsl - DSL → Video",
    "GET /gallery - Video Library UI",
    "GET /api/videos - List All Videos",
    "GET /models - Model Status Check",
    "DELETE /api/videos/{id} - Remove Video",
])

# Response Handler
draw_gradient_box(1040, y1, 450, 220, "📦 Response Handler", colors['info'])
draw_bullet_list(1060, y1 + 65, [
    "Base64 Encoded MP4 Video",
    "Generated/Provided DSL Script",
    "Metadata (model, duration, fps)",
    "Auto-saved to SQLite Database",
    "Video ID for Future Retrieval",
])

# Database (Side Panel)
draw_gradient_box(1530, y1, 410, 480, "💾 SQLite Database", colors['accent'])
draw.text((1550, y1 + 65), "videos.db Schema:", fill=colors['text'], font=subheading_font)
draw_bullet_list(1550, y1 + 100, [
    "id (PRIMARY KEY, AUTO)",
    "prompt (TEXT)",
    "dsl_script (TEXT)",
    "model_used (TEXT)",
    "duration, fps (NUMERIC)",
    "width, height (INTEGER)",
    "video_base64 (BLOB)",
    "created_at (TIMESTAMP)",
])
draw.text((1550, y1 + 310), "Operations:", fill=colors['text'], font=subheading_font)
draw_bullet_list(1550, y1 + 345, [
    "✓ Auto-save on generation",
    "✓ List all videos with metadata",
    "✓ Download by ID",
    "✓ Delete by ID",
])

# ========== LAYER 2: LLM TRANSLATION ==========
y2 = 470

draw_gradient_box(60, y2, 960, 200, "🤖 LLM Translation Engine", colors['warning'])
draw.text((80, y2 + 65), "Multi-Model AI Backend:", fill=colors['text'], font=subheading_font)
draw_bullet_list(80, y2 + 100, [
    "Primary: Groq Llama 4 Maverick (meta-llama/llama-4-maverick-17b-128e-instruct)",
    "Fallback: OpenAI GPT-4o (optional, requires API key)",
    "Offline Mode: Template-based DSL Generator",
    "Output: Validated Mini-DSL Animation Script",
])

# ========== LAYER 3: DSL PARSER ==========
y3 = 720

draw_gradient_box(60, y3, 960, 190, "🔍 DSL Parser & Validator", colors['primary'])
draw_bullet_list(80, y3 + 65, [
    "Lexical Analysis & Tokenization",
    "Command Parsing (BACKGROUND, TEXT, SHAPE, MOVE)",
    "Coordinate & Hex Color Validation (#RRGGBB)",
    "Resource Limit Enforcement (resolution, duration, objects)",
    "Output: AnimationSpec Object with validated commands",
])

# ========== LAYER 4: RENDERING ENGINE ==========
y4 = 960

draw_gradient_box(60, y4, 960, 190, "🎨 PIL Rendering Engine", colors['accent'])
draw_bullet_list(80, y4 + 65, [
    "Frame-by-frame PIL Image Generation",
    "Linear/Ease-in/Ease-out Animation Interpolation",
    "Shape Rendering (Circle, Rectangle with AA)",
    "Text with Anti-aliasing & Custom Fonts",
    "imageio-ffmpeg MP4 Export (H.264 codec)",
])

# Security Panel
draw_gradient_box(1530, 730, 410, 420, "🔒 Security & Limits", colors['danger'])
draw.text((1550, 795), "Security Controls:", fill=colors['text'], font=subheading_font)
draw_bullet_list(1550, 830, [
    "✓ No Python Code Execution",
    "✓ DSL-Only Approach",
    "✓ Command Whitelist Only",
    "✓ Hex Color Validation",
    "✓ Coordinate Clamping",
])
draw.text((1550, 985), "Resource Limits:", fill=colors['text'], font=subheading_font)
draw_bullet_list(1550, 1020, [
    "Max Resolution: 1280×720",
    "Max Duration: 6 seconds",
    "Max FPS: 24 frames/sec",
    "Max Frames: 300 total",
    "Max Objects: 50/scene",
    "Render Timeout: 30 sec",
])

# ========== DATA FLOW ARROWS ==========

# Client → API
draw_styled_arrow(480, 310, 520, 310, colors['primary'], label="HTTP POST")

# API → Response
draw_styled_arrow(1000, 310, 1040, 310, colors['info'], label="JSON")

# API → LLM
draw_styled_arrow(760, 420, 760, 470, colors['warning'], label="Prompt")

# LLM → Parser
draw_styled_arrow(540, 670, 540, 720, colors['primary'], label="DSL")

# Parser → Renderer
draw_styled_arrow(540, 910, 540, 960, colors['accent'], label="AnimationSpec")

# Renderer → DB (save)
draw_styled_arrow(1020, 1050, 1530, 920, colors['secondary'], label="Save MP4")

# Renderer → API Response
draw_styled_arrow(60, 1050, 200, 420, colors['accent'], label="MP4 Bytes", width=4)

# Direct DSL Path (bypass LLM)
draw_styled_arrow(900, 420, 900, 720, colors['text_dim'], width=3, label="Direct DSL")

# DB → API (retrieve)
draw_styled_arrow(1530, 680, 1000, 420, colors['secondary'], width=3, label="Retrieve")

# ========== LEGEND ==========
legend_y = 1230
draw.text((60, legend_y), "Data Flow Legend:", fill=colors['text'], font=subheading_font)

legend_items = [
    (250, "Primary Path", colors['primary']),
    (450, "LLM Processing", colors['warning']),
    (650, "Database Ops", colors['secondary']),
    (850, "Direct DSL", colors['text_dim']),
    (1050, "Response Flow", colors['info']),
]

for x, label, color in legend_items:
    draw.line([x, legend_y + 12, x + 90, legend_y + 12], fill=color, width=5)
    draw.polygon([x + 90, legend_y + 12, x + 80, legend_y + 7, x + 80, legend_y + 17], fill=color)
    draw.text((x + 100, legend_y + 5), label, fill=colors['text'], font=small_font)

# Footer
draw.text((60, 1320), "AnveshAI - Secure Programmatic Video Generation Pipeline", 
          fill=colors['text_dim'], font=small_font)
draw.text((1650, 1320), "Generated: 2025", fill=colors['text_dim'], font=small_font)

# Save
output_path = "static/architecture.png"
img.save(output_path, quality=95, optimize=True)
file_size = os.path.getsize(output_path) / 1024

print(f"✓ Professional architecture diagram saved to {output_path}")
print(f"  Dimensions: {width}×{height}px")
print(f"  File size: {file_size:.1f} KB")
