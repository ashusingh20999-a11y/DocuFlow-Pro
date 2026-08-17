from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid, shutil
from converters import convert_file

BASE=Path(__file__).parent
UPLOADS=BASE/"uploads"; OUTPUTS=BASE/"outputs"
UPLOADS.mkdir(exist_ok=True); OUTPUTS.mkdir(exist_ok=True)

app=FastAPI(title="DocuFlow Pro")
app.mount("/static", StaticFiles(directory=BASE/"static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE/"static/index.html").read_text(encoding="utf-8")

@app.get("/tools", response_class=HTMLResponse)
def tools():
    return (BASE/"static/tools.html").read_text(encoding="utf-8")

@app.post("/convert")
async def convert(files: list[UploadFile]=File(...), target:str=Form(...)):
    job=uuid.uuid4().hex[:12]
    jobdir=UPLOADS/job
    jobdir.mkdir()
    saved=[]
    try:
        for i,f in enumerate(files):
            ext=Path(f.filename or "").suffix.lower()
            p=jobdir/f"{i}{ext}"
            with p.open("wb") as out: shutil.copyfileobj(f.file,out)
            saved.append(p)
        result=convert_file(saved,target,OUTPUTS/job)
        return FileResponse(result,path=result,filename=result.name,media_type="application/octet-stream")
    except Exception as e:
        raise HTTPException(500,str(e))
