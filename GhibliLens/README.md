# 🌿 GhibliLens

> **Transform any short video into a Studio Ghibli anime masterpiece using AI.**

GhibliLens is a full-stack web application that takes a user-uploaded video (up to 15 seconds), stylizes every frame using Stable Diffusion + a Ghibli LoRA via the Replicate API, applies ControlNet for structural consistency and optical-flow temporal blending to eliminate flickering, then reassembles the stylized frames back into an MP4 with the original audio.

---

## ✨ Features

- 🎬 **Drag-and-drop upload** — MP4, MOV, WEBM up to 100 MB
- ✂️ **Integrated trimmer** — pick any 15-second window from longer videos
- 🎨 **Ghibli AI Engine** — SDXL + Ghibli LoRA via Replicate, ControlNet SoftEdge conditioning
- 🎞️ **Zero flicker** — Farneback Optical Flow temporal consistency pass
- 🔊 **Audio preserved** — original audio is stripped and re-muxed into the output
- 📊 **Live progress** — polling progress bar with cheeky Ghibli-themed status messages
- ↔️ **Side-by-side comparison** — Original vs Ghibli player with split / solo views
- ☁️ **Cloud Run ready** — multi-stage Dockerfile + GitHub Actions CI/CD included

---

## 🗂 Project Structure

```
GhibliLens/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── main.py           # App entry + static file serving
│   │   ├── config.py         # Pydantic settings (env vars)
│   │   ├── routers/
│   │   │   ├── video.py      # POST /api/v1/video/upload
│   │   │   └── jobs.py       # GET/DELETE /api/v1/jobs/{id}/...
│   │   ├── services/
│   │   │   ├── ffmpeg_service.py       # Frame extract, trim, mux
│   │   │   ├── replicate_service.py    # Replicate API calls
│   │   │   ├── controlnet_service.py   # SoftEdge depth maps
│   │   │   ├── consistency_service.py  # Optical flow blending
│   │   │   └── job_manager.py          # In-memory job state
│   │   ├── models/schemas.py   # Pydantic request/response models
│   │   └── utils/              # Validators, file helpers
│   ├── test_pipeline.py      # Step-by-step pipeline test script
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                 # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/       # UploadZone, Trimmer, Progress, Compare, Download
│   │   ├── hooks/            # useUpload (polling), useVideoMeta (duration)
│   │   ├── api/client.js     # Axios API client
│   │   └── styles/index.css  # Full Ghibli design system
│   └── index.html
├── .github/workflows/
│   └── deploy-cloud-run.yml  # CI/CD: build → push → deploy
├── docker-compose.yml
└── .gitignore
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| uv | latest (`irm https://astral.sh/uv/install.ps1 \| iex`) |
| ffmpeg | any recent (`winget install Gyan.FFmpeg`) |

### 1. Clone & Configure

```bash
git clone https://github.com/YOUR_USERNAME/GhibliLens.git
cd GhibliLens
```

Create your backend `.env`:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env and set your REPLICATE_API_TOKEN
```

Get your token at → **https://replicate.com/account/api-tokens**

### 2. Start the Backend

```powershell
cd backend
uv sync --no-install-project
.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload
```

API available at `http://localhost:8000`  
Swagger docs at `http://localhost:8000/docs`

### 3. Start the Frontend

```powershell
cd frontend
npm install
npm run dev
```

App available at `http://localhost:5173`

### 4. Validate the AI Pipeline

```powershell
cd backend
.venv\Scripts\python.exe test_pipeline.py --image test_frame.png
```

This tests ControlNet, Replicate API, and temporal consistency independently.

---

## 🐳 Docker (Production)

### Build & Run locally

```bash
docker build -f backend/Dockerfile -t ghibilens .
docker run -p 8080:8080 -e REPLICATE_API_TOKEN=your_token ghibilens
```

App served at `http://localhost:8080` (React + API on same port)

### docker-compose (full stack)

```bash
REPLICATE_API_TOKEN=your_token docker-compose up --build
```

---

## ☁️ Deploy to Google Cloud Run

### Prerequisites

1. A Google Cloud project with billing enabled
2. Cloud Run API enabled
3. A service account with roles: `Cloud Run Admin`, `Storage Admin`

### One-time GitHub Secrets Setup

Go to your repo → **Settings → Secrets → Actions** and add:

| Secret | Value |
|---|---|
| `GCP_PROJECT_ID` | Your GCP project ID |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Workload Identity pool provider |
| `GCP_SERVICE_ACCOUNT` | `deploy-sa@your-project.iam.gserviceaccount.com` |
| `REPLICATE_API_TOKEN` | Your Replicate API token |

### Deploy

Push to `main` branch — GitHub Actions automatically:
1. Builds the multi-stage Docker image (Node + Python + ffmpeg)
2. Pushes to Google Container Registry
3. Deploys to Cloud Run with 2 vCPU / 2 GB RAM / 300s timeout

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/video/upload` | Upload video, start Ghibli stylization |
| `GET` | `/api/v1/jobs/{id}/status` | Poll job progress |
| `GET` | `/api/v1/jobs/{id}/download` | Download final MP4 |
| `GET` | `/api/v1/jobs/{id}/preview` | Get preview still frame |
| `DELETE` | `/api/v1/jobs/{id}` | Cancel job & clean up |
| `GET` | `/health` | Health check |

Full interactive docs: `http://localhost:8000/docs`

---

## 🎨 The AI Pipeline

```
Upload MP4
    │
    ▼
[1] Validate (≤15s, format, size)
    │
    ▼
[2] FFmpeg: Trim → Extract frames @ 12fps → Strip audio
    │
    ▼
[3] ControlNet: SoftEdge map per frame (OpenCV Canny)
    │
    ▼
[4] Replicate SDXL + Ghibli LoRA per frame (batched)
    │  Prompt: "Studio Ghibli style, lush watercolor textures,
    │           hand-painted backgrounds, soft lighting..."
    │
    ▼
[5] Temporal Consistency: Farneback Optical Flow blend (α=0.3)
    │
    ▼
[6] FFmpeg: Reassemble frames → MP4 → Mux original audio
    │
    ▼
Output: Stylized Ghibli MP4
```

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `REPLICATE_API_TOKEN` | *(required)* | Replicate API key |
| `REPLICATE_MODEL` | `stability-ai/sdxl:...` | Model version to use |
| `CONTROLNET_CONDITIONING_SCALE` | `0.75` | ControlNet strength (0–1) |
| `DEFAULT_FPS` | `12` | Frame extraction rate |
| `MAX_VIDEO_DURATION` | `15` | Max clip length in seconds |
| `TEMP_DIR` | `temp_jobs` | Temp directory for job files |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed frontend origins |

---

## 📄 License

MIT — do whatever you want, just don't use it to make anything non-Ghibli. 🌿
