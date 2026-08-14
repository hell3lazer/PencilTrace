from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
import shutil

# Add the project root to sys.path so 'backend' module is found
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

app = FastAPI(title="PencilTrace Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Mount frontend
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open(os.path.join(FRONTEND_DIR, "index.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/process")
async def process_image(file: UploadFile = File(...), template_name: str = Form("default.json")):
    # Save the uploaded file
    file_path = os.path.join(UPLOADS_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    template_path = os.path.join(TEMPLATES_DIR, template_name)
    
    # Standardize image formats (handles iPhone HEIC secretly named .png)
    omr_input_path = file_path
    try:
        from PIL import Image
        import pillow_heif
        pillow_heif.register_heif_opener()
        
        img = Image.open(file_path)
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            img = background
        else:
            img = img.convert("RGB")
        standardized_path = os.path.join(UPLOADS_DIR, "std_" + file.filename + ".jpg")
        img.save(standardized_path, "JPEG")
        omr_input_path = standardized_path
    except Exception:
        pass # If it's a PDF or already standard, just pass the original path
    
    from backend.omr_engine_wrapper import process_omr_batch
    from backend.grading import grade_results
    
    try:
        raw_data = process_omr_batch([omr_input_path], template_path, output_dir=UPLOADS_DIR)
        graded = grade_results(raw_data)
        
        if graded:
            result = graded[0]
            return JSONResponse(content={"status": "success", "filename": file.filename, "score": result["score"], "responses": result["responses"]})
        else:
            return JSONResponse(content={"status": "error", "filename": file.filename, "message": "No results generated. Ensure template matches image."})
    except Exception as e:
        return JSONResponse(content={"status": "error", "filename": file.filename, "message": str(e)})

@app.get("/api/templates")
async def list_templates():
    templates = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".json")]
    return JSONResponse(content={"templates": templates})

@app.post("/api/templates/import")
async def import_template(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        return JSONResponse(content={"status": "error", "message": "Only JSON templates are allowed."})
    
    file_path = os.path.join(TEMPLATES_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return JSONResponse(content={"status": "success", "message": f"Template {file.filename} imported successfully.", "filename": file.filename})

from fastapi.responses import FileResponse

@app.get("/api/templates/export/{template_name}")
async def export_template(template_name: str):
    file_path = os.path.join(TEMPLATES_DIR, template_name)
    if not os.path.exists(file_path):
        return JSONResponse(content={"status": "error", "message": "Template not found."}, status_code=404)
    
    return FileResponse(path=file_path, filename=template_name, media_type="application/json")

import webbrowser
import threading

def open_browser():
    # Wait a second for server to start, then open browser
    import time
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)
