import os
from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from telethon import TelegramClient
from telethon.sessions import StringSession
from supabase import create_client
import shutil

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session_string = os.environ["SESSION_STRING"]
supabase_url = os.environ["SUPABASE_URL"]
supabase_key = os.environ["SUPABASE_KEY"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = TelegramClient(StringSession(session_string), api_id, api_hash)
supabase = create_client(supabase_url, supabase_key)

@app.on_event("startup")
async def startup():
    await client.start()

@app.post("/upload")
async def upload_file(file: UploadFile, chat_id: str = Form(...)):
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    size_bytes = os.path.getsize(temp_path)
    target = int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id

    sent_message = await client.send_file(
        target,
        temp_path,
        caption=f"Uploaded: {file.filename}",
        part_size_kb=512,
    )

    supabase.table("files").insert({
        "filename": file.filename,
        "message_id": sent_message.id,
        "chat_id": str(chat_id),
        "size_bytes": size_bytes,
    }).execute()

    os.remove(temp_path)
    return {"status": "sent", "filename": file.filename}
