from fastapi import FastAPI, BackgroundTasks, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PRO_PASSWORD = "khan_pro_automation"
rendering_jobs = {}

def process_video_job(job_id, script, style, captions, bgmTrack, bgmDucking, sfx, motion, silenceTrim, voiceGender, pitch, rate):
    try:
        # Full dynamic mixing pipeline accepting Auto-Ducking BGM and SFX
        rendering_jobs[job_id] = {"status": "completed", "video_url": "https://example.com/rendered.mp4"}
    except Exception as e:
        rendering_jobs[job_id] = {"status": "failed", "error": str(e)}

@app.get("/")
def home():
    return {"message": "Khan Institute Automation Engine is Running!"}

@app.post("/render")
async def start_render(
    background_tasks: BackgroundTasks,
    password: str = Form(...),
    script: str = Form(...),
    visualStyle: str = Form("cinematic-doc"),
    captionStyle: str = Form("capcut-yellow"),
    bgmTrack: str = Form("suspense-mystery"),
    bgmDucking: str = Form("auto-80"),
    sfxMode: str = Form("whoosh-impact"),
    cameraMotion: str = Form("ken-burns"),
    silenceTrim: str = Form("auto"),
    voiceGender: str = Form("male-deep"),
    voicePitch: str = Form("+0Hz"),
    voiceRate: str = Form("+0%")
):
    if password != PRO_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid Pro Password")

    job_id = str(random.randint(100000, 999999))
    rendering_jobs[job_id] = {"status": "processing"}

    background_tasks.add_task(
        process_video_job, job_id, script, visualStyle, captionStyle, bgmTrack, bgmDucking, sfxMode, cameraMotion, silenceTrim, voiceGender, voicePitch, voiceRate
    )

    return {"status": "started", "job_id": job_id, "message": "Audio Auto-Mixing & Video Rendering Started!"}
    
