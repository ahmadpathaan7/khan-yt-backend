import os
import random
import requests
import subprocess
from fastapi import FastAPI, BackgroundTasks, Form, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional
from gTTS import gTTS
from pymongo import MongoClient

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# MongoDB Connection Configuration
# نیچے YOUR_PASSWORD کی جگہ اپنا کلاؤڈ پاس ورڈ درج کریں
MONGO_URI = "mongodb+srv://ahmad770:Ahmad**110@cluster0.qdsw5r2.mongodb.net/?retryWrites=true&w=majority"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["khan_studio_db"]
jobs_collection = db["jobs"]
# -------------------------------------------------------------

MEDIA_DIR = "rendered_output"
os.makedirs(MEDIA_DIR, exist_ok=True)
app.mount("/download", StaticFiles(directory=MEDIA_DIR), name="download")

PRO_PASSWORD = "khan_pro_automation"

def update_job_status(job_id: str, status_data: dict):
    status_data["job_id"] = job_id
    jobs_collection.update_one({"job_id": job_id}, {"$set": status_data}, upsert=True)

def get_job_status(job_id: str):
    return jobs_collection.find_one({"job_id": job_id}, {"_id": 0})

def build_video_task(job_id: str, script: str, video_format: str, voice_setting: str, bgm_path: Optional[str]):
    try:
        update_job_status(job_id, {"status": "processing", "message": "Voiceover readying..."})

        clean_script = script.split("||")[0].strip() if "||" in script else script

        if voice_setting == 'female-ur':
            tts = gTTS(text=clean_script, lang='ur', tld='co.in', slow=False)
        elif voice_setting == 'male-en':
            tts = gTTS(text=clean_script, lang='en', tld='co.uk', slow=False)
        elif voice_setting == 'female-en':
            tts = gTTS(text=clean_script, lang='en', tld='com', slow=False)
        else:
            tts = gTTS(text=clean_script, lang='ur', tld='com.pk', slow=False)

        voice_path = os.path.join(MEDIA_DIR, f"{job_id}_voice.mp3")
        tts.save(voice_path)

        width, height = (1920, 1080) if video_format == "16:9" else (1080, 1920)
        img_path = os.path.join(MEDIA_DIR, f"{job_id}_bg.jpg")
        img_res = requests.get(f"https://picsum.photos/{width}/{height}")
        with open(img_path, "wb") as f:
            f.write(img_res.content)

        output_filename = f"video_{job_id}.mp4"
        output_path = os.path.join(MEDIA_DIR, output_filename)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img_path,
            "-i", voice_path,
            "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac",
            "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest",
            output_path
        ]

        subprocess.run(cmd, check=True)

        if os.path.exists(img_path): os.remove(img_path)
        if os.path.exists(voice_path): os.remove(voice_path)

        update_job_status(job_id, {
            "status": "completed",
            "video_url": f"/download/{output_filename}"
        })

    except Exception as e:
        update_job_status(job_id, {"status": "failed", "error": str(e)})

@app.get("/")
def home():
    return {"status": "active"}

@app.post("/render")
async def start_render(
    background_tasks: BackgroundTasks,
    password: Optional[str] = Form(""),
    script: str = Form(...),
    videoFormat: str = Form("9:16"),
    voiceGender: str = Form("male-ur"),
    imageEngine: str = Form("standard-web"),
    captionStyle: str = Form("clean-sub"),
    sfxMode: str = Form("none"),
    cameraMotion: str = Form("static"),
    voiceEmotion: str = Form("none"),
    bgmFile: Optional[UploadFile] = File(None)
):
    job_id = str(random.randint(100000, 999999))
    update_job_status(job_id, {"status": "processing"})

    background_tasks.add_task(
        build_video_task,
        job_id,
        script,
        videoFormat,
        voiceGender,
        None
    )

    return {"status": "started", "job_id": job_id}

@app.get("/status/{job_id}")
def check_status(job_id: str):
    job = get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID Not Found")
    return job
