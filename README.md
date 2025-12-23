# AnveshAI — Video Generator V2

A secure, production-safe programmatic video generator that uses AI to create animations from natural language descriptions. Simply describe what you want to see, and AnveshAI generates an MP4 video automatically.

## Features

✨ **AI-Powered Video Generation**
- Generate animations from simple English descriptions
- Support for multiple AI models (Groq Llama, OpenAI GPT-4o, or fallback template)
- All videos automatically stored with full metadata

🎨 **Web Interface**
- Interactive UI for generating videos with instant preview
- Video gallery showing all generated animations
- Download and delete functionality for stored videos

⚡ **Fast & Secure**
- No Python code execution—safe DSL (Domain-Specific Language) only
- Strict resource limits prevent abuse
- Encrypted API key management

📊 **RESTful API**
- Full API for programmatic video generation
- JSON responses with base64-encoded videos
- Video management endpoints

## Quick Start

### Using the Web UI

1. **Open the Generator**: Navigate to `/` in your browser
2. **Write a Prompt**: Describe what animation you want (e.g., "a red ball bouncing across a dark screen")
3. **Generate**: Click the generate button and wait for your video
4. **View Gallery**: Check out all your videos at `/gallery`

### Using the API

Generate a video from a prompt:

```bash
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a bouncing red ball",
    "duration": 3,
    "fps": 24,
    "model": "auto"
  }'
```

List all generated videos:

```bash
curl http://localhost:5000/api/videos
```

Download a specific video:

```bash
curl http://localhost:5000/api/videos/1/download > my_video.mp4
```

Delete a video:

```bash
curl -X DELETE http://localhost:5000/api/videos/1
```

## Supported AI Models

- **`auto`** - Automatically selects the best available model
- **`groq`** - Llama 4 Maverick (fastest, requires `GROQ_API_KEY`)
- **`openai`** - GPT-4o (requires `OPENAI_API_KEY`)
- **`fallback`** - Template-based generation (no API key needed)

## Mini-DSL Reference

For advanced users, you can write animations in AnveshAI's simple language:

```
BACKGROUND #1a1a2e
FPS 24
DURATION 3
SHAPE CIRCLE ID ball AT 50,180 RADIUS 30 COLOR #FF4444 MOVE TO 550,180 DUR 3 EASE linear
TEXT "Hello" AT 280,50 SIZE 36 COLOR #FFFFFF
```

**Commands:**
- `BACKGROUND #RRGGBB` - Set background color
- `FPS number` - Set frames per second (1-24)
- `DURATION seconds` - Total animation length (0.5-6 seconds)
- `TEXT "content" AT x,y SIZE pixels COLOR #RRGGBB [MOVE TO x,y DUR seconds]` - Add text
- `SHAPE CIRCLE/RECT ID name AT x,y ...` - Add shapes with optional movement
- `MOVE object_id TO x,y DUR seconds EASE linear` - Move objects

## Installation & Setup

### Prerequisites

- Python 3.8+
- FastAPI and dependencies (already installed)

### Environment Variables

Set these secrets in your Replit project:

- `GROQ_API_KEY` - Your Groq API key (for Llama model)
- `OPENAI_API_KEY` - Your OpenAI API key (for GPT-4o model)

Both are optional. If neither is set, the system uses template-based generation.

### Running the Server

The server starts automatically in the development environment. It listens on port 5000.

For manual startup:

```bash
python main.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web UI for video generation |
| `POST` | `/generate` | Generate video from prompt |
| `POST` | `/generate-dsl` | Generate video from DSL code |
| `GET` | `/gallery` | Video gallery page |
| `GET` | `/models` | List available AI models |
| `GET` | `/api/videos` | List all stored videos (JSON) |
| `GET` | `/api/videos/{id}/download` | Download specific video |
| `DELETE` | `/api/videos/{id}` | Delete video from database |
| `GET` | `/health` | Health check |
| `GET` | `/dsl-help` | DSL documentation |

## Resource Limits

To maintain security and performance:

- **Max Resolution**: 1280×720
- **Max Duration**: 6 seconds
- **Max FPS**: 24
- **Max Objects**: 50
- **Render Timeout**: 30 seconds
- **Supported Colors**: Hex format only (#RRGGBB)

## Architecture

The system follows a **security-first pipeline**:

```
Prompt → LLM Translator → DSL Parser → Renderer → Database
   OR
   DSL → DSL Parser → Renderer → Database
```

**Key Design Principles:**

1. **No Python Execution** - LLM outputs DSL, never code
2. **Strict Validation** - All DSL parsed and validated before rendering
3. **Resource Bounded** - Every limit enforced before frame generation
4. **Persistent Storage** - All videos saved in SQLite with metadata

### Core Components

- **main.py** - FastAPI web server and API endpoints
- **video_engine/dsl_parser.py** - DSL tokenizer, parser, and validator
- **video_engine/renderer.py** - PIL-based frame rendering
- **video_engine/llm_translator.py** - Multi-model LLM integration
- **video_engine/database.py** - SQLite database operations
- **video_engine/pipeline.py** - Orchestrates the generation process
- **templates/** - Web UI HTML templates
- **static/** - CSS and JavaScript for the web interface

## Project Status

✅ **Fully Functional**
- Web UI with real-time generation
- Multiple AI model support
- Video gallery with management features
- SQLite database persistence
- Both prompt-based and DSL-based generation

## Examples

### Simple Bouncing Ball

**Prompt:** "A red ball bouncing left to right"

**Generated DSL:**
```
BACKGROUND #1a1a2e
FPS 24
DURATION 3
SHAPE CIRCLE ID ball AT 50,180 RADIUS 30 COLOR #FF4444 MOVE TO 550,180 DUR 3 EASE linear
```

### Text Animation

**Prompt:** "Welcome text appearing in the center"

**Generated DSL:**
```
BACKGROUND #ffffff
FPS 24
DURATION 2
TEXT "Welcome" AT 320,180 SIZE 48 COLOR #000000
```

## Troubleshooting

**No models available?**
- Ensure API keys are set in secrets (GROQ_API_KEY or OPENAI_API_KEY)
- The fallback model always works without keys

**Video not generating?**
- Check that the prompt or DSL is valid
- Verify resource limits aren't exceeded
- Check console logs for error messages

**Gallery not showing videos?**
- Make sure videos were successfully generated
- Check that the SQLite database (videos.db) exists
- Refresh the page

## Security Notes

- ✅ All generated videos are stored in a local SQLite database
- ✅ API keys are stored as encrypted secrets (never exposed)
- ✅ No arbitrary code execution—only DSL interpretation
- ✅ All inputs validated and sanitized
- ✅ Resource limits prevent denial-of-service

## License

This project is maintained as part of the AnveshAI initiative.

## Support

For issues, feature requests, or questions, please check the logs or refer to the architecture documentation at `/architecture`.
