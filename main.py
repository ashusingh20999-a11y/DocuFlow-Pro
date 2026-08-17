from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid, shutil, traceback
import fitz
from converters import convert_file

BASE=Path(__file__).resolve().parent
UPLOADS=BASE/'uploads'; OUTPUTS=BASE/'outputs'
UPLOADS.mkdir(exist_ok=True); OUTPUTS.mkdir(exist_ok=True)
app=FastAPI(title='DocuFlow Pro')
app.mount('/static', StaticFiles(directory=BASE/'static'), name='static')

@app.get('/health')
def health(): return {'status':'ok','service':'DocuFlow Pro'}
@app.get('/',response_class=HTMLResponse)
def home(): return (BASE/'static/index.html').read_text(encoding='utf-8')
@app.get('/tools',response_class=HTMLResponse)
def tools(): return (BASE/'static/tools.html').read_text(encoding='utf-8')

@app.post('/convert')
async def convert(files:list[UploadFile]=File(...),target:str=Form(...)):
    if not files: raise HTTPException(400,'Please select at least one file.')
    job=uuid.uuid4().hex[:12]; jobdir=UPLOADS/job; outdir=OUTPUTS/job
    jobdir.mkdir(parents=True,exist_ok=True); outdir.mkdir(parents=True,exist_ok=True)
    try:
        saved=[]
        for i,u in enumerate(files):
            p=jobdir/f"{i}{Path(u.filename or 'file').suffix.lower()}"
            with p.open('wb') as out: shutil.copyfileobj(u.file,out)
            saved.append(p)
        result=Path(convert_file(saved,target,outdir))
        if not result.exists() or result.stat().st_size==0: raise RuntimeError('Empty output file')
        return FileResponse(path=str(result),filename=result.name,media_type='application/octet-stream')
    except Exception as exc:
        traceback.print_exc(); return JSONResponse(500,{'detail':f'Conversion failed: {type(exc).__name__}: {exc}'})

@app.post('/edit-pdf')
async def edit_pdf(file:UploadFile=File(...),find_text:str=Form(''),replace_text:str=Form(''),page:int=Form(0),add_text:str=Form(''),x:float=Form(50),y:float=Form(80),font_size:float=Form(12)):
    if not file.filename or Path(file.filename).suffix.lower()!='.pdf': raise HTTPException(400,'Please select a PDF file.')
    if not find_text and not add_text: raise HTTPException(400,'Enter text to replace or text to add.')
    job=uuid.uuid4().hex[:12]; jobdir=UPLOADS/job; outdir=OUTPUTS/job
    jobdir.mkdir(parents=True,exist_ok=True); outdir.mkdir(parents=True,exist_ok=True)
    src=jobdir/'source.pdf'; out=outdir/'edited.pdf'
    with src.open('wb') as f: shutil.copyfileobj(file.file,f)
    try:
        doc=fitz.open(str(src))
        try:
            if find_text:
                pages=range(len(doc)) if page==0 else [page-1]; matches=0
                for pno in pages:
                    p=doc[pno]; rects=p.search_for(find_text)
                    if not rects: continue
                    matches+=len(rects)
                    for rect in rects: p.add_redact_annot(rect,fill=(1,1,1))
                    p.apply_redactions()
                    if replace_text:
                        for rect in rects: p.insert_text((rect.x0,rect.y1-2),replace_text,fontsize=font_size,color=(0,0,0))
                if matches==0: raise ValueError(f'Text not found: {find_text}')
            if add_text:
                pno=max(1,page)-1
                if pno>=len(doc): raise ValueError('Page number is outside the PDF')
                doc[pno].insert_text((x,y),add_text,fontsize=font_size,color=(0,0,0))
            doc.save(str(out),garbage=4,deflate=True)
        finally: doc.close()
        return FileResponse(path=str(out),filename='edited.pdf',media_type='application/pdf')
    except Exception as exc:
        traceback.print_exc(); return JSONResponse(500,{'detail':f'PDF edit failed: {type(exc).__name__}: {exc}'})
