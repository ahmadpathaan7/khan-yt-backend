import io
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from gtts import gTTS

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Voice presets — tld changes the accent slightly, which is the only real "voice" knob
# gTTS exposes. Kept simple on purpose: this server does ONE thing (text -> mp3 bytes)
# and nothing else, so there is nothing here that can go stale, run out of storage, or
# lose track of a job. Every request is fully self-contained.
VOICE_MAP = {
    'male-ur':   dict(lang='ur', tld='com.pk'),
    'female-ur': dict(lang='ur', tld='co.in'),
    'male-en':   dict(lang='en', tld='co.uk'),
    'female-en': dict(lang='en', tld='com'),
}


@app.get("/")
def home():
    return {"status": "active"}


@app.get("/tts")
def tts(text: str = Query(..., min_length=1), voice: str = "male-ur", slow: bool = False):
    conf = VOICE_MAP.get(voice, dict(lang='ur', tld='com'))
    buf = io.BytesIO()
    gTTS(text=text, lang=conf['lang'], tld=conf['tld'], slow=slow).write_to_fp(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-store"}
    )
