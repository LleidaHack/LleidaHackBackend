from fastapi import UploadFile, File
import uuid
import aiofiles
import os

async def uploadFile(in_file:UploadFile=File(...)):
    rand=uuid.uuid4()
    async with aiofiles.open(f"static/{rand}.jpg", "wb") as f:
        await f.write(in_file.file.read())
    return rand

async def getFile(uuid:str):
    file_path = f"static/{uuid}.jpg"
    if not os.path.isfile(file_path):
        return {"error": "Image not found."}
    return FileResponse(file_path, headers={"Content-Type": "image/jpeg"})
