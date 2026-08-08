from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import shutil

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
async def process_image(file: UploadFile = File(...), template_name: str = "default.json"):
    # Save the uploaded file
    file_path = os.path.join(UPLOADS_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # TODO: Pass the image to the omr_engine wrapper
    # result = process_omr(file_path, template_name)
    
    return JSONResponse(content={"status": "success", "filename": file.filename, "message": "File uploaded (OMR processing pending implementation)"})

@app.post("/api/templates/save")
async def save_template(request: Request):
    data = await request.json()
    template_name = data.get("name", "custom_template.json")
    if not template_name.endswith(".json"):
        template_name += ".json"
    
    template_path = os.path.join(TEMPLATES_DIR, template_name)
    import json
    with open(template_path, "w") as f:
        json.dump(data.get("template_data", {}), f, indent=4)
        
    return JSONResponse(content={"status": "success", "message": f"Template {template_name} saved successfully."})

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
