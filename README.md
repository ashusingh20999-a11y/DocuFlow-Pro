# DocuFlow Pro

All-in-one document conversion platform.

## Current tools

- PDF → Word
- PDF → Excel
- Word → PDF
- Excel → PDF
- CSV → Excel
- Excel → CSV
- Merge PDF
- Split PDF
- Images → PDF
- PDF → Images (ZIP)

## Run locally

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`.

LibreOffice is recommended for higher-fidelity Word → PDF conversion.
