import os
import json
import random
import requests
from fastapi import FastAPI, BackgroundTasks, Form, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional
from gTTS import gTTS
from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MEDIA_DIR = "rendered_output"
JOBS_FILE = os.path.join(MEDIA_DIR, "jobs.json")
os.makedirs(MEDIA_DIR, exist_ok=True)
app.mount("/download", StaticFiles(directory=MEDIA_DIR), name="download")

PRO_PASSWORD = "khan_pro_automation"

def load_jobs():
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def update_job_status(job_id: str, status_data: dict):
    jobs = load_jobs()
    jobs[job_id] = status_data
    try:
        with open(JOBS_FILE, "w") as f:
            json.dump(jobs, f, indent=4)
    except Exception:
        pass

def build_video_task(job_id: str, script: str, video_format: str, bgm_path: Optional[str]):
    try:
        # Update status to active processing
        update_job_status(job_id, {"status": "processing", "progress": "Generating Voiceover..."})

        # 1. Voiceover
        tts = gTTS(text=script, lang='ur', slow=False)
        voice_path = os.path.join(MEDIA_DIR, f"{job_id}_voice.mp3")
        tts.save(voice_path)

        voice_clip = AudioFileClip(voice_path)
        video_duration = voice_clip.duration

        # 2. Dimensions
        width, height = (1920, 1080) if video_format == "16:9" else (1080, 1920)

        # 3. Image Download Fix
        img_path = os.path.join(MEDIA_DIR, f"{job_id}_bg.jpg")
        img_res = requests.get(f"https://picsum.photos/{width}/{height}")
        with open(img_path, "wb") as f:
            f.write(img_res.content)

        img_clip = ImageClip(img_path).set_duration(video_duration)

        # 4. Audio
        audio_clips = [voice_clip]
        if bgm_path and os.path.exists(bgm_path):
            bgm_clip = AudioFileClip(bgm_path).volumex(0.15).set_duration(video_duration)
            audio_clips.append(bgm_clip)

        final_audio = CompositeAudioClip(audio_clips)
        video_clip = img_clip.set_audio(final_audio)

        # 5. Export
        output_filename = f"video_{job_id}.mp4"
        output_path = os.path.join(MEDIA_DIR, output_filename)
        
        video_clip.write_videofile(
            output_path, 
            fps=24, 
            codec='libx264', 
            audio_codec='aac',
            threads=2
        )

        video_clip.close()
        voice_clip.close()

        # Clean temp image
        if os.path.exists(img_path):
            os.remove(img_path)

        update_job_status(job_id, {
            "status": "completed", 
            "video_url": f"/download/{output_filename}"
        })

    except Exception as e:
        update_job_status(job_id, {"status": "failed", "error": str(e)})

@app.get("/")
def home():
    return {"message": "Khan Automation Studio Engine Active"}

@app.post("/render")
async def start_render(
    background_tasks: BackgroundTasks,
    password: Optional[str] = Form(""),
    script: str = Form(...),
    videoFormat: str = Form("9:16"),
    captionStyle: str = Form("clean-sub"),
    sfxMode: str = Form("none"),
    cameraMotion: str = Form("static"),
    voiceEmotion: str = Form("none"),
    imageEngine: str = Form("standard-web"),
    bgmFile: Optional[UploadFile] = File(None)
):
    is_pro_used = (
        "capcut" in captionStyle or 
        sfxMode != "none" or 
        cameraMotion != "static" or 
        voiceEmotion != "none" or 
        imageEngine in ["flux-ai", "hybrid-flux"]
    )

    if is_pro_used and password != PRO_PASSWORD:
        raise HTTPException(status_code=403, detail="Pro Features Locked!")

    bgm_path = None
    if bgmFile:
        bgm_path = os.path.join(MEDIA_DIR, f"bgm_{bgmFile.filename}")
        with open(bgm_path, "wb") as f:
            f.write(await bgmFile.read())

    job_id = str(random.randint(100000, 999999))
    update_job_status(job_id, {"status": "processing"})

    background_tasks.add_task(build_video_task, job_id, script, videoFormat, bgm_path)

    return {"status": "started", "job_id": job_id}

@app.get("/status/{job_id}")
def check_status(job_id: str):
    jobs = load_jobs()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job ID Not Found")
    return jobs[job_id]
    
