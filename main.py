from fastapi import FastAPI, BackgroundTasks, Form, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
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

def process_video_job(job_id, script, style, captions, sfx, motion, voiceGender, voiceEmotion, bgmFilename):
    try:
        rendering_jobs[job_id] = {"status": "completed", "video_url": "https://example.com/rendered.mp4"}
    except Exception as e:
        rendering_jobs[job_id] = {"status": "failed", "error": str(e)}

@app.get("/")
def home():
    return {"message": "Khan Institute Automation Engine is Running!"}

@app.post("/render")
async def start_render(
    background_tasks: BackgroundTasks,
    password: Optional[str] = Form(""),
    script: str = Form(...),
    visualStyle: str = Form("cinematic-doc"),
    captionStyle: str = Form("clean-sub"),
    sfxMode: str = Form("none"),
    cameraMotion: str = Form("static"),
    voiceGender: str = Form("male-standard"),
    voiceEmotion: str = Form("none"),
    bgmFile: Optional[UploadFile] = File(None)
):
    # Pro Feature Verification Logic (Custom BGM is excluded from Pro check)
    is_pro_used = (
        "capcut" in captionStyle or "tiktok" in captionStyle or
        sfxMode != "none" or
        cameraMotion != "static" or
        voiceEmotion != "none"
    )

    if is_pro_used and password != PRO_PASSWORD:
        raise HTTPException(status_code=403, detail="Pro Features Locked! Enter valid Pro Password.")

    bgm_filename = None
    if bgmFile:
        bgm_filename = f"custom_bgm_{random.randint(100,999)}.mp3"

    job_id = str(random.randint(100000, 999999))
    rendering_jobs[job_id] = {"status": "processing"}

    background_tasks.add_task(
        process_video_job, job_id, script, visualStyle, captionStyle, sfxMode, cameraMotion, voiceGender, voiceEmotion, bgm_filename
    )

    return {"status": "started", "job_id": job_id, "message": "Rendering Task Initiated!"}
    
