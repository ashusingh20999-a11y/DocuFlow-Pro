from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid, shutil, traceback
from converters import convert_file

BASE = Path(__file__).resolve().parent
UPLOADS = BASE / "uploads"
OUTPUTS = BASE / "outputs"
UPLOADS.mkdir(exist_ok=True)
OUTPUTS.mkdir(exist_ok=True)

app = FastAPI(title="DocuFlow Pro")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

@app.get("/health")
def health():
    return {"status": "ok", "service": "DocuFlow Pro"}

@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE / "static/index.html").read_text(encoding="utf-8")

@app.get("/tools", response_class=HTMLResponse)
def tools():
    return (BASE / "static/tools.html").read_text(encoding="utf-8")

@app.post("/convert")
async def convert(files: list[UploadFile] = File(...), target: str = Form(...)):
    if not files:
        raise HTTPException(status_code=400, detail="Please select at least one file.")

    job = uuid.uuid4().hex[:12]
    jobdir = UPLOADS / job
    outdir = OUTPUTS / job
    jobdir.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)

    try:
        saved = []
        for i, uploaded in enumerate(files):
            original = uploaded.filename or "file"
            ext = Path(original).suffix.lower()
            path = jobdir / f"{i}{ext}"
            with path.open("wb") as out:
                shutil.copyfileobj(uploaded.file, out)
            saved.append(path)

        result = convert_file(saved, target, outdir)
        result = Path(result)
        if not result.exists() or result.stat().st_size == 0:
            raise RuntimeError("The conversion engine did not create a valid output file.")

        return FileResponse(
            path=str(result),
            filename=result.name,
            media_type="application/octet-stream",
        )
    except Exception as exc:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": f"Conversion failed: {type(exc).__name__}: {exc}"},
        )
