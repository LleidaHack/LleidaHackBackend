from fastapi import UploadFile, File
import uuid
import aiofiles

async def uploadFile(in_file:UploadFile=File(...)):
    rand=uuid.uuid4()
    async with aiofiles.open(f"static/{rand}.jpg", "wb") as f:
        await f.write(in_file.file.read())
    return rand