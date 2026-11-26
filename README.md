# AutoReel AI MVP

Runnable Instagram-only Reel generation MVP. It implements brand profiles, mock AI content generation, scene-based FFmpeg video rendering, approval, scheduling records, and a production-safe Instagram publisher adapter that remains disabled until valid Meta credentials are supplied.

## What works
- FastAPI API and responsive web UI
- SQLite by default; PostgreSQL supported via `DATABASE_URL`
- User registration/login with JWT in an HTTP-only cookie
- Brand profile setup
- Generates a 30-second Reel plan using a deterministic Mock AI provider
- Creates seven vertical scene cards and renders a real 1080x1920 MP4 with FFmpeg
- Preview, edit metadata, approve, schedule, download
- State-machine validation
- Idempotent publication records
- Instagram Graph API adapter with dry-run safety
- Docker and Docker Compose
- Basic tests

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Open http://localhost:8000

Local without Docker requires Python 3.11+ and FFmpeg:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Production Instagram setup
Set `INSTAGRAM_PUBLISH_ENABLED=true`, `META_API_VERSION`, `META_APP_ID`, and `META_APP_SECRET`. Users must connect an eligible Instagram professional account via official Meta OAuth. This repository does not collect Instagram passwords and does not use browser automation.

The included OAuth callback is a safe foundation, but Meta app review, redirect URI registration, token exchange validation, permissions, and current endpoint requirements must be completed against Meta's official documentation before production use.

## Test
```bash
pytest -q
```

## AI provider
The defaults to a deterministic Mock provider so the MVP runs without paid AI credentials. To generate content with Google Gemini, set in `.env`:

```
AI_PROVIDER=gemini
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-2.0-flash
```

Get a key at https://aistudio.google.com/apikey. With no key or `AI_PROVIDER=mock`, the safe mock provider is used. All provider responses are validated and normalized (scene durations rescaled to the reel length, quality score clamped to 0-100) before rendering. To add other providers (OpenAI, Azure OpenAI, Anthropic), implement `ContentProvider` in `app/providers.py` and register it in `get_provider()` in `app/main.py`.

## Important
The renderer creates motion-card scenes rather than using copyrighted media.

## Test
```bash
pytest -q
```

## Production Instagram setup

