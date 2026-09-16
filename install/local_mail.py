"""Loopback-only mail capture service for local development; never sends mail."""
from datetime import date

from fastapi import FastAPI, HTTPException

app = FastAPI(title="LleidaHack local mail capture")
messages = []
templates = {}


@app.get("/v1/health")
def health():
    return {"success": True}


@app.get("/v1/template/name/{name}")
def template(name: str):
    template_id = templates.setdefault(name, len(templates) + 1)
    return {"id": template_id, "name": name, "description": "Local capture template",
            "created_date": date.today().isoformat(), "internal": True, "fields": [], "common_fields": []}


@app.post("/v1/mail/")
def create_mail(payload: dict):
    message = {"sender_id": 0, "receiver_id": "", "receiver_mail": "", **payload,
               "id": len(messages) + 1, "sent": False}
    messages.append(message)
    return message


@app.put("/v1/mail/send/{mail_id}")
def capture_mail(mail_id: int):
    if not 1 <= mail_id <= len(messages):
        raise HTTPException(status_code=404, detail="Mail not found")
    messages[mail_id - 1]["sent"] = True
    return {"success": True, "captured": True}


@app.get("/messages")
def get_messages():
    return messages
