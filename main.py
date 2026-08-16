import os
import json
import random
import requests
from fastapi import FastAPI, BackgroundTasks, Form, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional
from gTTS import gTTS
from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip, TextClip, CompositeVideoClip

app = FastAPI()

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Output directory for rendered videos and static files
MEDIA_DIR = "rendered_output"
JOBS_FILE = os.path.join(MEDIA_DIR, "jobs.json")
os.makedirs(MEDIA_DIR, exist_ok=True)
app.mount("/download", StaticFiles(directory=MEDIA_DIR), name="download")

PRO_PASSWORD = "khan_pro_automation"

# Persistent JSON Job Tracker Helper Functions
def load_jobs():
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_jobs(jobs):
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=4)

def update_job_status(job_id: str, status_data: dict):
    jobs = load_jobs()
    jobs[job_id] = status_data
    save_jobs(jobs)

# Background Video Processing Task
def build_video_task(
    job_id: str, 
    script: str, 
    video_format: str, 
    image_engine: str, 
    voice_gender: str, 
    voice_emotion: str, 
    caption_style: str, 
    bgm_path: Optional[str]
):
    try:
        # 1. Voiceover Generation using gTTS
        tld_accent = 'com.pk' if voice_gender == 'male-standard' else 'co.in'
        tts = gTTS(text=script, lang='ur', tld=tld_accent, slow=False)
        voice_path = os.path.join(MEDIA_DIR, f"{job_id}_voice.mp3")
        tts.save(voice_path)

        # Load Audio Clip
        voice_clip = AudioFileClip(voice_path)
        video_duration = voice_clip.duration

        # 2. Aspect Ratio Resolution
        if video_format == "16:9":
            width, height = 1920, 1080  # Long Video
        else:
            width, height = 1080, 1920  # Short / Reel (9:16)

        # 3. Visual Layer Setup
        img_url = f"https://picsum.photos/{width}/{height}"
        img_clip = ImageClip(img_url).set_duration(video_duration)

        # 4. Audio Mixing
        audio_clips = [voice_clip]
        if bgm_path and os.path.exists(bgm_path):
            bgm_clip = AudioFileClip(bgm_path).volumex(0.15).set_duration(video_duration)
            audio_clips.append(bgm_clip)

        final_audio = CompositeAudioClip(audio_clips)

        # 5. Video Assembly
        video_clip = img_clip.set_audio(final_audio)

        # 6. Export Final MP4
        output_filename = f"video_{job_id}.mp4"
        output_path = os.path.join(MEDIA_DIR, output_filename)
        
        video_clip.write_videofile(
            output_path, 
            fps=24, 
            codec='libx264', 
            audio_codec='aac',
            threads=2
        )

        # Free resources
        video_clip.close()
        voice_clip.close()

        # Update persistent job status
        update_job_status(job_id, {
            "status": "completed", 
            "video_url": f"/download/{output_filename}"
        })

    except Exception as e:
        update_job_status(job_id, {
            "status": "failed", 
            "error": str(e)
        })

@app.get("/")
def home():
    return {"message": "Khan Automation Studio Engine is Running!"}

@app.post("/render")
async def start_render(
    background_tasks: BackgroundTasks,
    password: Optional[str] = Form(""),
    script: str = Form(...),
    videoFormat: str = Form("9:16"),
    visualStyle: str = Form("cinematic-doc"),
    imageEngine: str = Form("standard-web"),
    voiceGender: str = Form("male-standard"),
    voiceEmotion: str = Form("none"),
    captionStyle: str = Form("clean-sub"),
    sfxMode: str = Form("none"),
    cameraMotion: str = Form("static"),
    bgmFile: Optional[UploadFile] = File(None)
):
    # Pro Features Verification
    is_pro_used = (
        "capcut" in captionStyle or "tiktok" in captionStyle or
        sfxMode != "none" or
        cameraMotion != "static" or
        voiceEmotion != "none" or
        imageEngine in ["flux-ai", "hybrid-flux"]
    )

    if is_pro_used and password != PRO_PASSWORD:
        raise HTTPException(status_code=403, detail="Pro Features Locked! Enter valid Pro Password.")

    bgm_path = None
    if bgmFile:
        bgm_path = os.path.join(MEDIA_DIR, f"bgm_{bgmFile.filename}")
        with open(bgm_path, "wb") as f:
            f.write(await bgmFile.read())

    job_id = str(random.randint(100000, 999999))
    
    # Persistent status store start
    update_job_status(job_id, {"status": "processing"})

    background_tasks.add_task(
        build_video_task, 
        job_id, 
        script, 
        videoFormat, 
        imageEngine, 
        voiceGender, 
        voiceEmotion, 
        captionStyle, 
        bgm_path
    )

    return {"status": "started", "job_id": job_id, "message": "Rendering Task Initiated!"}

@app.get("/status/{job_id}")
def check_status(job_id: str):
    jobs = load_jobs()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job ID Not Found")
    return jobs[job_id]
