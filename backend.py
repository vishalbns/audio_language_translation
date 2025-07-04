import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from uuid import uuid4
from datetime import datetime
from urllib.parse import quote_plus
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # load variables from .env file

# ---------- CONFIG ---------- #

openai_api_key = os.getenv("OPENAI_API_KEY")
mongo_uri = os.getenv("MONGO_URI")

client_mongo = MongoClient(mongo_uri)
db = client_mongo["audio_chat_db"]
collection = db["mvp_conversations"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

@app.get("/get-translations/")
def get_translations(limit: int = 10):
    # Fetch last `limit` messages sorted by timestamp descending
    results = collection.find().sort("timestamp", -1).limit(limit)
    items = []
    for r in results:
        items.append({
            "message_id": r.get("message_id"),
            "transcription": r.get("transcription"),
            "translation": r.get("translation"),
            "timestamp": r.get("timestamp").isoformat() if r.get("timestamp") else None,
        })
    return items

@app.post("/send-audio/")
async def send_audio(
    file: UploadFile = File(...),
    conversation_id: str = Form(...),
    sender: str = Form(...),
):
    try:
        audio_bytes = await file.read()

        # Save temp audio file
        temp_audio_path = f"/tmp/{uuid4()}.wav"
        with open(temp_audio_path, "wb") as f:
            f.write(audio_bytes)

        # Transcribe audio
        transcript_resp = client.audio.transcriptions.create(
            model="whisper-1",
            file=open(temp_audio_path, "rb")
        )
        transcription = transcript_resp.text

        # Translate audio
        translation_resp = client.audio.translations.create(
            model="whisper-1",
            file=open(temp_audio_path, "rb")
        )
        translation = translation_resp.text

        # Clean up temp file
        os.remove(temp_audio_path)

        message = {
            "message_id": str(uuid4()),
            "conversation_id": conversation_id,
            "sender": sender,
            "transcription": transcription,
            "translation": translation,
            "timestamp": datetime.utcnow(),
        }

        collection.insert_one(message)

        return {
            "status": "success",
            "transcription": transcription,
            "translation": translation,
            "message_id": message["message_id"],
        }

    except Exception as e:
        return {"status": "error", "detail": str(e)}