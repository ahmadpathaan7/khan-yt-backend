from fastapi import FastAPI, BackgroundTasks, Form, HTTPException
from style_engine import get_visual_prompt, process_video_final
import random

app = FastAPI()

# آپ کا پرو پاسورڈ (اسے اپنے پاس محفوظ رکھیں)
PRO_PASSWORD = "your_secret_password_here"

@app.post("/render")
async def start_render(
    background_tasks: BackgroundTasks,
    password: str = Form(...),
    style: str = Form(...),
    sceneSource: str = Form(...),
    script: str = Form(...),
    character: str = Form(""),
    silenceTrim: str = Form("auto")
):
    # 1. Password Verification
    if password != PRO_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid Pro Password")

    job_id = str(random.randint(10000, 99999))
    
    # 2. Parallel Processing Start
    # یہ فنکشن بیک گراؤنڈ میں چلے گا، یوزر کو فوری رسپانس مل جائے گا
    background_tasks.add_task(
        process_video_final, 
        job_id, script, style, sceneSource, character, silenceTrim
    )
    
    return {"status": "started", "job_id": job_id}
  
